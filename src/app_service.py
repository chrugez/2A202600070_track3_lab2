from __future__ import annotations

from src.agents.baseline_agent import BaselineAgent
from src.agents.memory_agent import MemoryAgent


class AgentService:
    def __init__(self) -> None:
        self.baseline = BaselineAgent()
        self.memory = MemoryAgent()

    def run_agent_turn(self, user_id: str, session_id: str, user_query: str, mode: str = "memory") -> dict:
        if mode == "baseline":
            return self.baseline.run(user_id, session_id, user_query)
        return self.memory.run(user_id, session_id, user_query)

