from __future__ import annotations

from src.utils import estimate_tokens, normalize_text


def keyword_score(response: str, expected_keywords: list[str]) -> float:
    lowered = normalize_text(response)
    hits = sum(1 for keyword in expected_keywords if normalize_text(keyword) in lowered)
    return hits / max(1, len(expected_keywords))


def relevance_rating(score: float) -> float:
    return round(1 + score * 4, 2)


def satisfaction_rating(score: float) -> float:
    return round(1 + score * 4, 2)


def tokens_per_successful_answer(results: list[dict]) -> float:
    successful = [row for row in results if row["pass"]]
    total_tokens = sum(row["estimated_tokens"] for row in results)
    return round(total_tokens / max(1, len(successful)), 2)


def estimate_response_tokens(response: str) -> int:
    return estimate_tokens(response)
