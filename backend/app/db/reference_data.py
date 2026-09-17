"""Read-only reference data shipped with the app (seeded by the initial Alembic migration).

Predefined drones (SRS §3.2.1) cannot be edited or deleted from inside the app.
Specs are manufacturer-published figures — the team should verify them before the defense.
"""

PREDICTION_MODELS = [
    # BR-09: Tier 1 committed, Tier 2 only if schedule allows (not trainable yet, see ml/train.py).
    {"id": 1, "name": "linear_regression", "display_name": "Linear Regression", "tier": 1},
    {"id": 2, "name": "random_forest", "display_name": "Random Forest", "tier": 1},
]

PREDEFINED_DRONES = [
    # Platform of the CMU KiltHub dataset (TB47D battery, 99.9 Wh).
    {
        "id": 1,
        "name": "DJI Matrice 100",
        "type": "Quadcopter",
        "weight_kg": 2.355,
        "battery_capacity_wh": 99.9,
        "payload_capacity_kg": 1.0,
        "is_predefined": True,
    },
    # Two TB60 batteries, 274 Wh each.
    {
        "id": 2,
        "name": "DJI Matrice 300 RTK",
        "type": "Quadcopter",
        "weight_kg": 6.3,
        "battery_capacity_wh": 548.0,
        "payload_capacity_kg": 2.7,
        "is_predefined": True,
    },
]
