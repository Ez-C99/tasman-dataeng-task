"""
This module provides a client for accessing USAJOBS codelists with caching.
"""

from __future__ import annotations

import os

import requests

DEFAULT_BASE = "https://developer.usajobs.gov/api/codelist"


class CodelistClient:
    """
    Minimal USAJOBS codelist client with TTL cache.
    Docs: GET {BASE}/{list_name} returns {"CodeList":[{"ValidValue":[{"Code":..,"Value":..}, ...]}]}
    """

    def __init__(
        self,
        base_url: str | None = None,
        ttl_seconds: int = 24 * 3600,
        session: requests.Session | None = None,
    ):
        """
        Initialise the codelist client.

        :param base_url: Base URL for the API.
        :param ttl_seconds: Time-to-live for cached responses.
        :param session: Optional requests.Session for HTTP requests.
        """
        self.base_url = base_url or os.environ.get("USAJOBS_CODELIST_BASE", DEFAULT_BASE).rstrip(
            "/"
        )
        self.ttl = ttl_seconds
        self._cache: dict[str, tuple[float, dict[str, str]]] = {}
        self._http = session or requests.Session()
