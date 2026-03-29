"""
PRISM — Monte Carlo Synthetic Fraud Dataset Generator
======================================================
Generates realistic gig-worker insurance claim records for Bengaluru
delivery workers. Each record is labelled as fraud (1) or legitimate (0)
using the same domain rules that power the live fraud_pipeline.py.

HOW MONTE CARLO WORKS HERE
---------------------------
We don't invent random numbers blindly. We define a probability
distribution for each feature based on what we know about real delivery
workers, then sample from those distributions thousands of times.

Each distribution encodes domain knowledge:
  - GPS offset: legitimate workers cluster within 500m of their zone.
    Fraudsters can be anywhere — modelled as a heavy-tail distribution.
  - Hour of claim: delivery work peaks 10am–10pm. Claims at 2–4am are rare
    and suspicious — modelled with a bimodal distribution.
  - Disruption score: real disruptions (storms, flooding) show high scores.
    Fake claims often happen on calm days — modelled differently for
    legit vs fraud populations.
  - Activity score: active workers have continuous GPS pings. Fraudsters
    often have near-zero activity before claiming.
  - Income delta: how much income was actually lost vs expected.

LABELLING RULES (domain knowledge -> label)
-------------------------------------------
A row is labelled fraud=1 if 2 or more of these conditions are true:
  1. GPS offset > 5000m from zone centre
  2. Disruption score < 0.25 (no real event that day)
  3. Activity score < 0.15 (app was barely open)
  4. Claim hour is 1-4am (outside all normal delivery windows)
  5. Income delta < 5% or > 92% of expected (implausible loss amount)
  6. is_duplicate flag set (same worker+policy claimed again within 1h)

These mirror the exact checks in _location_check, _activity_check, and
_duplicate_check in fraud_pipeline.py.

USAGE
-----
Run from the backend/ directory:

    python -m app.ml.generate_dataset

Output: data/synthetic_claims.csv  (~10,000 rows)
"""

import numpy as np
import pandas as pd
import os
import random

# ── Config ────────────────────────────────────────────────────────────────

RANDOM_SEED = 42
N_SAMPLES   = 10_000
FRAUD_RATE  = 0.18   # 18% fraud — realistic for parametric insurance
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "../../data/synthetic_claims.csv")

rng = np.random.default_rng(RANDOM_SEED)


# ── Feature samplers — LEGITIMATE worker ──────────────────────────────────

def _legit_gps_offset():
    """
    Legitimate workers are within their delivery zone.
    Normal distribution centred at 150m, rarely beyond 1km.
    Unit: metres
    """
    return float(np.clip(rng.normal(loc=150, scale=200), 0, 4500))


def _legit_disruption_score():
    """
    Legit workers claim during real disruptions.
    Beta distribution skewed toward high values (0.5-1.0).
    """
    return float(np.clip(rng.beta(a=5, b=2), 0.0, 1.0))


def _legit_activity_score():
    """
    Active workers have been online 60-240 min before claiming.
    Expressed as 0-1 (0=offline, 1=continuously active).
    Beta distribution skewed toward high activity.
    """
    return float(np.clip(rng.beta(a=6, b=2), 0.1, 1.0))


def _legit_claim_hour():
    """
    Delivery peaks: 10am-2pm (lunch), 7pm-10pm (dinner).
    Modelled as a mixture of two Gaussians.
    """
    if rng.random() < 0.55:
        hour = rng.normal(loc=20, scale=1.5)  # dinner peak
    else:
        hour = rng.normal(loc=12, scale=1.5)  # lunch peak
    return int(np.clip(hour, 8, 23))


def _legit_income_delta(expected):
    """
    Real disruptions reduce income by 30-80%.
    E.g. expected=220, actual=80 -> delta=140 -> delta_ratio=0.64
    """
    ratio = rng.uniform(0.30, 0.80)
    actual = expected * (1 - ratio)
    return float(actual), float(ratio)


def _legit_zone():
    return str(rng.choice(["central", "north", "south", "east", "west"]))


# ── Feature samplers — FRAUDULENT worker ──────────────────────────────────

def _fraud_gps_offset():
    """
    Fraudsters are often far outside any zone, or use GPS spoofing.
    Mixture: 40% plausible GPS (to avoid detection), 60% out-of-zone.
    """
    if rng.random() < 0.40:
        return float(rng.uniform(2000, 6000))   # trying to look legit
    else:
        return float(rng.uniform(6000, 20000))  # clearly outside zone


def _fraud_disruption_score():
    """
    Fraudsters claim on calm days. Low disruption score.
    Beta distribution skewed toward low values.
    """
    return float(np.clip(rng.beta(a=2, b=6), 0.0, 0.5))


def _fraud_activity_score():
    """
    Fraudsters barely open the app before claiming.
    Distribution skewed toward very low activity.
    """
    return float(np.clip(rng.beta(a=1.5, b=8), 0.0, 0.35))


def _fraud_claim_hour():
    """
    Fraudsters often submit at odd hours.
    Peak at 1-5am, but some try to blend in during daytime.
    """
    if rng.random() < 0.45:
        return int(rng.uniform(1, 5))    # 1am-5am: very suspicious
    elif rng.random() < 0.30:
        return int(rng.uniform(5, 8))    # early morning
    else:
        return int(rng.uniform(8, 23))   # daytime — trying to blend in


def _fraud_income_delta(expected):
    """
    Two fraud patterns:
    1. Tiny claimed loss (fishing for small easy approvals): delta ~5%
    2. Massive exaggerated loss: claimed 95%+ income loss on a calm day
    """
    if rng.random() < 0.50:
        ratio = rng.uniform(0.02, 0.10)   # pattern 1: suspicious small claim
    else:
        ratio = rng.uniform(0.85, 1.00)   # pattern 2: wildly exaggerated
    actual = expected * (1 - ratio)
    return float(max(actual, 0)), float(ratio)


def _fraud_zone():
    return str(rng.choice(["central", "north", "south", "east", "west", "unknown"]))


# ── Shared helpers ────────────────────────────────────────────────────────

def _make_worker_id():
    return int(rng.integers(1000, 9999))


def _make_policy_id(worker_id):
    return worker_id * 10 + int(rng.integers(1, 5))


def _expected_income():
    """
    Expected hourly income band: Rs 80-280 depending on zone/time.
    Log-normal to avoid negative values.
    """
    return float(np.clip(rng.lognormal(mean=5.1, sigma=0.3), 80, 280))


def _count_signals(gps, dis, act, hour, delta_ratio, is_dup):
    """
    Count how many fraud signals are present.
    Mirrors the exact thresholds from fraud_pipeline.py.
    """
    s = 0
    if gps > 5000:                                   s += 1  # _location_check
    if dis < 0.25:                                   s += 1  # AnomalyDetector
    if act < 0.15:                                   s += 1  # _activity_check
    if 1 <= hour <= 4:                               s += 1  # _temporal_score
    if delta_ratio < 0.05 or delta_ratio > 0.92:    s += 1  # _income_deviation_score
    if is_dup:                                       s += 1  # _duplicate_check
    return s


def _label(gps, dis, act, hour, delta_ratio, is_dup):
    """
    A record is labelled FRAUD if 2 or more fraud signals fire.
    This threshold means no single feature alone determines fraud —
    exactly the non-linear combination that makes RF/XGBoost the right fit.
    """
    return 1 if _count_signals(gps, dis, act, hour, delta_ratio, is_dup) >= 2 else 0


# ── Main generator ────────────────────────────────────────────────────────

def generate(n_samples=N_SAMPLES, fraud_rate=FRAUD_RATE, output_path=OUTPUT_PATH):
    """
    Generates n_samples synthetic claim records and saves to CSV.
    Returns the DataFrame.
    """
    n_fraud = int(n_samples * fraud_rate)
    n_legit = n_samples - n_fraud

    records = []
    seen_fingerprints = set()

    print(f"[PRISM] Generating {n_legit:,} legitimate + {n_fraud:,} fraud records...")

    # ── Legitimate records ────────────────────────────────────────────────
    for _ in range(n_legit):
        worker_id   = _make_worker_id()
        policy_id   = _make_policy_id(worker_id)
        expected    = _expected_income()
        actual, delta_ratio = _legit_income_delta(expected)
        gps         = _legit_gps_offset()
        dis         = _legit_disruption_score()
        act         = _legit_activity_score()
        hour        = _legit_claim_hour()
        zone        = _legit_zone()
        is_dup      = False  # legitimate workers almost never duplicate-claim

        records.append({
            "worker_id":        worker_id,
            "policy_id":        policy_id,
            "zone":             zone,
            "expected_income":  round(expected, 2),
            "actual_income":    round(actual, 2),
            "income_delta":     round(expected - actual, 2),
            "delta_ratio":      round(delta_ratio, 4),
            "gps_offset_m":     round(gps, 1),
            "disruption_score": round(dis, 4),
            "activity_score":   round(act, 4),
            "claim_hour":       hour,
            "is_duplicate":     int(is_dup),
            "fraud_signals":    _count_signals(gps, dis, act, hour, delta_ratio, is_dup),
            "is_fraud":         _label(gps, dis, act, hour, delta_ratio, is_dup),
            "population":       "legit",  # for analysis only, dropped before training
        })

    # ── Fraudulent records ────────────────────────────────────────────────
    for _ in range(n_fraud):
        worker_id   = _make_worker_id()
        policy_id   = _make_policy_id(worker_id)
        expected    = _expected_income()
        actual, delta_ratio = _fraud_income_delta(expected)
        gps         = _fraud_gps_offset()
        dis         = _fraud_disruption_score()
        act         = _fraud_activity_score()
        hour        = _fraud_claim_hour()
        zone        = _fraud_zone()

        # 5% of fraud records are intentional duplicate submissions
        fp_key = f"{worker_id}:{policy_id}"
        is_dup = (rng.random() < 0.05) and (fp_key in seen_fingerprints)
        seen_fingerprints.add(fp_key)

        records.append({
            "worker_id":        worker_id,
            "policy_id":        policy_id,
            "zone":             zone,
            "expected_income":  round(expected, 2),
            "actual_income":    round(max(actual, 0), 2),
            "income_delta":     round(expected - actual, 2),
            "delta_ratio":      round(delta_ratio, 4),
            "gps_offset_m":     round(gps, 1),
            "disruption_score": round(dis, 4),
            "activity_score":   round(act, 4),
            "claim_hour":       hour,
            "is_duplicate":     int(is_dup),
            "fraud_signals":    _count_signals(gps, dis, act, hour, delta_ratio, is_dup),
            "is_fraud":         _label(gps, dis, act, hour, delta_ratio, is_dup),
            "population":       "fraud",
        })

    # Shuffle so fraud rows aren't all at the bottom
    random.seed(RANDOM_SEED)
    random.shuffle(records)

    df = pd.DataFrame(records)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    df.to_csv(output_path, index=False)
    _print_summary(df, output_path)
    return df


def _print_summary(df, path):
    total = len(df)
    fraud = int(df["is_fraud"].sum())
    legit = total - fraud
    print(f"\n{'='*52}")
    print(f"  Dataset saved -> {path}")
    print(f"{'='*52}")
    print(f"  Total rows      : {total:,}")
    print(f"  Legitimate (0)  : {legit:,}  ({legit/total*100:.1f}%)")
    print(f"  Fraud (1)       : {fraud:,}  ({fraud/total*100:.1f}%)")
    print(f"\n  Feature ranges:")
    for col in ["gps_offset_m", "disruption_score", "activity_score",
                "claim_hour", "delta_ratio", "income_delta"]:
        print(f"    {col:<22s} min={df[col].min():.3f}  "
              f"max={df[col].max():.3f}  mean={df[col].mean():.3f}")
    print(f"{'='*52}\n")


if __name__ == "__main__":
    generate()
