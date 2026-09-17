# BAMP backend

FastAPI + SQLAlchemy + Alembic + scikit-learn. API docs: http://localhost:8000/docs

```
app/
├── api/v1/      one router per resource (drones, missions, models, simulations, scenarios, training)
├── core/        settings — SAFETY_MARGIN (BR-05) lives here and only here
├── db/          engine/session, read-only reference data (predefined drones, model types)
├── models/      SQLAlchemy mirror of the ERD (SRS §3.1.5)
├── schemas/     Pydantic v2 request/response models
├── services/    prediction, feasibility, simulation, range check, registry, recommendation
└── ml/          feature contract + training (artifacts/ is local-only, never exported — BR-11)
```

## Common commands (from the repo root)

```bash
docker compose exec backend alembic upgrade head          # apply migrations
docker compose exec backend pytest                        # tests + ≥80% coverage gate on services/
docker compose exec backend alembic revision --autogenerate -m "..."   # after changing a model
```

## Registering a team model

No model ships with the repo — the Prediction feature needs at least one registered version.
Put the curated dataset (one row per flight leg; columns `duration_min, altitude_m, distance_km,
payload_kg, wind_speed_ms, energy_wh`) somewhere under `backend/app/` so the container can see it, then:

```bash
docker compose exec backend python -m app.ml.train \
    --csv app/data/kilthub_legs.csv --model random_forest --dataset-name "CMU KiltHub"
```

Operators can do the same from the app via `POST /api/v1/training` (FE-09); the result is a
`custom-uploaded` version in the same table.
