from __future__ import annotations

from statistics import mean

from src.app_service import AgentService
from src.benchmark.metrics import (
    estimate_response_tokens,
    keyword_score,
    relevance_rating,
    satisfaction_rating,
    tokens_per_successful_answer,
)


def evaluate_dataset(dataset: list[dict]) -> dict:
    service = AgentService()
    variants = {"baseline": [], "memory": []}
    for mode in variants:
        for conversation in dataset:
            user_id = f"user_{conversation['id']:03d}"
            final_result = None
            for session_index, session_turns in enumerate(conversation["sessions"], start=1):
                session_id = f"session_{session_index}"
                for turn in session_turns:
                    final_result = service.run_agent_turn(user_id, session_id, turn, mode)
            assert final_result is not None
            match_score = keyword_score(final_result["response"], conversation["expected_keywords"])
            variants[mode].append(
                {
                    "id": conversation["id"],
                    "scenario": conversation["scenario"],
                    "response": final_result["response"],
                    "match_score": round(match_score, 3),
                    "relevance": relevance_rating(match_score),
                    "satisfaction": satisfaction_rating(match_score),
                    "pass": match_score >= 0.5,
                    "estimated_tokens": estimate_response_tokens(final_result["response"]),
                    "metrics": final_result["metrics"],
                }
            )
    return summarize_results(variants)


def summarize_results(variants: dict[str, list[dict]]) -> dict:
    summary = {"variants": variants, "aggregate": {}}
    for mode, rows in variants.items():
        memory_queries = [row for row in rows if row["metrics"].get("memory_required")]
        memory_hit_rate = (
            sum(1 for row in memory_queries if row["metrics"].get("memory_hits", 0) > 0) / len(memory_queries)
            if memory_queries
            else 0.0
        )
        token_breakdown: dict[str, int] = {}
        for row in rows:
            for source, tokens in row["metrics"].get("token_breakdown", {}).items():
                token_breakdown[source] = token_breakdown.get(source, 0) + tokens
        total_tokens = sum(token_breakdown.values()) or 1
        summary["aggregate"][mode] = {
            "response_relevance": round(mean(row["relevance"] for row in rows), 2),
            "user_satisfaction": round(mean(row["satisfaction"] for row in rows), 2),
            "memory_hit_rate": round(memory_hit_rate, 2),
            "context_utilization": round(mean(row["metrics"].get("context_utilization", 0.0) for row in rows), 2),
            "tokens_per_successful_answer": tokens_per_successful_answer(rows),
            "token_budget_breakdown": {
                source: {"tokens": tokens, "percentage": round(tokens / total_tokens * 100, 2)}
                for source, tokens in sorted(token_breakdown.items())
            },
        }
    return summary

