from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env_path(name: str, default: str) -> Path:
    return Path(os.environ.get(name, default)).expanduser().resolve()


@dataclass(frozen=True)
class Settings:
    data_dir: Path = _env_path("MEMORY_DATA_DIR", "/data")
    db_path: Path = _env_path("MEMORY_DB_PATH", "/data/memory.db")
    raw_dir: Path = _env_path("MEMORY_RAW_DIR", "/data/raw")
    derived_dir: Path = _env_path("MEMORY_DERIVED_DIR", "/data/derived")
    index_path: Path = _env_path("MEMORY_INDEX_PATH", "/data/derived/index.json")
    api_bind: str = os.environ.get("MEMORY_API_BIND", "0.0.0.0:8081")
    worker_poll_seconds: float = float(os.environ.get("MEMORY_WORKER_POLL_SECONDS", "1.0"))
    embedding_backend: str = os.environ.get("MEMORY_EMBEDDING_BACKEND", "hash")
    embedding_model: str = os.environ.get(
        "MEMORY_EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2",
    )
    max_chunk_chars: int = int(os.environ.get("MEMORY_MAX_CHUNK_CHARS", "900"))
    max_search_results: int = int(os.environ.get("MEMORY_MAX_SEARCH_RESULTS", "10"))


def load_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.raw_dir.mkdir(parents=True, exist_ok=True)
    settings.derived_dir.mkdir(parents=True, exist_ok=True)
    settings.index_path.parent.mkdir(parents=True, exist_ok=True)
    return settings

