from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import load_settings
from src.foundry_rag import FoundryRAGClient


STATE_FILE = ROOT / ".rag_resources.json"


def main() -> None:
    if not STATE_FILE.exists():
        print("No .rag_resources.json file found. Nothing to clean up.")
        return

    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    settings = load_settings()
    client = FoundryRAGClient(
        settings.project_endpoint,
        settings.model_deployment_name,
    )

    client.delete_agent_version(state["agent_name"], state["agent_version"])
    client.delete_vector_store(state["vector_store_id"])
    STATE_FILE.unlink()

    print("Deleted the agent version and vector store.")


if __name__ == "__main__":
    main()
