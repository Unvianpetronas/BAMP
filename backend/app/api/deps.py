from typing import Annotated, TypeVar

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db

DB = Annotated[Session, Depends(get_db)]

T = TypeVar("T")


def get_or_404(db: Session, model: type[T], id_: int) -> T:
    obj = db.get(model, id_)
    if obj is None:
        raise HTTPException(404, f"{model.__name__} {id_} not found.")
    return obj
