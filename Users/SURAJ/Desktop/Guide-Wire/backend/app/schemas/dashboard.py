from pydantic import BaseModel


class WorkerDashboard(BaseModel):
    worker_id: int
    expected_hourly_income: float
    protected_income: float
    active_policies: int
    total_payout: float


class AdminDashboard(BaseModel):
    disruption_heatmap: dict[str, float]
    risk_distribution: dict[str, int]
    claim_stats: dict[str, int]
    weekly_risk_forecast: dict[str, float]
