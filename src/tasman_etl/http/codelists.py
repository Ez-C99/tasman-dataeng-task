"""
This module provides a client for accessing USAJOBS codelists with caching.
"""

from __future__ import annotations

import os
import time

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

    def _expired(self, fetched_at: float) -> bool:
        """
        Check if the cached response has expired.

        :param fetched_at: Timestamp when the response was fetched.
        :return: True if the response has expired, False otherwise.
        """
        return (time.time() - fetched_at) > self.ttl

    def get_map(self, list_name: str) -> dict[str, str]:
        """
        Return {Code -> Value} mapping for a codelist, using TTL cache.

        :param list_name: Name of the codelist to retrieve.
        :return: A dictionary mapping codes to values for the specified codelist.
        """
        if list_name in self._cache and not self._expired(self._cache[list_name][0]):
            return self._cache[list_name][1]

        url = f"{self.base_url}/{list_name}"
        resp = self._http.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        code_map: dict[str, str] = {}
        for cl in (data or {}).get("CodeList", []):
            for vv in cl.get("ValidValue", []):
                code = str(vv.get("Code", "")).strip()
                value = str(vv.get("Value", "")).strip()
                if code:
                    code_map[code] = value

        self._cache[list_name] = (time.time(), code_map)
        return code_map
