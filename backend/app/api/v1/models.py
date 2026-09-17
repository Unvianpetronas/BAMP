"""UC-04 Select Prediction Model & Version, UC-05/UC-06 Recommendation (SRS §3.4).

Read-only by design: no update route (BR-02) and no artifact download/export route (BR-11).
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DB, get_or_404
from app.models import Mission, ModelVersion, PredictionModel
from app.schemas.model import ModelVersionOut, PredictionModelOut, RecommendationOut
from app.services import recommendation

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=list[PredictionModelOut])
def list_models(db: DB):
    """UC-04 — model types with their registered, immutable versions."""
    return db.scalars(
        select(PredictionModel)
        .options(selectinload(PredictionModel.versions))
        .order_by(PredictionModel.tier, PredictionModel.id)
    ).all()


@router.get("/versions/{version_id}", response_model=ModelVersionOut)
def get_version(version_id: int, db: DB):
    return get_or_404(db, ModelVersion, version_id)


@router.get("/recommendation", response_model=RecommendationOut)
def get_recommendation(db: DB, mission_id: int | None = None):
    """UC-05 (rule-based decision) + UC-06 (explanation, template fallback per BR-07)."""
    mission = get_or_404(db, Mission, mission_id) if mission_id is not None else None
    try:
        rec = recommendation.recommend(db, mission)
    except recommendation.NoModelVersionError as exc:
        raise HTTPException(404, str(exc))
    text, used_ai, notice = recommendation.explain(rec.reason, recommendation.AIExplanationClient())
    return RecommendationOut(
        model_version=rec.model_version,
        model_display_name=rec.model_version.prediction_model.display_name,
        covers_inputs=rec.covers_inputs,
        explanation=text,
        ai_generated=used_ai,
        notice=notice,
    )
