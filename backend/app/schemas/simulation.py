from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.model import ModelVersionOut


class SimulationRequest(BaseModel):
    mission_id: int
    drone_id: int
    model_version_id: int


class LegResult(BaseModel):
    position: int
    energy_wh: float


class SimulationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mission_id: int
    drone_id: int
    scenario_id: int | None
    # BR-02: every result carries the exact version and its metrics.
    model_version: ModelVersionOut
    leg_results: list[LegResult]
    total_energy_wh: float
    battery_capacity_wh: float
    safety_margin: float
    usable_capacity_wh: float
    margin_wh: float
    feasibility: bool
    reduced_confidence: bool
    warnings: list[dict[str, Any]]
    message: str | None = None
    created_at: datetime


class ComparisonRequest(BaseModel):
    mission_id: int
    drone_ids: list[int] = Field(min_length=2)
    model_version_id: int


class ComparisonOut(BaseModel):
    comparison_id: str
    results: list[SimulationOut]
