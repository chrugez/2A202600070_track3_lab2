from src.memory.context_manager import ContextWindowManager
from src.types import ContextItem


def test_context_manager_preserves_high_priority_items():
    manager = ContextWindowManager()
    items = [
        ContextItem("current_query", "query", 1, 1.0, 10, {}),
        ContextItem("preferences", "pref", 2, 0.9, 20, {}),
        ContextItem("short_term", "recent", 3, 0.2, 40, {}),
    ]
    selected = manager.build_context(items, 30)
    assert [item.source for item in selected] == ["current_query", "preferences"]
