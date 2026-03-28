from __future__ import annotations

from hashlib import sha1
import redis

from app.core.config import get_settings

settings = get_settings()


class FraudService:
    def __init__(self) -> None:
        self._redis = None
        try:
            self._redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)
            self._redis.ping()
        except Exception:
            self._redis = None

    def location_score(self, lat: float, lon: float, zone: str) -> float:
        # Simple placeholder validation until geo-fencing is integrated.
        if abs(lat) > 90 or abs(lon) > 180:
            return 1.0
        return 0.1 if zone else 0.4

    def activity_score(self, activity: float) -> float:
        if activity < 0.2:
            return 0.9
        if activity < 0.5:
            return 0.45
        return 0.1

    def duplicate_score(self, worker_id: int, policy_id: int, expected_income: float, actual_income: float) -> float:
        claim_sig = f"{worker_id}:{policy_id}:{expected_income:.2f}:{actual_income:.2f}"
        key = f"prism:claim:{sha1(claim_sig.encode()).hexdigest()}"
        if not self._redis:
            return 0.0
        if self._redis.exists(key):
            return 1.0
        self._redis.setex(key, 3600, "1")
        return 0.0

    def fraud_score(
        self,
        worker_id: int,
        policy_id: int,
        expected_income: float,
        actual_income: float,
        lat: float,
        lon: float,
        zone: str,
        activity: float,
    ) -> float:
        loc = self.location_score(lat, lon, zone)
        act = self.activity_score(activity)
        dup = self.duplicate_score(worker_id, policy_id, expected_income, actual_income)
        return round(min(loc * 0.4 + act * 0.35 + dup * 0.25, 1.0), 2)
