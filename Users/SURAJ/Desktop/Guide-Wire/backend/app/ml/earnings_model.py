from dataclasses import dataclass


@dataclass
class EarningsFeatures:
    hour: int
    rainfall_mm: float
    congestion_index: float
    aqi: float


class EarningsModel:
    # Lightweight deterministic baseline; replace with a trained model artifact in production.
    @staticmethod
    def predict(features: EarningsFeatures) -> float:
        base = 220.0
        hour_boost = 30.0 if features.hour in (12, 13, 19, 20, 21) else 0.0
        rain_penalty = min(features.rainfall_mm * 0.45, 50)
        traffic_penalty = features.congestion_index * 70
        pollution_penalty = min(features.aqi / 12, 30)
        prediction = base + hour_boost - rain_penalty - traffic_penalty - pollution_penalty
        return max(round(prediction, 2), 80.0)
