from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.benchmark.dataset import build_dataset
from src.benchmark.evaluator import evaluate_dataset
from src.config import get_settings
from src.utils import ensure_parent


def render_report(results: dict) -> str:
    aggregate = results["aggregate"]
    baseline = aggregate["baseline"]
    memory = aggregate["memory"]
    lines = [
        "# Benchmark Report - Lab 17 Multi-Memory Agent",
        "",
        "## Setup",
        "",
        "- Baseline: agent without persistent memory.",
        "- Memory agent: LangGraph workflow with short-term, preference, episodic, and semantic memory.",
        "- Dataset: 10 scripted multi-turn conversations.",
        "",
        "## Aggregate Results",
        "",
        "| Metric | Baseline | Memory Agent |",
        "|---|---:|---:|",
        f"| Response relevance | {baseline['response_relevance']}/5 | {memory['response_relevance']}/5 |",
        f"| User satisfaction | {baseline['user_satisfaction']}/5 | {memory['user_satisfaction']}/5 |",
        f"| Memory hit rate | {baseline['memory_hit_rate']} | {memory['memory_hit_rate']} |",
        f"| Context utilization | {baseline['context_utilization']} | {memory['context_utilization']} |",
        f"| Tokens per successful answer | {baseline['tokens_per_successful_answer']} | {memory['tokens_per_successful_answer']} |",
        "",
        "## Conversation Results",
        "",
        "| # | Scenario | No-memory result | With-memory result | Pass? |",
        "|---|---|---|---|---|",
    ]
    baseline_rows = {row["id"]: row for row in results["variants"]["baseline"]}
    memory_rows = {row["id"]: row for row in results["variants"]["memory"]}
    for identifier in sorted(memory_rows):
        base = baseline_rows[identifier]
        mem = memory_rows[identifier]
        lines.append(
            f"| {identifier} | {mem['scenario']} | {base['response']} | {mem['response']} | {'Pass' if mem['pass'] else 'Fail'} |"
        )
    lines.extend(
        [
            "",
            "## Token Budget Breakdown - Memory Agent",
            "",
            "| Source | Tokens | Percentage |",
            "|---|---:|---:|",
        ]
    )
    for source, payload in memory["token_budget_breakdown"].items():
        lines.append(f"| {source} | {payload['tokens']} | {payload['percentage']}% |")
    lines.extend(
        [
            "",
            "## Reflection",
            "",
            "- Preference memory gives the most visible personalization gain in recommendation tasks.",
            "- Episodic memory is the riskiest if retrieved incorrectly because it can overfit a stale learning issue.",
            "- Deletion must clear Redis or fallback preference storage, the JSON episodic log, and the Chroma or fallback semantic store.",
            "- Privacy risk: stable preferences and allergy-like profile facts can become sensitive if stored without consent and TTL.",
            "- Scaling limitation: rule-based routing and local token estimation are explainable, but weaker than model-based retrieval planning.",
        ]
    )
    return "\n".join(lines)


def reset_benchmark_memory(base_dir: Path) -> None:
    memory_dir = base_dir / "memory"
    for path in (
        memory_dir / "preferences_store.json",
        memory_dir / "episodic_log.jsonl",
        memory_dir / "semantic_store.jsonl",
    ):
        if path.exists():
            if path.suffix == ".json":
                path.write_text("{}", encoding="utf-8")
            else:
                path.write_text("", encoding="utf-8")
    chroma_dir = memory_dir / "chroma"
    if chroma_dir.exists():
        shutil.rmtree(chroma_dir)


def main() -> None:
    settings = get_settings()
    reset_benchmark_memory(Path(settings.base_dir))
    results = evaluate_dataset(build_dataset())
    reports_dir = Path(settings.reports_dir)
    report_path = reports_dir / "benchmark_report.md"
    results_path = reports_dir / "results.json"
    root_benchmark_path = Path(settings.base_dir) / "BENCHMARK.md"
    report_text = render_report(results)
    ensure_parent(report_path)
    report_path.write_text(report_text, encoding="utf-8")
    results_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    root_benchmark_path.write_text(report_text, encoding="utf-8")
    print(f"Wrote {report_path}")
    print(f"Wrote {results_path}")
    print(f"Wrote {root_benchmark_path}")


if __name__ == "__main__":
    main()
