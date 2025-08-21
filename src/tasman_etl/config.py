"""Environment configuration (production-ready, minimal).

Loads a local ``.env`` once (dotenv) and exposes helpers for code needing
configuration. A small cached ``Settings`` shim is retained for backwards
compat / DI convenience (dropped easily later).
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from dotenv import find_dotenv, load_dotenv

_DEFAULT_DB_URL = "postgresql://postgres:localpw@localhost:5432/usajobs"
_ENV_LOADED = False


def load_env(path: str = ".env", *, override: bool = False) -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    # If explicit path missing, attempt discovery (walk upwards) for flexibility.
    if not os.path.exists(path):  # pragma: no cover - defensive
        discovered = find_dotenv(usecwd=True)
        if discovered:
            path = discovered
    load_dotenv(path, override=override)
    _ENV_LOADED = True


def env(key: str, default: Any | None = None) -> Any:
    load_env()
    return os.getenv(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    val = env(key)
    if val is None:
        return default
    return str(val).lower() in {"1", "true", "yes", "on"}


def db_url() -> str:
    url = env("DB_URL", _DEFAULT_DB_URL)
    if url.startswith("postgresql+psycopg://"):
        url = url.replace("postgresql+psycopg://", "postgresql://", 1)
    return url


class Settings:  # pragma: no cover - compatibility shim
    def __init__(self) -> None:
        load_env()
        self.dq_enforce: bool = env_bool("DQ_ENFORCE", True)
        self.db_url: str = db_url()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Eager load: ensures simple scripts that import deep modules still have env.
load_env()
