from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import load_settings
from src.foundry_rag import FoundryRAGClient


STATE_FILE = ROOT / ".rag_resources.json"
CASES_FILE = ROOT / "eval" / "test_cases.json"
RESULTS_FILE = ROOT / "eval" / "results.json"


def contains_all(text: str, terms: list[str]) -> bool:
    lowered = text.lower()
    return all(term.lower() in lowered for term in terms)


def contains_none(text: str, terms: list[str]) -> bool:
    lowered = text.lower()
    return all(term.lower() not in lowered for term in terms)


def main() -> None:
    if not STATE_FILE.exists():
        raise RuntimeError("Run 'python scripts/ingest.py' before evaluation.")

    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    settings = load_settings()
    client = FoundryRAGClient(
        settings.project_endpoint,
        settings.model_deployment_name,
    )

    results = []

    for case in cases:
        start = time.perf_counter()
        answer, _ = client.ask(
            agent_name=state["agent_name"],
            question=case["question"],
            conversation_id=None,
        )
        latency = time.perf_counter() - start

        required_ok = contains_all(answer, case.get("required_terms", []))
        forbidden_ok = contains_none(answer, case.get("forbidden_terms", []))
        passed = required_ok and forbidden_ok

        results.append(
            {
                "id": case["id"],
                "question": case["question"],
                "answer": answer,
                "passed": passed,
                "required_terms_ok": required_ok,
                "forbidden_terms_ok": forbidden_ok,
                "latency_seconds": round(latency, 3),
            }
        )

        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {case['id']} ({latency:.2f}s)")

    pass_rate = sum(item["passed"] for item in results) / len(results)
    latencies = [item["latency_seconds"] for item in results]

    summary = {
        "cases": len(results),
        "passed": sum(item["passed"] for item in results),
        "pass_rate": round(pass_rate, 4),
        "average_latency_seconds": round(statistics.mean(latencies), 3),
        "results": results,
    }

    RESULTS_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\nEvaluation summary")
    print(f"Pass rate: {summary['pass_rate'] * 100:.1f}%")
    print(f"Average latency: {summary['average_latency_seconds']:.2f}s")
    print(f"Saved: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
