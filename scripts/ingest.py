from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import load_settings
from src.foundry_rag import FoundryRAGClient


STATE_FILE = ROOT / ".rag_resources.json"
KB_DIR = ROOT / "data" / "knowledge_base"


def main() -> None:
    settings = load_settings()
    client = FoundryRAGClient(
        settings.project_endpoint,
        settings.model_deployment_name,
    )

    files = sorted(KB_DIR.glob("*.md"))
    if not files:
        raise RuntimeError(f"No knowledge-base files found in {KB_DIR}")

    print(f"Uploading {len(files)} knowledge-base documents...")
    vector_store_id = client.create_vector_store(files)
    print(f"Vector store created: {vector_store_id}")

    agent = client.create_agent(vector_store_id)
    print(f"Agent created: {agent.name} (version {agent.version})")

    state = {
        "agent_name": agent.name,
        "agent_version": agent.version,
        "vector_store_id": vector_store_id,
        "model_deployment_name": settings.model_deployment_name,
        "documents": [path.name for path in files],
    }
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"Saved local resource state to {STATE_FILE.name}")
    print("Run: streamlit run app.py")


if __name__ == "__main__":
    main()
