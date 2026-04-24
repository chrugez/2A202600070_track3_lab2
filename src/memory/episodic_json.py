from __future__ import annotations

from pathlib import Path

from src.config import get_settings
from src.utils import append_jsonl, now_iso, overlap_score, read_jsonl, stable_hash


class EpisodicMemory:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.path = Path(self.settings.memory_dir) / "episodic_log.jsonl"

    def add_episode(self, episode: dict) -> None:
        payload = {
            "episode_id": episode.get("episode_id") or stable_hash(
                f"{episode.get('user_id')}:{episode.get('session_id')}:{episode.get('event')}"
            ),
            "timestamp": episode.get("timestamp") or now_iso(),
            "importance": episode.get("importance", 0.7),
            **episode,
        }
        append_jsonl(self.path, payload)

    def search_episodes(self, user_id: str, query: str, limit: int = 5) -> list[dict]:
        episodes = [row for row in read_jsonl(self.path) if row.get("user_id") == user_id]
        scored: list[dict] = []
        for episode in episodes:
            tags = " ".join(episode.get("tags", []))
            text = f"{episode.get('event', '')} {episode.get('context', '')} {tags}"
            score = overlap_score(query, text) + float(episode.get("importance", 0.0)) * 0.3
            if score > 0:
                scored.append(
                    {
                        **episode,
                        "source": "episodic",
                        "content": episode.get("event", ""),
                        "relevance_score": round(score, 3),
                        "confidence": min(1.0, score),
                    }
                )
        scored.sort(key=lambda item: item["relevance_score"], reverse=True)
        return scored[:limit]

