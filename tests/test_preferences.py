from src.memory.redis_preferences import RedisPreferenceMemory


def test_preference_upsert_overwrites_conflict():
    memory = RedisPreferenceMemory()
    user_id = "test_user_pref"
    memory.upsert_preference(user_id, "allergy", {"allergy": "sua bo", "confidence": 0.9})
    memory.upsert_preference(user_id, "allergy", {"allergy": "dau nanh", "confidence": 0.98})
    preferences = memory.get_preferences(user_id)
    assert preferences["allergy"]["allergy"] == "dau nanh"

