"""Feasibility Calculator (SRS §3.1.4 #2, BR-04, BR-05)."""

from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class Feasibility:
    total_energy_wh: float
    battery_capacity_wh: float
    safety_margin: float
    usable_capacity_wh: float
    margin_wh: float
    feasible: bool


def total_energy(leg_energies_wh: list[float]) -> float:
    """BR-04: total mission energy is the sum of per-leg predictions."""
    return float(sum(leg_energies_wh))


def assess(total_energy_wh: float, battery_capacity_wh: float) -> Feasibility:
    """BR-05: Feasible iff total <= capacity * (1 - SAFETY_MARGIN)."""
    margin = settings.SAFETY_MARGIN
    usable = battery_capacity_wh * (1 - margin)
    return Feasibility(
        total_energy_wh=total_energy_wh,
        battery_capacity_wh=battery_capacity_wh,
        safety_margin=margin,
        usable_capacity_wh=usable,
        margin_wh=usable - total_energy_wh,
        feasible=total_energy_wh <= usable,
    )
