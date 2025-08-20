"""
A database engine for connecting to the PostgreSQL database.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import psycopg
from psycopg import conninfo

# Default for local dev / docker-compose
_DEFAULT_DB_URL = "postgresql://postgres:localpw@localhost:5432/usajobs"


def _load_db_url() -> str:
    """
    Resolve the database URL from pydantic-settings if available,
    otherwise fall back to the DB_URL env var (then a sensible default).

    :return: The database URL.
    """
    # Try pydantic-settings first (works with Settings class if `db_url` exists)
    try:
        from tasman_etl.config import (
            Settings,  # local import to avoid hard dependency at import-time
        )

        settings = Settings()  # will read env vars automatically
        db_url = getattr(settings, "db_url", None)
        if isinstance(db_url, str) and db_url:
            return db_url
    except Exception:
        # If Settings isn't present or doesn't define db_url, just use env/default
        pass

    return os.getenv("DB_URL", _DEFAULT_DB_URL)


@dataclass(frozen=True)
class Engine:
    """
    Thin holder for a normalised DSN and a convenience connect() method.

    Use:
        from tasman_etl.db.engine import engine
        with psycopg.connect(engine.dsn) as conn:
            ...
    or:
        from tasman_etl.db.engine import engine
        with engine.connect() as conn:
            ...
    """

    dsn: str

    def connect(self, **kwargs) -> psycopg.Connection:
        """
        Create a new database connection.

        :return: A new database connection.
        """
        return psycopg.connect(self.dsn, **kwargs)


def build_engine(app_name: str = "tasman_etl") -> Engine:
    """
    Normalise/augment the DSN via psycopg.conninfo to set things like application_name.

    :param app_name: The application name to set in the connection (default: "tasman_etl").
    :return: An Engine instance.
    """
    url = _load_db_url()
    # conninfo.make_conninfo accepts either a URI or key=value string and merges options cleanly.
    # (libpq/psycopg will accept both URI and DSN formats.)
    dsn = conninfo.make_conninfo(url, application_name=app_name)
    return Engine(dsn=dsn)


# Singleton used across the app
engine = build_engine()
