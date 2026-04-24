from __future__ import annotations

from src.graph import AgentGraph
from src.memory.short_term import ShortTermMemory
from src.types import AgentState


class MemoryAgent:
    def __init__(self) -> None:
        self.graph = AgentGraph()
        self.sessions: dict[str, ShortTermMemory] = {}

    def run(self, user_id: str, session_id: str, user_query: str) -> dict:
        short_term = self.sessions.setdefault(session_id, ShortTermMemory())
        short_term.add_message("user", user_query)
        state: AgentState = {
            "user_id": user_id,
            "session_id": session_id,
            "messages": short_term.messages.copy(),
            "user_query": user_query,
        }
        result = self.graph.run(state)
        short_term.messages = result["messages"]
        return result

