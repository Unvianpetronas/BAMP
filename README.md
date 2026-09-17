# BAMP — Battery-Aware Mission Planner

A standalone, offline decision-support web app for surveillance-drone mission planners. Before a drone
leaves the ground, BAMP predicts how much battery a planned mission will use — per flight leg and in
total — and tells the Operator whether the mission is feasible on the selected drone, using ML models
trained on real UAV flight telemetry rather than route-geometry guesswork.

> Capstone project, IS1904, FPT University. Full requirements live in `docs/reports/` (Report 1–3);
> this repo is the implementation. If code and report ever disagree, the report is the source of truth
> until someone updates both.

## What this is, in one paragraph

BAMP is a **public GitHub repo, not a hosted service**. An Operator clones it, runs
`docker compose up`, and gets a full local stack — Next.js frontend, FastAPI backend, PostgreSQL — with
zero cloud dependency. The only thing that ever leaves the machine is an optional call to an external AI
API to phrase a recommendation in natural language (Tier 2, has an offline fallback). Everything else —
predictions, model training, saved scenarios — stays local. See `docs/ARCHITECTURE.md` for why.

## Quick start

```bash
git clone <this-repo>
cd BAMP
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API docs (FastAPI auto-generated): http://localhost:8000/docs
- Postgres: localhost:5432 (credentials in `.env`)

First run also needs a migration:

```bash
docker compose exec backend alembic upgrade head
```

## Repo layout

```
BAMP/
├── backend/     FastAPI + SQLAlchemy + scikit-learn — see backend/README.md
├── frontend/    Next.js + TypeScript + Tailwind — see frontend/README.md
├── docs/        Architecture notes, decision log, pointers to the 3 Word reports
├── docker-compose.yml
└── CLAUDE.md    Project-specific instructions for Claude Code
```

Both `backend/` and `frontend/` exist and are wired into `docker-compose.yml` from day one, even though
**frontend implementation hasn't started yet** — right now it's routing/folder structure only, so the
shape of the app is visible before any UI is built. Backend has real (if incomplete) models, schemas,
and API stubs matching the SRS.

## Where the requirements actually live

This README won't repeat them. Instead of duplicating specs into code comments and letting the two
drift apart, we reference sections by number:

| Topic | Where |
|---|---|
| Full functional spec, ERD, business rules (BR-01–BR-11) | `docs/reports/Report3_SRS.docx`, §3–§5 |
| Feature list (FE-01–FE-09), limitations (LI-01–LI-08) | `docs/reports/Report1_Introduction.docx`, §6 |
| WBS, effort estimate, schedule | `docs/reports/Report2_Management_Plan.docx`, §1, §3 |
| Diagrams (editable) | `docs/reports/BAMP_Diagrams.drawio` |
| Standing decisions (Tier 1/Tier 2 calls, etc.) | `docs/DECISIONS.md` |

If you're implementing a function, find its BR-xx / UC-xx / FE-xx reference in the docstring and go read
that section before guessing at behavior.

## Current scope (Tier 1 committed / Tier 2 stretch)

**Tier 1 — committed for the MVP:**
Drone Management (predefined + custom), Mission Configuration (multi-leg), Wind Speed (one value per
mission — see `docs/DECISIONS.md`), Prediction (Linear Regression + Random Forest), Simulation &
Feasibility, Drone Comparison, Scenario save/reuse, Custom Model Training from an uploaded dataset
(FE-09 — no export, ever, see BR-11).

**Tier 2 — only if schedule allows:**
XGBoost + Gradient Boosting models, AI-generated natural-language explanation of the recommendation,
per-flight-leg wind speed override.

## Explicitly not in scope

No physical drone control, no live telemetry, no live weather API (wind speed is manual — "weather"
anywhere in this codebase means wind speed only), no mobile app, no automated drone selection, no
battery-degradation modelling, no model export. Full list with reasoning: Report 1 §6.2 (LI-01–LI-08).

## Contributing / working on this with Claude Code

Read `CLAUDE.md` first — it has the conventions, the naming map between SRS terms and code, and the
things that are easy to get subtly wrong (wind speed granularity, model immutability, the no-export
rule).
# BAMP
