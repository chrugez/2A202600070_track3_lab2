from src.memory.router import MemoryRouter


def test_router_recommendation_pref_and_semantic():
    router = MemoryRouter()
    result = router.route("Tôi nên học framework nào tiếp theo?", [])
    assert result["use_preferences"] is True
    assert result["use_semantic"] is True


def test_router_episode_recall():
    router = MemoryRouter()
    result = router.route("Lần trước tôi bị rối async, giải thích lại giúp tôi.", [])
    assert result["use_episodic"] is True
    assert result["use_semantic"] is True
