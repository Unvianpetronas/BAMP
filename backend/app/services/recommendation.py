"""Model Recommendation Rule Engine (SRS §3.1.4 #3, UC-05) and explanation (UC-06).

The rule is deterministic ("Option A"). PLACEHOLDER RULE until the team's Report 3/4
cross-validation + significance-test results are encoded here:
  1. If a mission is given, prefer versions whose training range covers all its inputs (BR-03).
  2. Then lowest cross-validated RMSE.
  3. Tie-break: newest version id.
"""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models import Mission, ModelVersion, PredictionModel
from app.services.prediction import leg_features
from app.services.range_validator import check_ranges


class NoModelVersionError(LookupError):
    pass


class AIExplanationUnavailable(Exception):
    pass


@dataclass(frozen=True)
class Recommendation:
    model_version: ModelVersion
    covers_inputs: bool | None
    reason: dict[str, Any]


def _covers(mv: ModelVersion, mission: Mission) -> bool:
    checks = [
        {k: v for k, v in leg_features(leg, 0.0).items() if k != "wind_speed_ms"}
        for leg in mission.legs
    ]
    if mission.wind_speed is not None:
        checks.append({"wind_speed_ms": mission.wind_speed.wind_speed_ms})
    return not any(check_ranges(values, mv.feature_ranges) for values in checks)


def recommend(db: Session, mission: Mission | None = None) -> Recommendation:
    versions = db.scalars(
        select(ModelVersion)
        .join(PredictionModel)
        .where(PredictionModel.tier == 1)
        .options(selectinload(ModelVersion.prediction_model))
    ).all()
    if not versions:
        raise NoModelVersionError("No registered model version is available yet.")

    def key(mv: ModelVersion):
        covers = _covers(mv, mission) if mission is not None else True
        return (not covers, mv.metrics.get("cv_rmse", float("inf")), -mv.id)

    best = min(versions, key=key)
    covers = _covers(best, mission) if mission is not None else None
    return Recommendation(
        model_version=best,
        covers_inputs=covers,
        reason={
            "model": best.prediction_model.display_name,
            "version": best.version,
            "cv_rmse": best.metrics.get("cv_rmse"),
            "candidates": len(versions),
            "covers_inputs": covers,
        },
    )


def template_explanation(reason: dict[str, Any]) -> str:
    text = (
        f"{reason['model']} v{reason['version']} is recommended because it has the lowest "
        f"cross-validated RMSE ({reason['cv_rmse']:.3f} Wh) among {reason['candidates']} "
        "registered version(s)."
    )
    if reason["covers_inputs"] is True:
        text += " Its training data covers all of this mission's inputs."
    elif reason["covers_inputs"] is False:
        text += (
            " No registered version's training data covers all of this mission's inputs, "
            "so predictions will be flagged as reduced-confidence."
        )
    return text


class AIExplanationClient:
    """Tier 2 (UC-06) — the ONLY component allowed to make an outbound call (BR-08).

    Not implemented yet: always unavailable, so the template fallback is used (BR-07).
    """

    def explain(self, reason: dict[str, Any]) -> str:
        if not settings.AI_EXPLANATION_ENABLED:
            raise AIExplanationUnavailable("AI explanation is disabled.")
        raise AIExplanationUnavailable("AI explanation client is a Tier 2 extension (not built).")


MSG05 = "AI explanation unavailable – showing a standard explanation instead."


def explain(reason: dict[str, Any], client: AIExplanationClient) -> tuple[str, bool, str | None]:
    """Returns (text, used_ai, notice). Never raises (BR-07); never alters `reason` (BR-06)."""
    try:
        return client.explain(dict(reason)), True, None
    except Exception:
        return template_explanation(reason), False, MSG05
