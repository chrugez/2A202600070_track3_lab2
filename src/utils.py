from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: object) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def append_jsonl(path: Path, payload: dict) -> None:
    ensure_parent(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, math.ceil(len(TOKEN_RE.findall(text)) * 1.3))


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    without_marks = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return without_marks.lower().replace("đ", "d")


def tokenize(text: str) -> list[str]:
    return [token for token in TOKEN_RE.findall(normalize_text(text))]


def overlap_score(query: str, text: str) -> float:
    q_tokens = set(tokenize(query))
    t_tokens = set(tokenize(text))
    if not q_tokens or not t_tokens:
        return 0.0
    return len(q_tokens & t_tokens) / len(q_tokens | t_tokens)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def stable_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def cosine_similarity(left: Iterable[float], right: Iterable[float]) -> float:
    left_list = list(left)
    right_list = list(right)
    dot = sum(a * b for a, b in zip(left_list, right_list))
    left_norm = math.sqrt(sum(a * a for a in left_list))
    right_norm = math.sqrt(sum(b * b for b in right_list))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


def hashed_embedding(text: str, dims: int = 64) -> list[float]:
    vector = [0.0] * dims
    for token in tokenize(text):
        digest = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        index = digest % dims
        vector[index] += 1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]
