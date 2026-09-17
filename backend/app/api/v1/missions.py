"""UC-02 Configure Mission, UC-03 Specify Wind Speed, UC-11 What-if (SRS §3.3)."""

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import DB, get_or_404
from app.models import Mission, MissionLeg, WindSpeedCondition
from app.schemas.mission import MissionIn, MissionOut

router = APIRouter(prefix="/missions", tags=["missions"])


def to_out(mission: Mission) -> MissionOut:
    return MissionOut(
        id=mission.id,
        name=mission.name,
        legs=mission.legs,
        wind_speed_ms=mission.wind_speed.wind_speed_ms if mission.wind_speed else None,
        created_at=mission.created_at,
    )


def _apply(mission: Mission, body: MissionIn) -> None:
    mission.name = body.name
    mission.legs = [MissionLeg(position=i, **leg.model_dump()) for i, leg in enumerate(body.legs, 1)]
    if mission.wind_speed is None:
        mission.wind_speed = WindSpeedCondition(wind_speed_ms=body.wind_speed_ms)
    else:
        mission.wind_speed.wind_speed_ms = body.wind_speed_ms


@router.get("", response_model=list[MissionOut])
def list_missions(db: DB):
    return [to_out(m) for m in db.scalars(select(Mission).order_by(Mission.id)).all()]


@router.get("/{mission_id}", response_model=MissionOut)
def get_mission(mission_id: int, db: DB):
    return to_out(get_or_404(db, Mission, mission_id))


@router.post("", response_model=MissionOut, status_code=201)
def create_mission(body: MissionIn, db: DB):
    """UC-02 + UC-03 — legs and the single mission-level wind speed."""
    mission = Mission()
    _apply(mission, body)
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return to_out(mission)


@router.put("/{mission_id}", response_model=MissionOut)
def update_mission(mission_id: int, body: MissionIn, db: DB):
    """UC-11 — edit payload/altitude/wind speed and re-run without rebuilding the scenario."""
    mission = get_or_404(db, Mission, mission_id)
    _apply(mission, body)
    db.commit()
    db.refresh(mission)
    return to_out(mission)


@router.delete("/{mission_id}", status_code=204)
def delete_mission(mission_id: int, db: DB):
    db.delete(get_or_404(db, Mission, mission_id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Mission is used by a saved scenario; delete the scenario first.")
