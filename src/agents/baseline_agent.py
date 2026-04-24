from __future__ import annotations

from src.memory.short_term import ShortTermMemory
from src.utils import normalize_text


class BaselineAgent:
    def __init__(self) -> None:
        self.sessions: dict[str, ShortTermMemory] = {}

    def run(self, user_id: str, session_id: str, user_query: str) -> dict:
        memory = self.sessions.setdefault(session_id, ShortTermMemory())
        memory.add_message("user", user_query)
        recent = memory.get_recent_context(400)
        answer = self._answer(user_query, recent)
        memory.add_message("assistant", answer)
        return {
            "response": answer,
            "route_decision": {"mode": "baseline", "reason": "Uses only current session context."},
            "retrieved_memories": {"short_term": recent, "preferences": [], "episodic": [], "semantic": []},
            "memory_writes": [],
            "metrics": {
                "token_breakdown": {"current_query": len(user_query.split()), "short_term": sum(len(item["content"].split()) for item in recent)},
                "context_utilization": 0.25 if recent else 0.0,
                "memory_required": False,
                "memory_hits": 0,
            },
        }

    def _answer(self, query: str, recent: list[dict]) -> str:
        lowered = normalize_text(query)
        if "framework" in lowered:
            return "Bạn có thể bắt đầu với FastAPI, Django, Node.js Express hoặc Spring tùy mục tiêu học backend."
        if "async" in lowered or "await" in lowered:
            return "Async/await giúp xử lý bất đồng bộ. `await` tạm dừng cho đến khi tác vụ hoàn thành."
        if "decorator" in lowered:
            return "Decorator là một kỹ thuật để bọc thêm hành vi quanh một hàm."
        if recent:
            return "Mình đang dựa vào đoạn hội thoại hiện tại để tiếp tục trả lời."
        return "Mình sẽ trả lời dựa trên câu hỏi hiện tại."
