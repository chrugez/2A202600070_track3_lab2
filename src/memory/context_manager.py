from __future__ import annotations

from src.types import ContextItem


class ContextWindowManager:
    def build_context(self, items: list[ContextItem], max_tokens: int) -> list[ContextItem]:
        ordered = sorted(items, key=lambda item: (item.priority, -item.relevance_score, item.token_count))
        selected: list[ContextItem] = []
        spent = 0
        for item in ordered:
            if selected and spent + item.token_count > max_tokens:
                continue
            selected.append(item)
            spent += item.token_count
        return selected

