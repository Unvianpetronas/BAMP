import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.config import settings
from app.db.reference_data import PREDEFINED_DRONES, PREDICTION_MODELS
from app.db.session import Base, get_db
from app.main import app as fastapi_app
from app.ml import train as ml_train
from app.models import Drone, Mission, MissionLeg, PredictionModel, WindSpeedCondition
from app.services.model_registry import load_artifact, register_version


def synthetic_legs(n: int = 60, seed: int = 0) -> pd.DataFrame:
    """TEST FIXTURE ONLY — not real telemetry. Ranges are what the BR-03 tests rely on."""
    rng = np.random.default_rng(seed)
    df = pd.DataFrame(
        {
            "duration_min": rng.uniform(1, 30, n),
            "altitude_m": rng.uniform(10, 120, n),
            "distance_km": rng.uniform(0.1, 10, n),
            "payload_kg": rng.uniform(0.1, 1.0, n),
            "wind_speed_ms": rng.uniform(0, 10, n),
        }
    )
    df["energy_wh"] = (
        2.0 * df.duration_min + 0.05 * df.altitude_m + 1.5 * df.distance_km
        + 8.0 * df.payload_kg + 0.7 * df.wind_speed_ms + rng.normal(0, 0.5, n)
    )
    return df


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "ARTIFACT_DIR", tmp_path / "artifacts")
    load_artifact.cache_clear()
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    event.listen(engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = Session()
    session.add_all(PredictionModel(**m) for m in PREDICTION_MODELS)
    session.add_all(Drone(**d) for d in PREDEFINED_DRONES)
    session.commit()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def client(db):
    fastapi_app.dependency_overrides[get_db] = lambda: db
    yield TestClient(fastapi_app)
    fastapi_app.dependency_overrides.clear()


def make_version(db, model_name="linear_regression", df=None, source="team"):
    estimator, metrics, ranges, hp = ml_train.train(
        synthetic_legs() if df is None else df, model_name
    )
    return register_version(
        db,
        model_name=model_name,
        estimator=estimator,
        dataset_source=source,
        dataset_name="synthetic-test",
        feature_ranges=ranges,
        hyperparameters=hp,
        metrics=metrics,
    )


@pytest.fixture
def team_version(db):
    return make_version(db)


def make_mission(db, legs, wind=5.0):
    mission = Mission(
        name="Patrol",
        legs=[MissionLeg(position=i, **leg) for i, leg in enumerate(legs, 1)],
        wind_speed=WindSpeedCondition(wind_speed_ms=wind) if wind is not None else None,
    )
    db.add(mission)
    db.commit()
    return mission


IN_RANGE_LEG = {"duration_min": 10, "altitude_m": 50, "distance_km": 3, "payload_kg": 0.5}


@pytest.fixture
def mission(db):
    return make_mission(db, [IN_RANGE_LEG, {**IN_RANGE_LEG, "duration_min": 20}])
