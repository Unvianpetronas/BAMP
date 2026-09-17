from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MissionLegIn(BaseModel):
    """SRS §3.3.1 — duration (min), altitude (m), distance (km), payload (kg), all > 0."""

    duration_min: float = Field(gt=0)
    altitude_m: float = Field(gt=0)
    distance_km: float = Field(gt=0)
    payload_kg: float = Field(gt=0)


class MissionLegOut(MissionLegIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int


class MissionIn(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    legs: list[MissionLegIn]
    # Tier 1: one wind speed for the whole mission (docs/DECISIONS.md). Not per leg.
    wind_speed_ms: float = Field(ge=0)

    @field_validator("legs")
    @classmethod
    def at_least_one_leg(cls, legs: list[MissionLegIn]) -> list[MissionLegIn]:
        if not legs:
            raise ValueError("Add at least one flight leg before running a simulation.")  # BR-01
        return legs


class MissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None
    legs: list[MissionLegOut]
    wind_speed_ms: float | None
    created_at: datetime
