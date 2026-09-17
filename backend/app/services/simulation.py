"""Mission simulation (UC-07, includes UC-08) and drone comparison (UC-09)."""

import uuid

from sqlalchemy.orm import Session

from app.models import ComparisonResult, Drone, Mission, ModelVersion, SimulationResult
from app.services import feasibility
from app.services.prediction import leg_features, predict_legs
from app.services.range_validator import check_ranges


class SimulationInputError(ValueError):
    pass


MSG06 = "Add at least one flight leg before running a simulation."


def _build_result(mission: Mission, drone: Drone, model_version: ModelVersion) -> SimulationResult:
    if not mission.legs:
        raise SimulationInputError(MSG06)  # BR-01
    if mission.wind_speed is None:
        raise SimulationInputError("Enter the mission wind speed before running a simulation.")
    wind = mission.wind_speed.wind_speed_ms

    warnings = []
    for leg in mission.legs:
        values = leg_features(leg, wind)
        values.pop("wind_speed_ms")  # checked once per mission below
        warnings += check_ranges(values, model_version.feature_ranges, leg_position=leg.position)
    warnings += check_ranges({"wind_speed_ms": wind}, model_version.feature_ranges)

    energies = predict_legs(model_version, mission.legs, wind)
    result = feasibility.assess(feasibility.total_energy(energies), drone.battery_capacity_wh)

    return SimulationResult(
        mission_id=mission.id,
        drone_id=drone.id,
        model_version_id=model_version.id,
        leg_results=[
            {"position": leg.position, "energy_wh": e} for leg, e in zip(mission.legs, energies)
        ],
        total_energy_wh=result.total_energy_wh,
        battery_capacity_wh=result.battery_capacity_wh,
        safety_margin=result.safety_margin,
        usable_capacity_wh=result.usable_capacity_wh,
        margin_wh=result.margin_wh,
        feasibility=result.feasible,
        reduced_confidence=bool(warnings),  # BR-03: flag, still predict
        warnings=warnings,
    )


def run_simulation(
    db: Session,
    mission: Mission,
    drone: Drone,
    model_version: ModelVersion,
    scenario_id: int | None = None,
) -> SimulationResult:
    sim = _build_result(mission, drone, model_version)
    sim.scenario_id = scenario_id
    db.add(sim)
    db.commit()
    db.refresh(sim)
    return sim


def run_comparison(
    db: Session, mission: Mission, drones: list[Drone], model_version: ModelVersion
) -> tuple[str, list[SimulationResult]]:
    """Same mission, wind speed and model version applied to every drone (UC-09)."""
    comparison_id = str(uuid.uuid4())
    sims = [_build_result(mission, drone, model_version) for drone in drones]
    db.add_all(sims)
    db.flush()
    db.add_all(
        ComparisonResult(
            comparison_id=comparison_id,
            simulation_result_id=sim.id,
            mission_id=sim.mission_id,
            drone_id=sim.drone_id,
        )
        for sim in sims
    )
    db.commit()
    for sim in sims:
        db.refresh(sim)
    return comparison_id, sims
