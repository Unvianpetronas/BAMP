from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.wind_speed_condition import WindSpeedCondition


class Mission(Base):
    """ERD §3.1.5 #2 — a named mission composed of one or more flight legs (BR-01)."""

    __tablename__ = "mission"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Optional while editing; required only when saved as a Scenario (SRS §3.3.1).
    name: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    legs: Mapped[list["MissionLeg"]] = relationship(
        back_populates="mission",
        cascade="all, delete-orphan",
        order_by="MissionLeg.position",
    )
    wind_speed: Mapped[WindSpeedCondition | None] = relationship(
        cascade="all, delete-orphan", uselist=False
    )


class MissionLeg(Base):
    """ERD §3.1.5 #3 — one leg: duration, altitude, distance, payload."""

    __tablename__ = "mission_leg"
    __table_args__ = (
        CheckConstraint("duration_min > 0", name="ck_leg_duration_positive"),
        CheckConstraint("altitude_m > 0", name="ck_leg_altitude_positive"),
        CheckConstraint("distance_km > 0", name="ck_leg_distance_positive"),
        CheckConstraint("payload_kg > 0", name="ck_leg_payload_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    mission_id: Mapped[int] = mapped_column(ForeignKey("mission.id", ondelete="CASCADE"))
    position: Mapped[int]
    duration_min: Mapped[float]
    altitude_m: Mapped[float]
    distance_km: Mapped[float]
    payload_kg: Mapped[float]

    mission: Mapped[Mission] = relationship(back_populates="legs")
