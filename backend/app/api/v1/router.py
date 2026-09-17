from fastapi import APIRouter

from app.api.v1 import drones, missions, models, scenarios, simulations, training

api_router = APIRouter(prefix="/api/v1")
for module in (drones, missions, models, simulations, scenarios, training):
    api_router.include_router(module.router)
