"""Feature contract shared by training (ml/train.py) and inference (services/prediction.py).

One training row = one flight leg. Wind speed is per mission in Tier 1, so every leg of a mission
gets the same wind_speed_ms value at inference time.
"""

FEATURES = ["duration_min", "altitude_m", "distance_km", "payload_kg", "wind_speed_ms"]
TARGET = "energy_wh"
