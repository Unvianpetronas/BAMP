"""Model Registry Service (SRS §3.1.4 #7).

BR-02: versions are append-only — this module creates and reads, never updates.
BR-11: artifacts are only ever written to / loaded from ARTIFACT_DIR; nothing here serves the
file back out, and no such function should be added.
"""

import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import joblib
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.ml.features import FEATURES
from app.models import ModelVersion, PredictionModel


class ModelNotFoundError(LookupError):
    pass


def get_prediction_model(db: Session, model_name: str) -> PredictionModel:
    pm = db.scalar(select(PredictionModel).where(PredictionModel.name == model_name))
    if pm is None:
        raise ModelNotFoundError(f"Unknown prediction model '{model_name}'.")
    return pm


def register_version(
    db: Session,
    *,
    model_name: str,
    estimator: Any,
    dataset_source: Literal["team", "custom-uploaded"],
    dataset_name: str,
    feature_ranges: dict[str, dict[str, float]],
    hyperparameters: dict[str, Any],
    metrics: dict[str, float],
) -> ModelVersion:
    pm = get_prediction_model(db, model_name)
    next_version = (
        db.scalar(
            select(func.max(ModelVersion.version)).where(ModelVersion.prediction_model_id == pm.id)
        )
        or 0
    ) + 1

    artifact_dir = Path(settings.ARTIFACT_DIR) / model_name
    artifact_dir.mkdir(parents=True, exist_ok=True)
    # Artifact file name is unique so a failed DB commit can never overwrite a registered file.
    artifact_path = artifact_dir / f"v{next_version}_{uuid.uuid4().hex}.joblib"
    joblib.dump(estimator, artifact_path)

    mv = ModelVersion(
        prediction_model_id=pm.id,
        version=next_version,
        dataset_source=dataset_source,
        dataset_name=dataset_name,
        feature_set=list(FEATURES),
        feature_ranges=feature_ranges,
        hyperparameters=hyperparameters,
        metrics=metrics,
        artifact_path=str(artifact_path),
    )
    db.add(mv)
    try:
        db.commit()
    except Exception:
        db.rollback()
        artifact_path.unlink(missing_ok=True)
        raise
    db.refresh(mv)
    return mv


@lru_cache(maxsize=32)
def load_artifact(artifact_path: str) -> Any:
    """Safe to cache: a registered version's artifact never changes (BR-02)."""
    return joblib.load(artifact_path)
