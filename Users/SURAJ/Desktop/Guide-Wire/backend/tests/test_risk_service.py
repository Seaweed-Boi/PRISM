from app.services.risk_service import RiskService


def test_risk_low():
    tier, premium = RiskService.compute_risk_tier({"rainfall_mm": 5, "congestion_index": 0.1, "aqi": 50})
    assert tier == "low"
    assert premium == 10.0


def test_risk_high():
    tier, premium = RiskService.compute_risk_tier({"rainfall_mm": 130, "congestion_index": 0.9, "aqi": 390})
    assert tier == "high"
    assert premium == 35.0
