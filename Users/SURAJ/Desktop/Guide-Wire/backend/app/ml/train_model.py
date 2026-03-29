"""
PRISM — Fraud Model Training & Evaluation
==========================================
Trains and evaluates two classifiers on the synthetic dataset:
  1. Random Forest
  2. XGBoost

Then saves the best-performing model as models/fraud_model.pkl
so it can be loaded by the live fraud_pipeline.py.

WHY THESE TWO MODELS (recap)
------------------------------
Fraud signals in PRISM are non-linear combinations:
  - GPS alone does NOT prove fraud
  - Low disruption score alone does NOT prove fraud
  - GPS out-of-zone + low disruption + inactive = very likely fraud

Tree-based models (RF, XGBoost) split on combinations of features
naturally. No feature engineering needed. They also give you
feature_importances_ so you can explain every decision to regulators.

METRICS WE CARE ABOUT
-----------------------
  Precision  — of all claims we flagged as fraud, how many were actually fraud?
               Low precision = innocent workers wrongly rejected (bad for trust)

  Recall     — of all actual fraud cases, how many did we catch?
               Low recall = fraudsters slipping through (bad for losses)

  F1 Score   — harmonic mean of precision and recall. The primary metric
               when classes are imbalanced (18% fraud vs 82% legit).

  AUC-ROC    — overall discriminative power across all threshold levels.
               0.5 = random, 1.0 = perfect.

USAGE
-----
Run from the backend/ directory AFTER generating the dataset:

    python -m app.ml.generate_dataset   # step 1
    python -m app.ml.train_model        # step 2

Output:
    models/fraud_model.pkl     — best model (RF or XGBoost)
    models/training_report.txt — full evaluation report
"""

import os
import pickle
import warnings
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    f1_score,
    precision_score,
    recall_score,
)

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────

_BASE        = os.path.dirname(__file__)
DATA_PATH    = os.path.join(_BASE, "../../data/synthetic_claims.csv")
MODEL_DIR    = os.path.join(_BASE, "../../models")
MODEL_PATH   = os.path.join(MODEL_DIR, "fraud_model.pkl")
REPORT_PATH  = os.path.join(MODEL_DIR, "training_report.txt")

# ── Features used for training ────────────────────────────────────────────
# These MUST match the features available in the live fraud_pipeline.py.
# We deliberately exclude: worker_id, policy_id, population (metadata),
# fraud_signals (derived label helper — leaks the answer to the model).

FEATURE_COLS = [
    "gps_offset_m",       # from _location_check
    "disruption_score",   # from AnomalyDetector (income context)
    "activity_score",     # from _activity_check
    "claim_hour",         # from _temporal_score
    "delta_ratio",        # from _income_deviation_score
    "income_delta",       # raw loss amount
    "is_duplicate",       # from _duplicate_check (Redis)
    "zone_encoded",       # zone encoded as integer
]

LABEL_COL = "is_fraud"

RANDOM_SEED = 42


# ── Load & prepare data ───────────────────────────────────────────────────

def load_data(path=DATA_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Dataset not found at {path}\n"
            f"Run first:  python -m app.ml.generate_dataset"
        )

    df = pd.read_csv(path)

    # Encode zone (categorical -> integer)
    le = LabelEncoder()
    df["zone_encoded"] = le.fit_transform(df["zone"].astype(str))

    X = df[FEATURE_COLS].copy()
    y = df[LABEL_COL].copy()

    print(f"[PRISM] Dataset loaded: {len(df):,} rows | "
          f"fraud={int(y.sum()):,} ({y.mean()*100:.1f}%) | "
          f"legit={int((y==0).sum()):,}")
    return X, y, le


# ── Train Random Forest ───────────────────────────────────────────────────

def train_random_forest(X_train, y_train):
    """
    Random Forest: ensemble of decision trees.
    Each tree sees a random subset of rows and features.
    Final prediction = majority vote across all trees.

    n_estimators=200  -> 200 trees (more = more stable, slower)
    max_depth=12      -> trees can be moderately deep
    class_weight      -> tells the model fraud cases are rarer and more important
    """
    print("\n[RF] Training Random Forest (200 trees)...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=5,
        class_weight="balanced",   # compensates for 18% fraud imbalance
        random_state=RANDOM_SEED,
        n_jobs=-1,                 # use all CPU cores
    )
    model.fit(X_train, y_train)
    print("[RF] Training complete.")
    return model


# ── Train XGBoost ─────────────────────────────────────────────────────────

def train_xgboost(X_train, y_train):
    """
    XGBoost: gradient boosted trees.
    Each new tree corrects the errors of the previous ensemble.
    Typically 2-5% better than RF on fraud detection tasks.

    scale_pos_weight = legit_count / fraud_count
        -> tells XGBoost to penalise missing a fraud case more than
           falsely flagging a legitimate claim.
    """
    try:
        import xgboost as xgb
    except ImportError:
        print("[XGB] xgboost not installed. Skipping.")
        print("      To install: pip install xgboost")
        return None

    fraud_count = int(y_train.sum())
    legit_count = int((y_train == 0).sum())
    scale_pos_weight = legit_count / max(fraud_count, 1)

    print(f"\n[XGB] Training XGBoost "
          f"(scale_pos_weight={scale_pos_weight:.2f})...")
    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=RANDOM_SEED,
        verbosity=0,
    )
    model.fit(X_train, y_train)
    print("[XGB] Training complete.")
    return model


# ── Evaluate one model ────────────────────────────────────────────────────

def evaluate(model, X_test, y_test, name):
    """
    Runs the model on the held-out test set and prints a full report.
    Returns a dict of key metrics.
    """
    y_pred      = model.predict(X_test)
    y_prob      = model.predict_proba(X_test)[:, 1]

    precision   = precision_score(y_test, y_pred, zero_division=0)
    recall      = recall_score(y_test, y_pred, zero_division=0)
    f1          = f1_score(y_test, y_pred, zero_division=0)
    auc         = roc_auc_score(y_test, y_prob)
    cm          = confusion_matrix(y_test, y_pred)

    tn, fp, fn, tp = cm.ravel()

    lines = [
        f"\n{'='*56}",
        f"  Model : {name}",
        f"{'='*56}",
        f"  Precision  : {precision:.4f}   "
            f"(of flagged fraud, how many were real?)",
        f"  Recall     : {recall:.4f}   "
            f"(of all fraud, how many did we catch?)",
        f"  F1 Score   : {f1:.4f}   (primary metric — balances both)",
        f"  AUC-ROC    : {auc:.4f}   (1.0 = perfect, 0.5 = random)",
        f"\n  Confusion Matrix:",
        f"                   Predicted legit  Predicted fraud",
        f"  Actual legit         {tn:>6}           {fp:>6}",
        f"  Actual fraud         {fn:>6}           {tp:>6}",
        f"\n  True positives  (fraud caught)        : {tp}",
        f"  False negatives (fraud missed)        : {fn}   <- minimise this",
        f"  False positives (legit wrongly flagged): {fp}   <- minimise this",
        f"{'='*56}",
    ]

    report_str = "\n".join(lines)
    print(report_str)

    return {
        "name": name,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "auc": auc,
        "report_str": report_str,
        "model": model,
    }


# ── Feature importance ────────────────────────────────────────────────────

def print_feature_importance(model, name):
    """
    Shows which features the model relies on most.
    This is what you show regulators / your team to explain decisions.
    """
    importances = model.feature_importances_
    pairs = sorted(zip(FEATURE_COLS, importances), key=lambda x: -x[1])

    print(f"\n  Feature importances ({name}):")
    lines = []
    for feat, imp in pairs:
        bar = "#" * int(imp * 40)
        line = f"    {feat:<22s} {imp:.4f}  {bar}"
        print(line)
        lines.append(line)
    return lines


# ── Cross-validation ──────────────────────────────────────────────────────

def cross_validate(model, X, y, name):
    """
    5-fold stratified cross-validation.
    Gives a more reliable estimate than a single train/test split.
    Stratified = each fold preserves the 18%/82% fraud/legit ratio.
    """
    print(f"\n[CV] 5-fold cross-validation for {name}...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    scores = cross_val_score(model, X, y, cv=cv, scoring="f1", n_jobs=-1)
    print(f"  F1 per fold: {[round(s, 4) for s in scores]}")
    print(f"  Mean F1: {scores.mean():.4f} +/- {scores.std():.4f}")
    return scores


# ── Save model ────────────────────────────────────────────────────────────

def save_model(model, label_encoder, feature_cols, path=MODEL_PATH):
    """
    Saves the model + metadata needed to use it in fraud_pipeline.py.
    Pickle bundles everything the pipeline needs at inference time.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bundle = {
        "model":         model,
        "label_encoder": label_encoder,
        "feature_cols":  feature_cols,
        "version":       "1.0.0",
        "trained_on":    pd.Timestamp.now().isoformat(),
    }
    with open(path, "wb") as f:
        pickle.dump(bundle, f)
    print(f"\n[PRISM] Model saved -> {path}")


# ── Save text report ──────────────────────────────────────────────────────

def save_report(lines, path=REPORT_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"[PRISM] Training report saved -> {path}")


# ── Main ──────────────────────────────────────────────────────────────────

def train(data_path=DATA_PATH):
    report_lines = [
        "PRISM Fraud Model — Training Report",
        f"Generated: {pd.Timestamp.now().isoformat()}",
        "=" * 56,
    ]

    # 1. Load data
    X, y, le = load_data(data_path)

    # 2. Train/test split — 80% train, 20% test
    #    stratify=y preserves the fraud ratio in both splits
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_SEED, stratify=y
    )
    print(f"\n[PRISM] Split: {len(X_train):,} train / {len(X_test):,} test")

    results = []

    # 3. Train and evaluate Random Forest
    rf_model = train_random_forest(X_train, y_train)
    rf_result = evaluate(rf_model, X_test, y_test, "Random Forest")
    rf_importance = print_feature_importance(rf_model, "Random Forest")
    rf_cv = cross_validate(rf_model, X, y, "Random Forest")
    report_lines.append(rf_result["report_str"])
    report_lines.extend(rf_importance)
    results.append(rf_result)

    # 4. Train and evaluate XGBoost (if installed)
    xgb_model = train_xgboost(X_train, y_train)
    if xgb_model is not None:
        xgb_result = evaluate(xgb_model, X_test, y_test, "XGBoost")
        xgb_importance = print_feature_importance(xgb_model, "XGBoost")
        xgb_cv = cross_validate(xgb_model, X, y, "XGBoost")
        report_lines.append(xgb_result["report_str"])
        report_lines.extend(xgb_importance)
        results.append(xgb_result)

    # 5. Pick the best model by F1 score
    best = max(results, key=lambda r: r["f1"])
    print(f"\n[PRISM] Best model: {best['name']} "
          f"(F1={best['f1']:.4f}, AUC={best['auc']:.4f})")

    winner_line = f"\nBest model: {best['name']} | F1={best['f1']:.4f} | AUC={best['auc']:.4f}"
    report_lines.append(winner_line)

    # 6. Save best model
    save_model(best["model"], le, FEATURE_COLS)
    save_report(report_lines)

    return best["model"], le


# ── Inference helper (used by fraud_pipeline.py) ──────────────────────────

def load_model(path=MODEL_PATH):
    """
    Loads the saved model bundle.
    Call this from fraud_pipeline.py to get ML scores at inference time.

    Usage in fraud_pipeline.py:
        from app.ml.train_model import load_model, ml_fraud_score
        _ml_bundle = load_model()

        score = ml_fraud_score(_ml_bundle, gps_offset_m=300, disruption_score=0.8, ...)
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Model not found at {path}\n"
            f"Run first:  python -m app.ml.train_model"
        )
    with open(path, "rb") as f:
        return pickle.load(f)


def ml_fraud_score(bundle, **features):
    """
    Given a trained model bundle and raw claim features,
    returns a fraud probability (0.0 to 1.0).

    This is what replaces (or augments) the rule-based checks
    in the live fraud_pipeline.py.

    Example:
        score = ml_fraud_score(
            bundle,
            gps_offset_m=250,
            disruption_score=0.72,
            activity_score=0.85,
            claim_hour=14,
            delta_ratio=0.55,
            income_delta=120.0,
            is_duplicate=0,
            zone="central",
        )
        # returns e.g. 0.031  (very likely legitimate)
    """
    model   = bundle["model"]
    le      = bundle["label_encoder"]
    feat_cols = bundle["feature_cols"]

    zone_raw = features.get("zone", "central")
    try:
        zone_enc = int(le.transform([str(zone_raw)])[0])
    except ValueError:
        zone_enc = 0  # unknown zone -> default

    row = {
        "gps_offset_m":    features.get("gps_offset_m", 0),
        "disruption_score": features.get("disruption_score", 0.5),
        "activity_score":  features.get("activity_score", 0.5),
        "claim_hour":      features.get("claim_hour", 12),
        "delta_ratio":     features.get("delta_ratio", 0.5),
        "income_delta":    features.get("income_delta", 0),
        "is_duplicate":    features.get("is_duplicate", 0),
        "zone_encoded":    zone_enc,
    }

    X = pd.DataFrame([row])[feat_cols]
    prob = float(model.predict_proba(X)[0][1])
    return round(prob, 4)


if __name__ == "__main__":
    train()
