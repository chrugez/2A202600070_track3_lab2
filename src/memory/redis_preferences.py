from __future__ import annotations

from pathlib import Path
from typing import Any

from src.config import get_settings
from src.utils import normalize_text, now_iso, overlap_score, read_json, stable_hash, write_json

try:
    import redis
except ImportError:  # pragma: no cover
    redis = None


class RedisPreferenceMemory:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.local_path = Path(self.settings.memory_dir) / "preferences_store.json"
        self._redis = None
        if self.settings.use_redis and redis is not None:
            try:
                client = redis.Redis.from_url(self.settings.redis_url, decode_responses=True)
                client.ping()
                self._redis = client
            except Exception:
                self._redis = None

    def _load_local(self) -> dict[str, Any]:
        return read_json(self.local_path, {})  # type: ignore[return-value]

    def _write_local(self, data: dict[str, Any]) -> None:
        write_json(self.local_path, data)

    def get_preferences(self, user_id: str) -> dict:
        if self._redis:
            key = f"user:{user_id}:preferences"
            payload = self._redis.get(key)
            return {} if not payload else __import__("json").loads(payload)
        return self._load_local().get(user_id, {})

    def upsert_preference(self, user_id: str, key: str, value: dict) -> None:
        preferences = self.get_preferences(user_id)
        existing = preferences.get(key, {})
        merged = {
            **existing,
            **value,
            "key": key,
            "updated_at": now_iso(),
            "memory_id": existing.get("memory_id") or stable_hash(f"{user_id}:{key}"),
            "stale": False,
        }
        preferences[key] = merged
        if self._redis:
            redis_key = f"user:{user_id}:preferences"
            self._redis.set(redis_key, __import__("json").dumps(preferences, ensure_ascii=False))
            return
        all_users = self._load_local()
        all_users[user_id] = preferences
        self._write_local(all_users)

    def search_preferences(self, user_id: str, query: str) -> list[dict]:
        preferences = self.get_preferences(user_id)
        recommendation_query = any(
            phrase in normalize_text(query)
            for phrase in ["nen hoc", "goi y", "phu hop", "framework", "tong hop", "nhac lai", "di ung", "automation"]
        )
        results: list[dict] = []
        for key, value in preferences.items():
            text = f"{key} {value}"
            score = overlap_score(query, text)
            if score > 0 or any(word in normalize_text(text) for word in normalize_text(query).split()) or recommendation_query:
                results.append(
                    {
                        "source": "preferences",
                        "key": key,
                        "value": value,
                        "content": f"{key}: {value}",
                        "relevance_score": round(score + (0.35 if recommendation_query else 0.25), 3),
                        "confidence": value.get("confidence", 0.8),
                    }
                )
        results.sort(key=lambda item: item["relevance_score"], reverse=True)
        return results
