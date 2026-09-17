"""Out-of-Range Validator (SRS §3.1.4 #5, BR-03).

Out-of-range is a WARNING, never a block and never a clamp: callers still predict with the
original value and mark the result reduced-confidence.
"""

from typing import Any

MSG02 = "This value is outside the range seen in the training data; the prediction may be less reliable."


def check_ranges(
    values: dict[str, float],
    feature_ranges: dict[str, dict[str, float]],
    leg_position: int | None = None,
) -> list[dict[str, Any]]:
    warnings = []
    for field, value in values.items():
        rng = feature_ranges.get(field)
        if rng is None or rng["min"] <= value <= rng["max"]:
            continue
        warnings.append(
            {
                "code": "MSG02",
                "field": field,
                "leg_position": leg_position,
                "value": value,
                "min": rng["min"],
                "max": rng["max"],
                "message": MSG02,
            }
        )
    return warnings
