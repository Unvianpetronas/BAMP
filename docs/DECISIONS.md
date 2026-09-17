# Decision log

Short-form record of decisions that took real discussion to reach, so nobody re-litigates them from
scratch or silently reverses one while fixing something unrelated. Newest first. Each entry says what
was decided, why, and what it touches in code.

---

### Open items from the initial backend implementation — 2026-09-17

Provisional choices made in code so it could run end to end. Each needs confirmation (supervisor or team).

- **SAFETY_MARGIN = 0.15** (`core/config.py`, overridable via `.env`). SRS §3.5.2 says "provisionally
  10–15%"; 0.15 is the conservative end. MSG07's "exceeds by {x} Wh" is measured against the *usable*
  capacity (after the margin).
- **Recommendation rule is a placeholder** (`services/recommendation.py`): prefer versions whose training
  range covers the mission, then lowest `cv_rmse`, then newest. Replace with the rule derived from the
  team's CV + significance-test results.
- **Feature set** (`ml/features.py`): one training row per leg with `duration_min, altitude_m,
  distance_km, payload_kg, wind_speed_ms → energy_wh`. Drone specs are not model features (the KiltHub
  data is a single platform), so BR-03 range checks currently cover leg + wind inputs only, not drone
  specs.
- **Predefined drones** (`db/reference_data.py`): DJI Matrice 100 and Matrice 300 RTK with
  manufacturer figures — verify before the defense.
- **AI Explanation Client** (Tier 2) is an always-unavailable stub, so the template fallback (BR-07) is
  what users see.
- **Word reports vs. these notes:** the `.docx` files in `docs/reports/` predate FE-09/BR-10/BR-11 and
  still say `WeatherCondition`. Code follows this log and `CLAUDE.md`; update the reports to match.

---

### Wind speed is per-mission (Tier 1), per-leg is Tier 2 — 2026-09-15

**Decision:** One wind-speed value applies to the whole mission. `WindSpeedCondition.mission_id`, not
`leg_id`.

**Why:** The team voted. Two options were live: (A) one value per mission — simpler UI, matches the
original wireframe; (B) one value per leg — more realistic for long missions crossing different
conditions, but changes the ERD and the Flight Leg Editor form. The team picked A for Tier 1 and parked
B as a Tier 2 extension (same field, same validation pattern, just re-pointed at `MissionLeg` — not a
redesign).

**Touches:** `models/wind_speed_condition.py` (FK target), `schemas/mission.py`, the Mission
Configuration screen, SRS §3.3.2, ERD §3.1.5.

**If you're asked to build per-leg wind speed:** re-read this entry first. It's a schema migration
(`mission_id` → `leg_id` on `WindSpeedCondition`), not a frontend-only change.

---

### No model export, ever — decided alongside FE-09 (custom training)

**Decision:** BR-11. Neither team-trained nor Operator-trained models can be downloaded/exported from
the app.

**Why:** Keeps the "everything stays local" claim (BR-08) honest even for models an Operator trained
themselves — otherwise "no export" would only apply to the team's models, which is an inconsistent
rule that's easy to get wrong later. Also sidesteps a whole class of questions about model licensing/
liability that weren't in scope to answer.

**Touches:** No `GET /models/{id}/download` route exists or should be added. `services/model_registry.py`
only ever writes to `ml/artifacts/`, never serves the file back out.

---

### Custom model training (FE-09 / UC-12) is Tier 1, not Tier 2

**Decision:** An Operator can upload a private flight dataset and train a model inside the app. This is
committed scope, not a stretch goal — unlike XGBoost/Gradient Boosting (which *are* Tier 2).

**Why:** Directly answers the biggest weakness of the approach (CMU KiltHub dataset is only 209 flights,
one drone platform — Risk #1 in Report 2). Rather than claiming the small dataset is "fixed," this gives
the Operator a way to opt into their own data instead, with the same transparency rule (BR-03
out-of-range warning) applied to their upload. Framed as "BAMP is a prediction *platform*, not a single
frozen model" — not as a claim that dataset size stopped being a limitation.

**Touches:** `api/v1/training.py`, `services/model_registry.py`, `ml/train.py`, WBS item 4.4 in
Report 2 (10 man-days, Complex).

---

### Distribution model: public GitHub repo + Docker Compose, not a hosted service

**Decision:** No cloud deployment. Operator clones the repo and runs everything locally.

**Why:** Keeps "offline-first" (BR-08) true by construction rather than by policy — there's no server to
accidentally depend on. Trade-off acknowledged explicitly (see `docs/ARCHITECTURE.md` and SRS §4.2.4):
this isn't realistic yet for a non-technical field Operator, only for the MVP/defense stage. Near-term
mitigation (setup script) and long-term mitigation (packaged installer) are both documented, not just
promised verbally.

**Touches:** `docker-compose.yml`, root `README.md`, SRS §4.2.4.

---

### Quality targets: numbers instead of TBD — 2026-09-16

**Decision:** Report 2 §1.2 test-coverage/defect targets are concrete proposed numbers (e.g., Unit Test
≥80% coverage, ≤5 open defects) instead of "TBD after WP4."

**Why:** A capstone document with TBD in front of a supervisor invites "so you haven't thought about
this yet" — a number the team can revise later is a stronger starting position than a placeholder.

**Touches:** Report 2 only, no code impact yet — but when CI/test tooling is set up, wire the coverage
gate to the 80% figure here rather than picking a new number ad hoc.
