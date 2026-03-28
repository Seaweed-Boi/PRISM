from fastapi import APIRouter

from app.api.v1.workers import router as workers_router
from app.api.v1.policies import router as policies_router
from app.api.v1.claims import router as claims_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.fraud import router as fraud_router

api_router = APIRouter()
api_router.include_router(workers_router, prefix="/workers", tags=["workers"])
api_router.include_router(policies_router, prefix="/policies", tags=["policies"])
api_router.include_router(claims_router, prefix="/claims", tags=["claims"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(fraud_router, prefix="/fraud", tags=["fraud"])
