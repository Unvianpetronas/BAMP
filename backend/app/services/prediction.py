"""Prediction Engine (SRS §3.1.4 #1) — loads a version-locked artifact and predicts per leg.

BR-08: offline only. Reads local artifacts; never touches the network.
"""

import pandas as pd

from app.ml.features import FEATURES
from app.models import MissionLeg, ModelVersion
from app.services.model_registry import load_artifact


def leg_features(leg: MissionLeg, wind_speed_ms: float) -> dict[str, float]:
    return {
        "duration_min": leg.duration_min,
        "altitude_m": leg.altitude_m,
        "distance_km": leg.distance_km,
        "payload_kg": leg.payload_kg,
        "wind_speed_ms": wind_speed_ms,
    }


def predict_legs(
    model_version: ModelVersion, legs: list[MissionLeg], wind_speed_ms: float
) -> list[float]:
    estimator = load_artifact(model_version.artifact_path)
    X = pd.DataFrame([leg_features(leg, wind_speed_ms) for leg in legs], columns=FEATURES)
    return [float(v) for v in estimator.predict(X)]
