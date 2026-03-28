
class RiskService:
    @staticmethod
    def compute_risk_tier(snapshot: dict) -> tuple[str, float]:
        rainfall = snapshot.get("rainfall_mm", 0)
        congestion = snapshot.get("congestion_index", 0)
        aqi = snapshot.get("aqi", 0)

        score = (rainfall / 140) * 0.4 + congestion * 0.35 + min(aqi / 500, 1) * 0.25

        if score < 0.35:
            return "low", 10.0
        if score < 0.65:
            return "medium", 20.0
        return "high", 35.0
