from random import uniform


class ExternalDataService:
    @staticmethod
    def weather(zone: str) -> dict:
        return {"zone": zone, "rainfall_mm": round(uniform(0, 140), 1), "temp_c": round(uniform(18, 44), 1)}

    @staticmethod
    def traffic(zone: str) -> dict:
        return {"zone": zone, "congestion_index": round(uniform(0, 1), 2)}

    @staticmethod
    def pollution(zone: str) -> dict:
        return {"zone": zone, "aqi": round(uniform(30, 420), 0)}

    @classmethod
    def disruption_snapshot(cls, zone: str) -> dict:
        weather = cls.weather(zone)
        traffic = cls.traffic(zone)
        pollution = cls.pollution(zone)
        return {**weather, **traffic, **pollution}
