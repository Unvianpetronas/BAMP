from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.prediction_model import ModelVersion


class SimulationResult(Base):
    """ERD §3.1.5 #8 — per-leg + total predicted energy and feasibility.

    Always records the exact model version used (BR-02).
    """

    __tablename__ = "simulation_result"

    id: Mapped[int] = mapped_column(primary_key=True)
    mission_id: Mapped[int] = mapped_column(ForeignKey("mission.id", ondelete="CASCADE"))
    drone_id: Mapped[int] = mapped_column(ForeignKey("drone.id", ondelete="CASCADE"))
    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_version.id"))
    scenario_id: Mapped[int | None] = mapped_column(ForeignKey("scenario.id", ondelete="SET NULL"))
    # [{"position": int, "energy_wh": float}, ...]
    leg_results: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    total_energy_wh: Mapped[float]
    battery_capacity_wh: Mapped[float]
    safety_margin: Mapped[float]
    usable_capacity_wh: Mapped[float]
    # usable_capacity_wh - total_energy_wh; negative means Not Feasible by that many Wh.
    margin_wh: Mapped[float]
    feasibility: Mapped[bool]
    reduced_confidence: Mapped[bool]
    warnings: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    model_version: Mapped[ModelVersion] = relationship()


class ComparisonResult(Base):
    """ERD §3.1.5 #9 — denormalized link of a SimulationResult to its mission/drone (UC-09).

    Rows produced by one comparison run share a `comparison_id`.
    """

    __tablename__ = "comparison_result"

    id: Mapped[int] = mapped_column(primary_key=True)
    comparison_id: Mapped[str] = mapped_column(String(36), index=True)
    simulation_result_id: Mapped[int] = mapped_column(
        ForeignKey("simulation_result.id", ondelete="CASCADE")
    )
    mission_id: Mapped[int] = mapped_column(ForeignKey("mission.id", ondelete="CASCADE"))
    drone_id: Mapped[int] = mapped_column(ForeignKey("drone.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    simulation_result: Mapped[SimulationResult] = relationship()
