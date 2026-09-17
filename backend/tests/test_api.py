import io

from app.main import app
from tests.conftest import IN_RANGE_LEG, synthetic_legs

API = "/api/v1"
DRONE = {"name": "X", "type": "Quad", "weight_kg": 1.2, "battery_capacity_wh": 80, "payload_capacity_kg": 0.5}
MISSION = {"name": "Patrol", "legs": [IN_RANGE_LEG], "wind_speed_ms": 4}


def test_drone_crud_and_predefined_read_only(client):
    assert [d["name"] for d in client.get(f"{API}/drones").json()][:2] == [
        "DJI Matrice 100",
        "DJI Matrice 300 RTK",
    ]
    assert client.put(f"{API}/drones/1", json=DRONE).status_code == 403
    assert client.delete(f"{API}/drones/1").status_code == 403

    created = client.post(f"{API}/drones", json=DRONE).json()
    assert created["is_predefined"] is False
    updated = client.put(f"{API}/drones/{created['id']}", json={**DRONE, "name": "Y"}).json()
    assert updated["name"] == "Y"
    assert client.delete(f"{API}/drones/{created['id']}").status_code == 204
    assert client.get(f"{API}/drones/{created['id']}").status_code == 404


def test_drone_numeric_fields_must_be_positive(client):
    assert client.post(f"{API}/drones", json={**DRONE, "weight_kg": 0}).status_code == 422


def test_br01_mission_needs_a_leg(client):
    assert client.post(f"{API}/missions", json={**MISSION, "legs": []}).status_code == 422


def test_mission_wind_speed_is_per_mission(client):
    m = client.post(f"{API}/missions", json={**MISSION, "legs": [IN_RANGE_LEG] * 2}).json()
    assert m["wind_speed_ms"] == 4
    assert all("wind_speed_ms" not in leg for leg in m["legs"])

    edited = client.put(f"{API}/missions/{m['id']}", json={**MISSION, "wind_speed_ms": 7}).json()
    assert edited["wind_speed_ms"] == 7 and len(edited["legs"]) == 1
    assert len(client.get(f"{API}/missions").json()) == 1
    assert client.delete(f"{API}/missions/{m['id']}").status_code == 204


def test_simulation_comparison_and_scenario_flow(client, team_version):
    mission = client.post(f"{API}/missions", json=MISSION).json()
    body = {"mission_id": mission["id"], "drone_id": 1, "model_version_id": team_version.id}

    sim = client.post(f"{API}/simulations", json=body)
    assert sim.status_code == 201
    sim = sim.json()
    assert sim["model_version"]["id"] == team_version.id  # BR-02
    assert "cv_rmse" in sim["model_version"]["metrics"]
    assert client.get(f"{API}/simulations/{sim['id']}").json()["total_energy_wh"] == sim["total_energy_wh"]

    comp = client.post(
        f"{API}/comparisons",
        json={"mission_id": mission["id"], "drone_ids": [1, 2], "model_version_id": team_version.id},
    )
    assert comp.status_code == 201 and len(comp.json()["results"]) == 2
    same = client.post(
        f"{API}/comparisons",
        json={"mission_id": mission["id"], "drone_ids": [1, 1], "model_version_id": team_version.id},
    )
    assert same.status_code == 422

    scenario = client.post(f"{API}/scenarios", json={"name": "S1", **body}).json()
    renamed = client.put(f"{API}/scenarios/{scenario['id']}", json={"name": "S2", **body}).json()
    assert renamed["name"] == "S2"
    assert [s["id"] for s in client.get(f"{API}/scenarios").json()] == [scenario["id"]]
    run = client.post(f"{API}/scenarios/{scenario['id']}/run").json()
    assert run["scenario_id"] == scenario["id"]

    # A mission referenced by a saved scenario cannot be deleted out from under it.
    assert client.delete(f"{API}/missions/{mission['id']}").status_code == 409
    assert client.delete(f"{API}/scenarios/{scenario['id']}").status_code == 204
    assert client.get(f"{API}/scenarios/{scenario['id']}").status_code == 404


def test_infeasible_simulation_reports_msg07(client, team_version):
    tiny = client.post(f"{API}/drones", json={**DRONE, "battery_capacity_wh": 1}).json()
    mission = client.post(f"{API}/missions", json=MISSION).json()
    sim = client.post(
        f"{API}/simulations",
        json={"mission_id": mission["id"], "drone_id": tiny["id"], "model_version_id": team_version.id},
    ).json()
    assert sim["feasibility"] is False
    assert sim["message"].startswith("Estimated energy exceeds")


def test_simulation_unknown_references_404(client, team_version):
    body = {"mission_id": 999, "drone_id": 1, "model_version_id": team_version.id}
    assert client.post(f"{API}/simulations", json=body).status_code == 404


def test_models_list_and_recommendation(client):
    assert client.get(f"{API}/models/recommendation").status_code == 404  # nothing registered yet
    models = client.get(f"{API}/models").json()
    assert [(m["name"], m["tier"]) for m in models] == [("linear_regression", 1), ("random_forest", 1)]


def test_recommendation_uses_template_offline(client, team_version):
    mission = client.post(f"{API}/missions", json=MISSION).json()
    rec = client.get(f"{API}/models/recommendation", params={"mission_id": mission["id"]}).json()
    assert rec["model_version"]["id"] == team_version.id
    assert rec["ai_generated"] is False and rec["notice"]  # BR-07
    assert rec["covers_inputs"] is True


def test_br02_no_update_route_for_model_versions(client, team_version):
    url = f"{API}/models/versions/{team_version.id}"
    assert client.get(url).status_code == 200
    for method in ("put", "patch", "delete"):
        assert getattr(client, method)(url).status_code == 405


def test_br11_no_artifact_download_or_export_route(client, team_version):
    paths = [r.path.lower() for r in app.routes]
    assert not any(w in p for p in paths for w in ("download", "export", "artifact"))
    assert client.get(f"{API}/models/versions/{team_version.id}/download").status_code == 404
    assert "artifact_path" not in client.get(f"{API}/models/versions/{team_version.id}").json()


def _csv(df):
    return {"file": ("legs.csv", io.BytesIO(df.to_csv(index=False).encode()), "text/csv")}


def test_br10_custom_training_creates_custom_uploaded_version(client, team_version):
    resp = client.post(
        f"{API}/training",
        files=_csv(synthetic_legs(seed=3)),
        data={"model_name": "random_forest", "dataset_name": "my flights", "hyperparameters": '{"n_estimators": 20}'},
    )
    assert resp.status_code == 201, resp.text
    mv = resp.json()
    assert mv["dataset_source"] == "custom-uploaded"
    assert mv["hyperparameters"]["n_estimators"] == 20
    assert client.get(f"{API}/models").json()[1]["versions"][0]["id"] == mv["id"]


def test_custom_training_rejects_bad_input(client):
    data = {"model_name": "linear_regression", "dataset_name": "d"}
    bad_cols = synthetic_legs().drop(columns="energy_wh")
    assert client.post(f"{API}/training", files=_csv(bad_cols), data=data).status_code == 422
    assert client.post(
        f"{API}/training", files=_csv(synthetic_legs()), data={**data, "hyperparameters": "[1]"}
    ).status_code == 422
    empty = {"file": ("e.csv", io.BytesIO(b""), "text/csv")}
    assert client.post(f"{API}/training", files=empty, data=data).status_code == 422
    xgb = {**data, "model_name": "xgboost"}
    assert client.post(f"{API}/training", files=_csv(synthetic_legs()), data=xgb).status_code == 422
