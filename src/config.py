from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    project_endpoint: str
    model_deployment_name: str


def load_settings() -> Settings:
    load_dotenv()

    endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "").strip()
    model = os.getenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "").strip()

    missing = []
    if not endpoint:
        missing.append("FOUNDRY_PROJECT_ENDPOINT")
    if not model:
        missing.append("FOUNDRY_MODEL_DEPLOYMENT_NAME")

    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
        )

    return Settings(
        project_endpoint=endpoint,
        model_deployment_name=model,
    )
