from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class ModelVersionOut(BaseModel):
    """Metadata only — never the artifact or its path (BR-11)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    prediction_model_id: int
    version: int
    dataset_source: Literal["team", "custom-uploaded"]
    dataset_name: str
    feature_set: list[str]
    feature_ranges: dict[str, dict[str, float]]
    hyperparameters: dict[str, Any]
    metrics: dict[str, float]
    created_at: datetime


class PredictionModelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    display_name: str
    tier: Literal[1, 2]
    versions: list[ModelVersionOut]


class RecommendationOut(BaseModel):
    model_version: ModelVersionOut
    model_display_name: str
    covers_inputs: bool | None
    explanation: str
    ai_generated: bool
    notice: str | None
