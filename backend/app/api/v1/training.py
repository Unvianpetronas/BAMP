"""UC-12 / FE-09 Custom Model Training (Tier 1) — see docs/DECISIONS.md.

The result is versioned exactly like a team model (BR-02, BR-10). There is no export (BR-11).
"""

import io
import json
from typing import Annotated, Literal

import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.api.deps import DB
from app.ml import train as ml_train
from app.schemas.model import ModelVersionOut
from app.services.model_registry import register_version

router = APIRouter(prefix="/training", tags=["training"])


@router.post("", response_model=ModelVersionOut, status_code=201)
def train_custom_model(
    db: DB,
    file: Annotated[UploadFile, File(description="CSV, one row per flight leg")],
    model_name: Annotated[Literal["linear_regression", "random_forest"], Form()],
    dataset_name: Annotated[str, Form(min_length=1, max_length=200)],
    hyperparameters: Annotated[str, Form(description="JSON object")] = "{}",
):
    try:
        hp = json.loads(hyperparameters)
        if not isinstance(hp, dict):
            raise ValueError
    except ValueError:
        raise HTTPException(422, "hyperparameters must be a JSON object.")
    try:
        df = pd.read_csv(io.BytesIO(file.file.read()))
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as exc:
        raise HTTPException(422, f"Could not read CSV: {exc}")

    try:
        estimator, metrics, ranges, hp_used = ml_train.train(df, model_name, hp)
    except ValueError as exc:
        raise HTTPException(422, str(exc))

    return register_version(
        db,
        model_name=model_name,
        estimator=estimator,
        dataset_source="custom-uploaded",
        dataset_name=dataset_name,
        feature_ranges=ranges,
        hyperparameters=hp_used,
        metrics=metrics,
    )
