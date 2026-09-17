import pytest

from app.core.config import settings
from app.services import feasibility


def test_br04_total_is_sum_of_legs():
    assert feasibility.total_energy([10.0, 20.5, 4.5]) == 35.0


@pytest.mark.parametrize(
    ("margin", "total", "capacity", "feasible"),
    [
        (0.15, 85.0, 100.0, True),  # exactly at the usable limit
        (0.15, 85.01, 100.0, False),
        (0.10, 90.0, 100.0, True),
        (0.10, 95.0, 100.0, False),  # below capacity, but inside the safety margin
    ],
)
def test_br05_feasibility_uses_safety_margin(monkeypatch, margin, total, capacity, feasible):
    monkeypatch.setattr(settings, "SAFETY_MARGIN", margin)
    result = feasibility.assess(total, capacity)
    assert result.feasible is feasible
    assert result.safety_margin == margin
    assert result.usable_capacity_wh == pytest.approx(capacity * (1 - margin))
    assert result.margin_wh == pytest.approx(capacity * (1 - margin) - total)
