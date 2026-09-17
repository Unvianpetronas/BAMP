from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class WindSpeedCondition(Base):
    """ERD §3.1.5 #4 (SRS name: WeatherCondition) — ONE wind speed per mission in Tier 1.

    FK is mission_id, not leg_id — see docs/DECISIONS.md (2026-09-15). Per-leg override is Tier 2
    and means a schema migration re-pointing this at mission_leg.
    """

    __tablename__ = "wind_speed_condition"
    __table_args__ = (CheckConstraint("wind_speed_ms >= 0", name="ck_wind_speed_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    mission_id: Mapped[int] = mapped_column(
        ForeignKey("mission.id", ondelete="CASCADE"), unique=True
    )
    wind_speed_ms: Mapped[float]
