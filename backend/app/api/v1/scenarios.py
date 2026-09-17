"""UC-10 Manage Scenario (Save / Reuse) (SRS §3.7)."""

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DB, get_or_404
from app.api.v1.simulations import simulate
from app.models import Drone, Mission, ModelVersion, Scenario
from app.schemas.scenario import ScenarioIn, ScenarioOut
from app.schemas.simulation import SimulationOut

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


def _check_refs(db, body: ScenarioIn) -> None:
    get_or_404(db, Drone, body.drone_id)
    get_or_404(db, Mission, body.mission_id)
    get_or_404(db, ModelVersion, body.model_version_id)


@router.get("", response_model=list[ScenarioOut])
def list_scenarios(db: DB):
    return db.scalars(select(Scenario).order_by(Scenario.created_at.desc())).all()


@router.get("/{scenario_id}", response_model=ScenarioOut)
def get_scenario(scenario_id: int, db: DB):
    """Loading a scenario pre-fills Mission Configuration (SRS §3.7.1)."""
    return get_or_404(db, Scenario, scenario_id)


@router.post("", response_model=ScenarioOut, status_code=201)
def create_scenario(body: ScenarioIn, db: DB):
    """MSG04 on success: Scenario "{name}" saved successfully."""
    _check_refs(db, body)
    scenario = Scenario(**body.model_dump())
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.put("/{scenario_id}", response_model=ScenarioOut)
def update_scenario(scenario_id: int, body: ScenarioIn, db: DB):
    """Rename, or re-point the scenario at another drone / model version."""
    scenario = get_or_404(db, Scenario, scenario_id)
    _check_refs(db, body)
    for k, v in body.model_dump().items():
        setattr(scenario, k, v)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.delete("/{scenario_id}", status_code=204)
def delete_scenario(scenario_id: int, db: DB):
    db.delete(get_or_404(db, Scenario, scenario_id))
    db.commit()


@router.post("/{scenario_id}/run", response_model=SimulationOut, status_code=201)
def run_scenario(scenario_id: int, db: DB):
    """UC-11 — re-run after what-if edits to the scenario's mission."""
    s = get_or_404(db, Scenario, scenario_id)
    return simulate(db, s.mission_id, s.drone_id, s.model_version_id, scenario_id=s.id)
