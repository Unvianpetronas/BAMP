"""Model training — shared by team-trained models (this CLI) and Operator uploads (FE-09 / UC-12).

Team usage (inside the backend container):
    python -m app.ml.train --csv data/kilthub_legs.csv --model random_forest --dataset-name "CMU KiltHub"

The CSV must contain the columns in app.ml.features (FEATURES + TARGET), one row per flight leg.
"""

import argparse
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import RegressorMixin
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.features import FEATURES, TARGET

CV_FOLDS = 5
MIN_ROWS = 2 * CV_FOLDS
RANDOM_STATE = 42

# BR-09: Tier 1 only. XGBoost / Gradient Boosting are Tier 2 and not trainable yet.
TRAINABLE_MODELS = {"linear_regression", "random_forest"}


class DatasetError(ValueError):
    pass


def build_estimator(model_name: str, hyperparameters: dict[str, Any]) -> RegressorMixin:
    if model_name == "linear_regression":
        est = Pipeline([("scaler", StandardScaler()), ("model", LinearRegression())])
        params = {f"model__{k}": v for k, v in hyperparameters.items()}
    elif model_name == "random_forest":
        est = RandomForestRegressor(n_estimators=200, random_state=RANDOM_STATE)
        params = hyperparameters
    else:
        raise ValueError(f"Model '{model_name}' is not trainable in Tier 1 (BR-09).")
    try:
        est.set_params(**params)
    except ValueError as exc:
        raise ValueError(f"Invalid hyperparameters for {model_name}: {exc}") from exc
    return est


def validate_dataset(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in [*FEATURES, TARGET] if c not in df.columns]
    if missing:
        raise DatasetError(f"Dataset is missing required columns: {', '.join(missing)}")
    data = df[[*FEATURES, TARGET]]
    try:
        data = data.astype(float)
    except ValueError as exc:
        raise DatasetError(f"Dataset contains non-numeric values: {exc}") from exc
    if data.isna().any().any():
        raise DatasetError("Dataset contains empty values.")
    if len(data) < MIN_ROWS:
        raise DatasetError(f"Dataset needs at least {MIN_ROWS} rows for {CV_FOLDS}-fold CV.")
    return data


def train(
    df: pd.DataFrame, model_name: str, hyperparameters: dict[str, Any] | None = None
) -> tuple[RegressorMixin, dict[str, float], dict[str, dict[str, float]], dict[str, Any]]:
    """Returns (fitted estimator, CV metrics, feature ranges for BR-03, hyperparameters used)."""
    hyperparameters = hyperparameters or {}
    data = validate_dataset(df)
    X, y = data[FEATURES], data[TARGET]

    estimator = build_estimator(model_name, hyperparameters)
    cv = cross_validate(
        estimator,
        X,
        y,
        cv=KFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE),
        scoring=("neg_root_mean_squared_error", "neg_mean_absolute_error", "r2"),
        error_score="raise",
    )
    metrics = {
        "cv_rmse": float(-np.mean(cv["test_neg_root_mean_squared_error"])),
        "cv_mae": float(-np.mean(cv["test_neg_mean_absolute_error"])),
        "cv_r2": float(np.mean(cv["test_r2"])),
        "n_samples": int(len(data)),
    }
    estimator.fit(X, y)

    feature_ranges = {f: {"min": float(X[f].min()), "max": float(X[f].max())} for f in FEATURES}
    # Record the full effective hyperparameters, not just the overrides (BR-02 traceability).
    core = estimator.named_steps["model"] if isinstance(estimator, Pipeline) else estimator
    effective = {k: v for k, v in core.get_params().items() if v is None or isinstance(v, (bool, int, float, str))}
    return estimator, metrics, feature_ranges, effective


def main() -> None:
    from app.db.session import SessionLocal
    from app.services.model_registry import register_version

    parser = argparse.ArgumentParser(description="Train and register a team model version.")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--model", required=True, choices=sorted(TRAINABLE_MODELS))
    parser.add_argument("--dataset-name", required=True)
    args = parser.parse_args()

    estimator, metrics, ranges, hp = train(pd.read_csv(args.csv), args.model)
    with SessionLocal() as db:
        mv = register_version(
            db,
            model_name=args.model,
            estimator=estimator,
            dataset_source="team",
            dataset_name=args.dataset_name,
            feature_ranges=ranges,
            hyperparameters=hp,
            metrics=metrics,
        )
        print(f"Registered {args.model} v{mv.version} (id={mv.id}): {metrics}")


if __name__ == "__main__":
    main()
