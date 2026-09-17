from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.models import ModelVersionImmutableError
from app.services import model_registry
from tests.conftest import make_version


def test_br02_existing_model_version_cannot_be_updated(db, team_version):
    team_version.metrics = {"cv_rmse": 0.0}
    with pytest.raises(ModelVersionImmutableError):
        db.commit()
    db.rollback()
    db.refresh(team_version)
    assert team_version.metrics["cv_rmse"] != 0.0


def test_versions_are_appended_not_overwritten(db):
    v1 = make_version(db)
    v2 = make_version(db)
    assert (v1.version, v2.version) == (1, 2)
    assert v1.artifact_path != v2.artifact_path
    assert Path(v1.artifact_path).exists() and Path(v2.artifact_path).exists()


def test_artifacts_stay_inside_local_registry(db, team_version):
    assert Path(team_version.artifact_path).is_relative_to(settings.ARTIFACT_DIR)


def test_br10_custom_versions_share_the_same_table_and_numbering(db):
    team = make_version(db, source="team")
    custom = make_version(db, source="custom-uploaded")
    assert custom.version == team.version + 1
    assert custom.dataset_source == "custom-uploaded"


def test_unknown_dataset_source_rejected_and_artifact_cleaned_up(db):
    with pytest.raises(IntegrityError):
        make_version(db, source="internet")
    assert not any(Path(settings.ARTIFACT_DIR).rglob("*.joblib"))


def test_unknown_model_name(db):
    with pytest.raises(model_registry.ModelNotFoundError):
        model_registry.get_prediction_model(db, "xgboost")


def test_br11_registry_exposes_no_export_function():
    names = [n.lower() for n in dir(model_registry)]
    assert not any(word in n for n in names for word in ("download", "export", "serve"))
