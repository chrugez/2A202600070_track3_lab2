from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypedDict


@dataclass(slots=True)
class ContextItem:
    source: str
    content: str
    priority: int
    relevance_score: float
    token_count: int
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentState(TypedDict, total=False):
    user_id: str
    session_id: str
    messages: list[dict[str, str]]
    user_query: str
    route_decision: dict[str, Any]
    retrieved_memories: dict[str, list[dict[str, Any]]]
    context_items: list[ContextItem]
    final_context: list[ContextItem]
    response: str
    memory_writes: list[dict[str, Any]]
    metrics: dict[str, Any]

