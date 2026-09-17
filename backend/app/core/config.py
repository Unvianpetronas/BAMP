from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://bamp:bamp@localhost:5432/bamp"

    # BR-05: a mission is Feasible iff total_energy_wh <= battery_capacity_wh * (1 - SAFETY_MARGIN).
    # SRS §3.5.2 says "provisionally 10-15%"; 0.15 is the conservative end. TBC with supervisor —
    # see docs/DECISIONS.md. Do not hardcode this anywhere else.
    SAFETY_MARGIN: float = Field(default=0.15, ge=0, lt=1)

    # Local Model Registry. Artifacts are written here and never served back out (BR-11).
    ARTIFACT_DIR: Path = Path(__file__).resolve().parent.parent / "ml" / "artifacts"

    # Tier 2 AI explanation (UC-06). When off, the template fallback is used (BR-07).
    AI_EXPLANATION_ENABLED: bool = False


settings = Settings()
