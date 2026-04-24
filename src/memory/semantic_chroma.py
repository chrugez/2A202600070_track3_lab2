from __future__ import annotations

from pathlib import Path

from src.config import get_settings
from src.utils import append_jsonl, cosine_similarity, hashed_embedding, now_iso, read_jsonl, stable_hash

try:
    import chromadb
except ImportError:  # pragma: no cover
    chromadb = None


class SemanticMemory:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.local_path = Path(self.settings.memory_dir) / "semantic_store.jsonl"
        self._collection = None
        if self.settings.use_chroma and chromadb is not None:
            try:
                client = chromadb.PersistentClient(path=str(Path(self.settings.memory_dir) / "chroma"))
                self._collection = client.get_or_create_collection("semantic_memory")
            except Exception:
                self._collection = None

    def add_document(self, user_id: str, text: str, metadata: dict) -> None:
        payload = {
            "doc_id": metadata.get("doc_id") or stable_hash(f"{user_id}:{text}"),
            "user_id": user_id,
            "text": text,
            "metadata": {
                "created_at": now_iso(),
                **metadata,
            },
        }
        if self._collection is not None:
            self._collection.upsert(
                ids=[payload["doc_id"]],
                documents=[text],
                metadatas=[{"user_id": user_id, **payload["metadata"]}],
                embeddings=[hashed_embedding(text)],
            )
            return
        append_jsonl(self.local_path, payload)

    def search(self, user_id: str, query: str, limit: int = 5) -> list[dict]:
        if self._collection is not None:
            result = self._collection.query(
                query_embeddings=[hashed_embedding(query)],
                n_results=limit,
                where={"user_id": user_id},
            )
            documents = result.get("documents", [[]])[0]
            metadatas = result.get("metadatas", [[]])[0]
            distances = result.get("distances", [[]])[0] if result.get("distances") else [0.0] * len(documents)
            hits = []
            for doc, metadata, distance in zip(documents, metadatas, distances):
                hits.append(
                    {
                        "source": "semantic",
                        "content": doc,
                        "metadata": metadata,
                        "relevance_score": round(max(0.0, 1.0 - float(distance)), 3),
                        "confidence": 0.8,
                    }
                )
            return hits

        rows = [row for row in read_jsonl(self.local_path) if row.get("user_id") == user_id]
        query_embedding = hashed_embedding(query)
        hits: list[dict] = []
        for row in rows:
            score = cosine_similarity(query_embedding, hashed_embedding(row["text"]))
            if score > 0:
                hits.append(
                    {
                        "source": "semantic",
                        "content": row["text"],
                        "metadata": row.get("metadata", {}),
                        "relevance_score": round(score, 3),
                        "confidence": 0.75,
                    }
                )
        hits.sort(key=lambda item: item["relevance_score"], reverse=True)
        return hits[:limit]

