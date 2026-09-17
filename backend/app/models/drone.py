from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Drone(Base):
    """ERD §3.1.5 #1 — a predefined (read-only) or custom drone configuration."""

    __tablename__ = "drone"
    __table_args__ = (
        CheckConstraint("weight_kg > 0", name="ck_drone_weight_positive"),
        CheckConstraint("battery_capacity_wh > 0", name="ck_drone_battery_positive"),
        CheckConstraint("payload_capacity_kg > 0", name="ck_drone_payload_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(50))
    weight_kg: Mapped[float]
    battery_capacity_wh: Mapped[float]
    payload_capacity_kg: Mapped[float]
    is_predefined: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
