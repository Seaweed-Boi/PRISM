# PRISM - Predictive Income Protection for Gig Workers

PRISM is an AI-powered parametric insurance platform that protects delivery workers from income loss caused by weather, traffic, pollution, or platform disruptions.

This implementation includes:

- FastAPI backend with policy, claim, fraud, and payout engines
- Cloudflare-style security middleware with bot/rate/country checks
- Next.js frontend with Worker and Admin dashboards
- Redis duplicate-claim check
- Simulated disruption and instant payout flow

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the flow aligned with your reference image.

## Project Structure

- `backend/` - FastAPI services, models, APIs
- `frontend/` - Next.js App Router dashboards
- `docker-compose.yml` - PostgreSQL and Redis containers

## Backend Setup

1. Open terminal in `backend/`
2. Create and activate virtual environment
3. Install dependencies
4. Run API server

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --app-dir . --reload --port 8000
```

API docs: `http://localhost:8000/docs`

## Frontend Setup

1. Open second terminal in `frontend/`
2. Install dependencies
3. Start development server

```powershell
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Frontend URL: `http://localhost:3000`

## Optional Infra (Redis + Postgres)

```powershell
docker compose up -d
```

Default backend uses SQLite for simplicity. To switch to PostgreSQL, update `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg2://prism:prism@localhost:5432/prism
```

## Demo Flow

1. Open Worker Console
2. Click `Step 1: Onboard`
3. Click `Step 2: Buy Weekly Policy`
4. Click `Step 3-4: Simulate Disruption + Claim`
5. Observe updated protected income and payout
6. Open Admin Console and click `Refresh Analytics`

## Implemented Engines

- Cloudflare Security Layer:
  - Optional Cloudflare header enforcement (`cf-ray`)
  - Bot score threshold enforcement (`cf-bot-score`)
  - Country-based blocking (`cf-ipcountry`)
  - IP/path rate limiting (Redis-backed with in-memory fallback)
  - Request tracing via `x-prism-request-id`
- Disruption Engine: weather/traffic/pollution snapshots
- Risk Model: low/medium/high risk tier with dynamic premium
- Earnings Prediction: hourly expected income baseline model
- Fraud Engine:
  - GPS sanity validation
  - Activity validation
  - Duplicate claim detection (Redis signature)
- Decision Engine: claim approve/reject logic
- Payout Engine: simulated UPI payout reference generation

## Cloudflare Security Configuration

Set these variables in `backend/.env`:

```env
CLOUDFLARE_SECURITY_ENABLED=true
CLOUDFLARE_ALLOW_LOCAL_DEV=true
CLOUDFLARE_REQUIRE_RAY=false
CLOUDFLARE_MIN_BOT_SCORE=20
CLOUDFLARE_RATE_LIMIT_WINDOW_SECONDS=60
CLOUDFLARE_RATE_LIMIT_MAX_REQUESTS=120
CLOUDFLARE_BLOCK_COUNTRIES=
```

For production, set `CLOUDFLARE_ALLOW_LOCAL_DEV=false` and typically set `CLOUDFLARE_REQUIRE_RAY=true`.
