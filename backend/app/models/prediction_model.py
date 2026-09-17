from datetime import datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, event, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class PredictionModel(Base):
    """ERD §3.1.5 #5 — a candidate model type. `tier` marks Tier 1 vs Tier 2 (BR-09)."""

    __tablename__ = "prediction_model"
    __table_args__ = (CheckConstraint("tier IN (1, 2)", name="ck_prediction_model_tier"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    display_name: Mapped[str] = mapped_column(String(100))
    tier: Mapped[int]

    versions: Mapped[list["ModelVersion"]] = relationship(
        back_populates="prediction_model", order_by="ModelVersion.version"
    )


class ModelVersionImmutableError(Exception):
    pass


class ModelVersion(Base):
    """ERD §3.1.5 #6 — an immutable registered artifact (BR-02). Never add an update path.

    `artifact_path` points at a local .joblib file; the file itself is never served (BR-11).
    """

    __tablename__ = "model_version"
    __table_args__ = (
        UniqueConstraint("prediction_model_id", "version", name="uq_model_version"),
        CheckConstraint(
            "dataset_source IN ('team', 'custom-uploaded')", name="ck_model_version_dataset_source"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    prediction_model_id: Mapped[int] = mapped_column(ForeignKey("prediction_model.id"))
    version: Mapped[int]
    dataset_source: Mapped[str] = mapped_column(String(20))
    dataset_name: Mapped[str] = mapped_column(String(200))
    feature_set: Mapped[list[str]] = mapped_column(JSON)
    # {feature: {"min": float, "max": float}} — the training-data range used by BR-03.
    feature_ranges: Mapped[dict[str, dict[str, float]]] = mapped_column(JSON)
    hyperparameters: Mapped[dict[str, Any]] = mapped_column(JSON)
    metrics: Mapped[dict[str, float]] = mapped_column(JSON)
    artifact_path: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    prediction_model: Mapped[PredictionModel] = relationship(back_populates="versions")


@event.listens_for(ModelVersion, "before_update")
def _reject_model_version_update(mapper, connection, target) -> None:
    raise ModelVersionImmutableError(
        f"ModelVersion {target.id} is immutable (BR-02); register a new version instead."
    )
