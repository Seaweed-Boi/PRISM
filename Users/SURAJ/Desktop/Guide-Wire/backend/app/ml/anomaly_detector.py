"""
Anomaly Detection (ML) — PRISM Fraud Detection Engine

Lightweight statistical anomaly detector that scores claim requests without
requiring a pre-trained artifact.  In production this would be replaced with
a serialised XGBoost / Isolation-Forest model.

Sub-scores produced:
  • income_deviation  – how far actual income deviates from the historical
                        band for that worker and zone.
  • temporal          – requests outside normal working-hours windows score
                        higher.
  • pattern           – repeated identical expected-income values may indicate
                        scripted fraud.
"""

from __future__ import annotations

import math
from collections import defaultdict, deque
from threading import Lock


# ---------------------------------------------------------------------------
# In-memory worker history store (replaced by DB query in production)
# ---------------------------------------------------------------------------
_worker_history: defaultdict[int, deque] = defaultdict(lambda: deque(maxlen=50))  # type: ignore[type-arg]
_history_lock = Lock()

# Typical income band per worker (seeded; updated on each call)
_worker_income_band: dict[int, tuple] = {}


def _update_history(worker_id: int, actual: float, expected: float) -> None:
    with _history_lock:
        _worker_history[worker_id].append((actual, expected))
        records = list(_worker_history[worker_id])
        actuals = [r[0] for r in records]
        mean = sum(actuals) / len(actuals)
        variance = sum((x - mean) ** 2 for x in actuals) / len(actuals)
        std = math.sqrt(variance) if variance > 0 else 30.0
        _worker_income_band[worker_id] = (mean - 2 * std, mean + 2 * std)


def _income_deviation_score(worker_id: int, actual: float) -> float:
    """Returns 0..1 where 1 = highly anomalous income drop."""
    band = _worker_income_band.get(worker_id)
    if not band:
        # No history yet – cannot score, assume normal
        return 0.1
    lo, hi = band
    if lo <= actual <= hi:
        return 0.05
    distance = min(abs(actual - lo), abs(actual - hi))
    band_width = max(hi - lo, 1.0)
    return min(distance / band_width, 1.0)


def _temporal_score(hour: int) -> float:
    """Returns 0..1 where 1 = unusual hour for a delivery worker."""
    # 8 AM–11 PM is normal delivery operating window
    if 8 <= hour <= 23:
        return 0.05
    # Late night / very early morning
    if 0 <= hour < 5:
        return 0.75
    return 0.4


def _pattern_score(worker_id: int, expected: float) -> float:
    """Detects repeated identical expected-income values (scripted fraud)."""
    with _history_lock:
        history = list(_worker_history.get(worker_id, deque()))  # type: ignore[arg-type]
    if len(history) < 3:
        return 0.0
    tail = history[max(0, len(history) - 5):]
    recent_expected = [r[1] for r in tail]
    matches = sum(1 for v in recent_expected if abs(v - expected) < 0.01)
    return min(matches / 5, 1.0)


class AnomalyDetector:
    """
    Stateless anomaly scoring component.
    Thread-safe: uses module-level locked stores.
    """

    @staticmethod
    def score(
        worker_id: int,
        actual_income: float,
        expected_income: float,
        request_hour: int,
    ) -> dict:
        """
        Returns a dict with sub-scores and a composite anomaly_score (0..1).
        Higher = more anomalous.
        """
        _update_history(worker_id, actual_income, expected_income)

        inc = _income_deviation_score(worker_id, actual_income)
        tem = _temporal_score(request_hour)
        pat = _pattern_score(worker_id, expected_income)

        composite = round(float(inc * 0.50 + tem * 0.25 + pat * 0.25), 3)

        return {
            "income_deviation_score": inc,
            "temporal_score": tem,
            "pattern_score": pat,
            "anomaly_score": composite,
        }
