from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.drone import Drone
from app.models.mission import Mission
from app.models.prediction_model import ModelVersion


class Scenario(Base):
    """ERD §3.1.5 #7 — saved drone + mission (incl. wind speed) + model version (UC-10/UC-11)."""

    __tablename__ = "scenario"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    drone_id: Mapped[int] = mapped_column(ForeignKey("drone.id"))
    mission_id: Mapped[int] = mapped_column(ForeignKey("mission.id"))
    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_version.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    drone: Mapped[Drone] = relationship()
    mission: Mapped[Mission] = relationship()
    model_version: Mapped[ModelVersion] = relationship()
