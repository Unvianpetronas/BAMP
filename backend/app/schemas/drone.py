from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DroneIn(BaseModel):
    """SRS §3.2.2 — all numeric fields must be > 0 (MSG01)."""

    name: str = Field(min_length=1, max_length=100)
    type: str = Field(min_length=1, max_length=50)
    weight_kg: float = Field(gt=0)
    battery_capacity_wh: float = Field(gt=0)
    payload_capacity_kg: float = Field(gt=0)


class DroneOut(DroneIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_predefined: bool
    created_at: datetime
