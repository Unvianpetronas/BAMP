import pytest

from app.ml import train
from tests.conftest import synthetic_legs


def test_train_returns_cv_metrics_ranges_and_effective_hyperparameters():
    _, metrics, ranges, hp = train.train(synthetic_legs(), "random_forest", {"n_estimators": 10})
    assert set(metrics) == {"cv_rmse", "cv_mae", "cv_r2", "n_samples"}
    assert set(ranges) == set(train.FEATURES)
    assert hp["n_estimators"] == 10 and "max_depth" in hp


def test_missing_columns():
    with pytest.raises(train.DatasetError, match="energy_wh"):
        train.validate_dataset(synthetic_legs().drop(columns="energy_wh"))


def test_too_few_rows():
    with pytest.raises(train.DatasetError, match="at least"):
        train.validate_dataset(synthetic_legs(5))


def test_non_numeric_and_empty_values():
    df = synthetic_legs().astype({"payload_kg": object})
    df.loc[0, "payload_kg"] = "heavy"
    with pytest.raises(train.DatasetError, match="non-numeric"):
        train.validate_dataset(df)
    df = synthetic_legs()
    df.loc[0, "payload_kg"] = None
    with pytest.raises(train.DatasetError, match="empty"):
        train.validate_dataset(df)


def test_invalid_hyperparameters():
    with pytest.raises(ValueError, match="Invalid hyperparameters"):
        train.build_estimator("linear_regression", {"not_a_param": 1})


def test_br09_tier2_models_not_trainable():
    with pytest.raises(ValueError, match="BR-09"):
        train.build_estimator("xgboost", {})
