import socket

import pandas as pd
import pytest

from app.models import ComparisonResult, Drone
from app.services import simulation
from app.services.model_registry import load_artifact
from tests.conftest import IN_RANGE_LEG, make_mission


@pytest.fixture
def drone(db):
    return db.get(Drone, 1)


def test_simulation_per_leg_total_and_traceability(db, mission, drone, team_version):
    sim = simulation.run_simulation(db, mission, drone, team_version)
    assert [r["position"] for r in sim.leg_results] == [1, 2]
    assert sim.total_energy_wh == pytest.approx(sum(r["energy_wh"] for r in sim.leg_results))  # BR-04
    assert sim.model_version_id == team_version.id  # BR-02
    assert sim.reduced_confidence is False and sim.warnings == []


def test_br01_mission_without_legs_is_rejected(db, drone, team_version):
    empty = make_mission(db, [])
    with pytest.raises(simulation.SimulationInputError, match="at least one flight leg"):
        simulation.run_simulation(db, empty, drone, team_version)


def test_mission_without_wind_speed_is_rejected(db, drone, team_version):
    no_wind = make_mission(db, [IN_RANGE_LEG], wind=None)
    with pytest.raises(simulation.SimulationInputError, match="wind speed"):
        simulation.run_simulation(db, no_wind, drone, team_version)


def test_br03_out_of_range_warns_but_still_predicts_unclamped(db, drone, team_version):
    far_leg = {**IN_RANGE_LEG, "altitude_m": 900}
    mission = make_mission(db, [far_leg], wind=25.0)
    sim = simulation.run_simulation(db, mission, drone, team_version)

    assert sim.reduced_confidence is True
    assert {(w["field"], w["leg_position"]) for w in sim.warnings} == {
        ("altitude_m", 1),
        ("wind_speed_ms", None),
    }
    # The prediction used the raw inputs, not values clamped to the training range.
    est = load_artifact(team_version.artifact_path)
    raw = est.predict(pd.DataFrame([{**far_leg, "wind_speed_ms": 25.0}]))[0]
    assert sim.total_energy_wh == pytest.approx(raw)


def test_infeasible_when_drone_battery_too_small(db, mission, team_version):
    tiny = Drone(name="Tiny", type="Quad", weight_kg=0.2, battery_capacity_wh=1.0, payload_capacity_kg=0.1)
    db.add(tiny)
    db.commit()
    sim = simulation.run_simulation(db, mission, tiny, team_version)
    assert sim.feasibility is False
    assert sim.margin_wh < 0


def test_br08_simulation_works_with_network_disabled(db, mission, drone, team_version, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("core functionality attempted a network call (BR-08)")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setattr(socket, "create_connection", no_network)
    sim = simulation.run_simulation(db, mission, drone, team_version)
    assert sim.id is not None


def test_comparison_runs_same_mission_for_each_drone(db, mission, team_version):
    drones = [db.get(Drone, 1), db.get(Drone, 2)]
    comparison_id, sims = simulation.run_comparison(db, mission, drones, team_version)

    assert [s.drone_id for s in sims] == [1, 2]
    assert len({s.total_energy_wh for s in sims}) == 1  # same mission + model → same energy
    assert {s.model_version_id for s in sims} == {team_version.id}
    rows = db.query(ComparisonResult).filter_by(comparison_id=comparison_id).all()
    assert {r.simulation_result_id for r in rows} == {s.id for s in sims}
