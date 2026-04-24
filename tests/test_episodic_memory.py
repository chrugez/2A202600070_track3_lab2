from src.memory.episodic_json import EpisodicMemory


def test_episode_search_returns_relevant_match():
    memory = EpisodicMemory()
    memory.add_episode(
        {
            "user_id": "test_user_ep",
            "session_id": "session_1",
            "event": "User was confused about Python async await",
            "context": "await does not block the whole program",
            "tags": ["python", "async"],
            "importance": 0.8,
        }
    )
    results = memory.search_episodes("test_user_ep", "async await block", limit=3)
    assert results
    assert "async" in results[0]["content"].lower()

