# CLAUDE.md — instructions for Claude Code working on BAMP

Read this before writing code. It exists so you don't have to re-derive decisions that were already
made (and sometimes reversed) across three reports and a lot of back-and-forth. When this file and the
Word reports disagree, the reports win — but update this file to match rather than silently picking one.

## What you're building

Battery-Aware Mission Planner: predicts drone mission energy consumption from drone + mission + wind
speed inputs, using models trained on real flight telemetry, and reports Feasible/Not Feasible against
the drone's battery capacity. Full spec: `docs/reports/Report3_SRS.docx`.

## Stack (fixed — do not substitute)

- **Frontend:** Next.js (App Router), TypeScript, Tailwind CSS, Recharts for charts
- **Backend:** FastAPI, Python, Pydantic v2
- **Database:** PostgreSQL, SQLAlchemy (ORM), Alembic (migrations)
- **ML:** scikit-learn, joblib for artifact persistence
- **Local dev/deploy:** Docker Compose only — this is not a cloud-hosted app, see `docs/ARCHITECTURE.md`

## Non-negotiable business rules

These are load-bearing. Getting one wrong isn't a style nit, it contradicts the SRS. Full list in
Report 3 §5.1 (BR-01–BR-11); the ones that trip people up:

- **BR-02 — model versions are immutable.** Never add an UPDATE endpoint/method for `ModelVersion`.
  Once created (team-trained or custom-trained), a version's dataset/hyperparameters/metrics are frozen.
  If something's wrong with a version, register a new one — don't mutate.
- **BR-03 — out-of-range is a warning, not a block.** If a drone/mission/wind-speed parameter is outside
  the training data's range, flag it (`reduced_confidence: true` or similar) and still return a
  prediction. Never silently clamp or reject.
- **BR-05 — feasibility margin is a named constant, not a magic number.** `total_energy_wh <=
  battery_capacity_wh * (1 - SAFETY_MARGIN)`. Keep `SAFETY_MARGIN` in one place (`core/config.py`), not
  hardcoded per call site. The actual value is still TBC with the supervisor — see `docs/DECISIONS.md`.
- **BR-08 — core functionality is 100% offline.** Drone Management, Mission Configuration, Prediction,
  Simulation, Feasibility must never make an outbound network call. Only the AI Explanation Client
  (Tier 2) touches the internet, and it must degrade gracefully (BR-07) when unreachable — never raise
  an unhandled exception that breaks the Model Recommendation feature.
- **BR-10 / BR-11 — custom training, never export.** An Operator can upload a dataset and train a model
  (FE-09 / UC-12); the result is versioned exactly like a team-trained model (same immutability, same
  table). There is **no download/export endpoint for model artifacts, ever** — not for team models, not
  for custom-trained ones. If you're tempted to add `GET /models/{id}/download`, don't; that's BR-11.

## Wind speed: per-mission, not per-leg (read this before touching `MissionLeg`)

This flip-flopped during design. **Current, final answer: Tier 1 is one wind-speed value per mission**
(`WindSpeedCondition` has a `mission_id` FK, not a `leg_id` FK). A Tier 2 extension may let the Operator
override it per leg — if you're asked to build that, it means re-pointing `WindSpeedCondition` at
`MissionLeg` instead, which is a schema change, not just a UI change. Don't build per-leg wind speed
unless explicitly asked; the SRS (§3.3.2) and ERD (§3.1.5) both currently say per-mission.

Also: **"weather" never means real weather.** No rain, temperature, or visibility anywhere in this
codebase. If a variable, table, or endpoint needs a name for "environmental condition," call it
`wind_speed`, not `weather`.

## Naming map: SRS term → code

| SRS / ERD term | Code identifier |
|---|---|
| Operator | the only user role; no auth/role system in Tier 1 |
| WindSpeedCondition | `WindSpeedCondition` model, `wind_speed_ms` field |
| ModelVersion.dataset_source | `"team"` or `"custom-uploaded"` (BR-10) |
| Feasible / Not Feasible | boolean or enum on `SimulationResult.feasibility`, not a free string |
| Tier 1 / Tier 2 | a `tier: Literal[1, 2]` marker in `PredictionModel`, not a separate table |

Full entity list and attributes: Report 3 §3.1.5 (ERD) and `docs/reports/BAMP_Diagrams.drawio`, tab 4.

## API shape

Routers live in `backend/app/api/v1/`, one file per resource, mounted in `router.py`. Each stub's
docstring names the UC-xx it implements — read that use case in the SRS before filling in the body.
Don't invent new top-level resources without checking whether they map to an existing entity first.

## Testing expectations (Report 2 §1.2 — these are targets, not decorations)

- Unit tests (pytest): ≥ 80% coverage on `services/` (the actual prediction/feasibility logic), not on
  routers or models.
- Every Business Rule above should have at least one test that would fail if the rule were violated —
  e.g., a test that asserts a second write to an existing `ModelVersion` is rejected (BR-02).

## What NOT to build yet

- No frontend UI implementation — routes/folders exist (`frontend/src/app/*`) but pages are placeholders.
  Don't fill them in unless asked; the backend and schema need to stabilize first.
- No live weather API integration, no mobile app, no automated drone selection, no battery-degradation
  modelling, no drone hardware/telemetry integration. Full reasoning: Report 1 §6.2 (LI-01–LI-08).
- No export/download for models (see BR-11 above — worth repeating, it's the one people forget).

## Before you open a PR

1. Does it violate anything above? (grep this file for the entity/endpoint you touched)
2. Did you add a test that pins the business rule you relied on?
3. Does `docker compose up` still bring up all three services clean?
