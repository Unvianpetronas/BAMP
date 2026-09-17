"""UC-07 Run Mission Simulation (includes UC-08 Feasibility) and UC-09 Compare Drones (SRS §3.5-3.6)."""

from fastapi import APIRouter, HTTPException

from app.api.deps import DB, get_or_404
from app.models import Drone, Mission, ModelVersion, SimulationResult
from app.schemas.simulation import ComparisonOut, ComparisonRequest, SimulationOut, SimulationRequest
from app.services import simulation

router = APIRouter(tags=["simulations"])

MSG03 = "Simulation complete – see the Feasibility Result below."


def to_out(sim: SimulationResult) -> SimulationOut:
    out = SimulationOut.model_validate(sim)
    if sim.feasibility:
        out.message = MSG03
    else:
        exceed = -sim.margin_wh
        out.message = f"Estimated energy exceeds the drone's battery capacity by {exceed:.1f} Wh."  # MSG07
    return out


def simulate(db, mission_id: int, drone_id: int, model_version_id: int, scenario_id: int | None = None):
    mission = get_or_404(db, Mission, mission_id)
    drone = get_or_404(db, Drone, drone_id)
    mv = get_or_404(db, ModelVersion, model_version_id)
    try:
        return to_out(simulation.run_simulation(db, mission, drone, mv, scenario_id))
    except simulation.SimulationInputError as exc:
        raise HTTPException(422, str(exc))


@router.post("/simulations", response_model=SimulationOut, status_code=201)
def run_simulation(body: SimulationRequest, db: DB):
    """UC-07 + UC-08."""
    return simulate(db, body.mission_id, body.drone_id, body.model_version_id)


@router.get("/simulations/{simulation_id}", response_model=SimulationOut)
def get_simulation(simulation_id: int, db: DB):
    return to_out(get_or_404(db, SimulationResult, simulation_id))


@router.post("/comparisons", response_model=ComparisonOut, status_code=201)
def compare_drones(body: ComparisonRequest, db: DB):
    """UC-09 — same mission, wind speed and model version across 2+ drones."""
    if len(set(body.drone_ids)) < 2:
        raise HTTPException(422, "Select at least two different drones to compare.")
    mission = get_or_404(db, Mission, body.mission_id)
    mv = get_or_404(db, ModelVersion, body.model_version_id)
    drones = [get_or_404(db, Drone, d) for d in dict.fromkeys(body.drone_ids)]
    try:
        comparison_id, sims = simulation.run_comparison(db, mission, drones, mv)
    except simulation.SimulationInputError as exc:
        raise HTTPException(422, str(exc))
    return ComparisonOut(comparison_id=comparison_id, results=[to_out(s) for s in sims])
