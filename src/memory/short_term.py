from __future__ import annotations

from dataclasses import dataclass, field

from src.utils import estimate_tokens


@dataclass
class ShortTermMemory:
    max_messages: int = 12
    messages: list[dict[str, str]] = field(default_factory=list)

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

    def get_recent_context(self, max_tokens: int) -> list[dict[str, str]]:
        selected: list[dict[str, str]] = []
        running_tokens = 0
        for message in reversed(self.messages):
            message_tokens = estimate_tokens(message["content"])
            if selected and running_tokens + message_tokens > max_tokens:
                break
            selected.append(message)
            running_tokens += message_tokens
        return list(reversed(selected))

    def trim(self, max_tokens: int) -> None:
        self.messages = self.get_recent_context(max_tokens)

