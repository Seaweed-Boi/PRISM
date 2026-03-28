from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from uuid import uuid4

import redis
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import Settings


@dataclass
class SecurityDecision:
    allowed: bool
    status_code: int
    reason: str


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._store: dict[str, list[datetime]] = defaultdict(list)
        self._lock = Lock()

    def allow(self, key: str, window_seconds: int, max_requests: int) -> bool:
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=window_seconds)
        with self._lock:
            self._store[key] = [ts for ts in self._store[key] if ts >= window_start]
            if len(self._store[key]) >= max_requests:
                return False
            self._store[key].append(now)
            return True


class RedisRateLimiter:
    def __init__(self, redis_url: str) -> None:
        self._client = redis.Redis.from_url(redis_url, decode_responses=True)
        self._client.ping()

    def allow(self, key: str, window_seconds: int, max_requests: int) -> bool:
        pipeline = self._client.pipeline()
        pipeline.incr(key)
        pipeline.expire(key, window_seconds)
        count, _ = pipeline.execute()
        return int(count) <= max_requests


class CloudflareSecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.settings = settings
        self.exempt_paths = {"/", "/docs", "/openapi.json", "/redoc"}
        self._limiter = self._build_limiter()
        self._blocked_countries = {
            code.strip().upper()
            for code in settings.cloudflare_block_countries.split(",")
            if code.strip()
        }

    def _build_limiter(self):
        try:
            return RedisRateLimiter(self.settings.redis_url)
        except Exception:
            return InMemoryRateLimiter()

    def _client_ip(self, request: Request) -> str:
        cf_ip = request.headers.get("cf-connecting-ip")
        if cf_ip:
            return cf_ip
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
        if request.client and request.client.host:
            return request.client.host
        return "unknown"

    def _is_local_dev(self, request: Request, client_ip: str) -> bool:
        if not self.settings.cloudflare_allow_local_dev:
            return False
        host = request.headers.get("host", "")
        local_hosts = {"localhost", "127.0.0.1"}
        return client_ip in local_hosts or any(h in host for h in local_hosts)

    def _evaluate(self, request: Request) -> SecurityDecision:
        if not self.settings.cloudflare_security_enabled:
            return SecurityDecision(True, 200, "disabled")

        if request.url.path in self.exempt_paths:
            return SecurityDecision(True, 200, "exempt")

        client_ip = self._client_ip(request)
        if self._is_local_dev(request, client_ip):
            return SecurityDecision(True, 200, "local-dev")

        if self.settings.cloudflare_require_ray and not request.headers.get("cf-ray"):
            return SecurityDecision(False, 403, "missing-cf-ray")

        country = request.headers.get("cf-ipcountry", "").upper()
        if country and country in self._blocked_countries:
            return SecurityDecision(False, 403, "country-blocked")

        bot_score_raw = request.headers.get("cf-bot-score")
        if bot_score_raw:
            try:
                bot_score = int(bot_score_raw)
            except ValueError:
                return SecurityDecision(False, 403, "invalid-bot-score")
            if bot_score < self.settings.cloudflare_min_bot_score:
                return SecurityDecision(False, 403, "low-bot-score")

        rate_key = f"prism:ratelimit:{client_ip}:{request.url.path}"
        allowed = self._limiter.allow(
            rate_key,
            self.settings.cloudflare_rate_limit_window_seconds,
            self.settings.cloudflare_rate_limit_max_requests,
        )
        if not allowed:
            return SecurityDecision(False, 429, "rate-limit")

        return SecurityDecision(True, 200, "ok")

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid4())
        decision = self._evaluate(request)
        if not decision.allowed:
            return JSONResponse(
                status_code=decision.status_code,
                content={
                    "detail": "Request blocked by Cloudflare security layer",
                    "reason": decision.reason,
                    "request_id": request_id,
                },
                headers={"x-prism-request-id": request_id},
            )

        response = await call_next(request)
        response.headers["x-prism-request-id"] = request_id
        cf_ray = request.headers.get("cf-ray")
        if cf_ray:
            response.headers["x-cf-ray"] = cf_ray
        return response
