from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ScenarioIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    drone_id: int
    mission_id: int
    model_version_id: int


class ScenarioOut(ScenarioIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
