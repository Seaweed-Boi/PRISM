# PRISM System Architecture

## Flow (aligned with reference image)

User App  
-> Cloudflare (Security Layer)  
-> Fraud Detection Engine  
-> Fraud Score  
-> Decision Engine

## Implemented Runtime Flow

Cloudflare Security Middleware (request gate)
-> External APIs (Weather, Traffic, Pollution)
-> Disruption Monitoring Service
-> AI Earnings Prediction + Risk Scoring
-> Policy Engine
-> Fraud Engine (GPS check, activity validation, duplicate check via Redis)
-> Decision Engine (approve/reject claims)
-> Payout Engine (simulated UPI reference)
-> Worker/Admin dashboards

## Components

- Backend: FastAPI in backend/app
- Cloudflare layer: backend/app/middleware/cloudflare_security.py
- ML baseline: deterministic model in backend/app/ml/earnings_model.py
- Data store: SQLAlchemy models (worker, policy, claim, payout)
- Cache/dedupe: Redis key signature for duplicate claim fingerprints
- Frontend: Next.js + Tailwind with Worker and Admin consoles

## Security Layer Controls

- Validates Cloudflare request metadata (`cf-ray`, `cf-bot-score`, `cf-ipcountry`)
- Applies configurable country block list
- Enforces IP + path rate limiting (Redis preferred)
- Adds request correlation ID (`x-prism-request-id`) on every response
