from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    base_dir: Path
    memory_dir: Path
    reports_dir: Path
    openai_api_key: str
    openai_model: str
    redis_url: str
    use_redis: bool
    use_chroma: bool
    max_context_tokens: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv()
    base_dir = Path(__file__).resolve().parent.parent
    memory_dir = base_dir / os.getenv("MEMORY_DIR", "memory")
    reports_dir = base_dir / os.getenv("REPORTS_DIR", "reports")
    return Settings(
        base_dir=base_dir,
        memory_dir=memory_dir,
        reports_dir=reports_dir,
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        use_redis=os.getenv("USE_REDIS", "false").lower() == "true",
        use_chroma=os.getenv("USE_CHROMA", "false").lower() == "true",
        max_context_tokens=int(os.getenv("DEFAULT_MAX_CONTEXT_TOKENS", "1400")),
    )

