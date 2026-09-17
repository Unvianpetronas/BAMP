import pytest

from app.core.config import settings
from app.services import recommendation
from tests.conftest import IN_RANGE_LEG, make_mission, make_version, synthetic_legs


def test_no_versions_raises(db):
    with pytest.raises(recommendation.NoModelVersionError):
        recommendation.recommend(db)


def test_picks_lowest_cv_rmse(db):
    versions = [make_version(db, "linear_regression"), make_version(db, "random_forest")]
    best = min(versions, key=lambda v: v.metrics["cv_rmse"])
    rec = recommendation.recommend(db)
    assert rec.model_version.id == best.id
    assert rec.covers_inputs is None


def test_prefers_version_whose_training_range_covers_the_mission(db):
    covering = make_version(db, "linear_regression")
    # Narrow training range (altitude 10-120 → only low-altitude rows) but typically lower error.
    narrow = synthetic_legs(200, seed=1)
    narrow = narrow[narrow.altitude_m < 30]
    make_version(db, "random_forest", df=narrow)

    mission = make_mission(db, [{**IN_RANGE_LEG, "altitude_m": 100}])
    rec = recommendation.recommend(db, mission)
    assert rec.model_version.id == covering.id
    assert rec.covers_inputs is True


def test_reports_when_nothing_covers_the_mission(db, team_version):
    mission = make_mission(db, [IN_RANGE_LEG], wind=50.0)
    rec = recommendation.recommend(db, mission)
    assert rec.covers_inputs is False
    assert "reduced-confidence" in recommendation.template_explanation(rec.reason)


class _BrokenClient:
    def explain(self, reason):
        raise ConnectionError("API unreachable")


class _MeddlingClient:
    def explain(self, reason):
        reason["model"] = "Something Else"
        return "AI text"


def test_br07_unreachable_ai_falls_back_to_template(db, team_version):
    rec = recommendation.recommend(db)
    text, used_ai, notice = recommendation.explain(rec.reason, _BrokenClient())
    assert used_ai is False
    assert notice == recommendation.MSG05
    assert "Linear Regression v1" in text


def test_br07_default_client_is_offline_safe(db, team_version, monkeypatch):
    rec = recommendation.recommend(db)
    for enabled in (False, True):
        monkeypatch.setattr(settings, "AI_EXPLANATION_ENABLED", enabled)
        _, used_ai, _ = recommendation.explain(rec.reason, recommendation.AIExplanationClient())
        assert used_ai is False


def test_br06_ai_cannot_alter_the_decision(db, team_version):
    rec = recommendation.recommend(db)
    before = dict(rec.reason)
    text, used_ai, _ = recommendation.explain(rec.reason, _MeddlingClient())
    assert (text, used_ai) == ("AI text", True)
    assert rec.reason == before
    assert rec.model_version.id == team_version.id
