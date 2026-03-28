from datetime import datetime

from app.ml.earnings_model import EarningsFeatures, EarningsModel
from app.services.external_data_service import ExternalDataService


class MonitoringService:
    @staticmethod
    def expected_hourly_income(zone: str) -> tuple[float, dict]:
        snapshot = ExternalDataService.disruption_snapshot(zone)
        features = EarningsFeatures(
            hour=datetime.now().hour,
            rainfall_mm=snapshot["rainfall_mm"],
            congestion_index=snapshot["congestion_index"],
            aqi=float(snapshot["aqi"]),
        )
        expected = EarningsModel.predict(features)
        return expected, snapshot
