"""UC-01 Select or Define Drone (SRS §3.2)."""

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import DB, get_or_404
from app.models import Drone
from app.schemas.drone import DroneIn, DroneOut

router = APIRouter(prefix="/drones", tags=["drones"])


def _custom_or_403(db, drone_id: int) -> Drone:
    drone = get_or_404(db, Drone, drone_id)
    if drone.is_predefined:
        raise HTTPException(403, "Predefined drones are read-only (SRS §3.2.1).")
    return drone


@router.get("", response_model=list[DroneOut])
def list_drones(db: DB):
    """UC-01 — predefined first, then custom."""
    return db.scalars(select(Drone).order_by(Drone.is_predefined.desc(), Drone.id)).all()


@router.get("/{drone_id}", response_model=DroneOut)
def get_drone(drone_id: int, db: DB):
    return get_or_404(db, Drone, drone_id)


@router.post("", response_model=DroneOut, status_code=201)
def create_drone(body: DroneIn, db: DB):
    """UC-01 — define a custom drone."""
    drone = Drone(**body.model_dump(), is_predefined=False)
    db.add(drone)
    db.commit()
    db.refresh(drone)
    return drone


@router.put("/{drone_id}", response_model=DroneOut)
def update_drone(drone_id: int, body: DroneIn, db: DB):
    """Custom drones can be edited in later scenarios (SRS §3.2.2)."""
    drone = _custom_or_403(db, drone_id)
    for k, v in body.model_dump().items():
        setattr(drone, k, v)
    db.commit()
    db.refresh(drone)
    return drone


@router.delete("/{drone_id}", status_code=204)
def delete_drone(drone_id: int, db: DB):
    drone = _custom_or_403(db, drone_id)
    db.delete(drone)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Drone is used by a saved scenario; delete the scenario first.")
