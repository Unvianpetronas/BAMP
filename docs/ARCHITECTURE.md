# Architecture

## The one-sentence version

Three containers (`frontend`, `backend`, `db`) wired together by `docker-compose.yml`, running entirely
on the Operator's own machine. No cloud deployment target exists or is planned for Tier 1.

## Why "clone a repo" instead of a normal installer

This was a defense question worth documenting. The honest answer: at MVP/proof-of-concept stage,
`git clone` + `docker compose up` is the cheapest way to get a reproducible full-stack environment
running, and the target user for the capstone deliverable is the supervisor/evaluator, not yet a
field-deployed non-technical Operator. That gap is real and we're not pretending otherwise:

- **Near-term (Tier 2, cheap):** a `.bat` (Windows) / `.sh` (macOS/Linux) script that wraps the clone +
  compose steps so the Operator double-clicks instead of typing commands. Still needs Docker Desktop
  installed first.
- **Longer-term (post-capstone):** a packaged installer that bundles its own runtime, so the Operator
  never has to know Docker exists. Not attempted here — it's a different distribution model, not an
  incremental change to this one.

Source: Report 3 SRS §4.2.4 (Portability), added after supervisor feedback on defense-readiness.

## Data flow (matches Report 3 Figure 1, Context Diagram)

```
Operator (browser)
      │
      ▼
frontend (Next.js, :3000)
      │  REST/JSON
      ▼
backend (FastAPI, :8000)
      │              │
      ▼              ▼
db (Postgres)   ml/artifacts/ (joblib files, local disk — the "Local Model Registry")
      │
      ▼ (optional, Tier 2 only)
AI Explanation Service (external API) — only call in the whole system that leaves the machine
```

## Why one Postgres instance and not "no database, just files"

The original proposal language ("standalone, offline") was sometimes misread as "no server component."
That's wrong — BAMP runs a real local server stack (FastAPI + Postgres via Docker Compose); "offline"
means no *cloud/hosted* dependency, not no server at all. See SRS §4.2.2 (Reliability) for the exact
wording that was corrected after this ambiguity got flagged.

## Model storage

Trained model artifacts (`.joblib` files) live under `backend/app/ml/artifacts/`, gitignored. The
`ModelVersion` table stores metadata (dataset source, hyperparameters, eval metrics) and a path/key
pointing at the artifact file — not the artifact itself. This applies identically to team-trained and
Operator-trained (custom) models; see BR-10/BR-11 in `CLAUDE.md`.

## Entity relationships

See `docs/reports/BAMP_Diagrams.drawio` (tab 4, ERD) for the diagram, and Report 3 §3.1.5 for the
authoritative entity descriptions. Backend models in `backend/app/models/` are a 1:1 mirror — if you
add a field to the ERD, add it to the SQLAlchemy model and vice versa; they should never drift.
