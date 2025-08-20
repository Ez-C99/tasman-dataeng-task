"""
This module provides a client for the USAJOBS API.
"""

from __future__ import annotations

import os
import time
from typing import Any

import requests


class UsaJobsClient:
    """
    Minimal USAJOBS Search API client.

    Reads required headers from env:
      - USAJOBS_HOST (default: data.usajobs.gov)
      - USAJOBS_USER_AGENT (your email registered with USAJOBS)
      - USAJOBS_AUTH_KEY (your API key)
    """

    def __init__(
        self,
        host: str | None = None,
        user_agent: str | None = None,
        auth_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 15.0,
    ) -> None:
        """
        Initialise the USAJOBS API client.

        :param host: The API host (default: data.usajobs.gov)
        :param user_agent: The User-Agent header value (default: USAJOBS_USER_AGENT env var)
        :param auth_key: The Authorization-Key header value (default: USAJOBS_AUTH_KEY env var)
        :param base_url: The base URL for API requests (default: https://{host}/api/search)
        :param timeout: The request timeout in seconds (default: 15.0)
        """
        self.host = host or os.getenv("USAJOBS_HOST", "data.usajobs.gov")
        self.user_agent = user_agent or os.getenv("USAJOBS_USER_AGENT")
        self.auth_key = auth_key or os.getenv("USAJOBS_AUTH_KEY")
        self.base_url = base_url or f"https://{self.host}/api/search"
        self.timeout = timeout

        if not self.user_agent or not self.auth_key:
            raise RuntimeError(
                "USAJOBS_USER_AGENT and USAJOBS_AUTH_KEY must be set in the environment"
            )

        self._headers = {
            "Host": self.host,
            "User-Agent": self.user_agent,
            "Authorization-Key": self.auth_key,
        }

    def fetch_search_page(
        self,
        *,
        keyword: str,
        location_name: str | None = None,
        radius_miles: int | None = None,
        results_per_page: int = 50,
        page: int = 1,
        fields: str | None = None,  # "full" or "min"
        retry: int = 2,
        backoff_sec: float = 1.0,
    ) -> tuple[dict, dict]:
        """
        Fetch one page from the Search API and return:
          request_dict: {"endpoint": "/api/search", "params": {...}}
          response_dict: {"status": int, "headers": {..}, "payload": dict}

        Shapes match what your bronze writer expects.

        :param keyword: The search keyword.
        :param location_name: The location name (optional).
        :param radius_miles: The search radius in miles (optional).
        :param results_per_page: The number of results per page (default: 50).
        :param page: The page number (default: 1).
        :param fields: The fields to include in the response (default: None).
        :param retry: The number of retry attempts (default: 2).
        :param backoff_sec: The backoff time in seconds (default: 1.0).
        :return: A tuple of (request_dict, response_dict).
        """
        params: dict[str, Any] = {
            "Keyword": keyword,
            "ResultsPerPage": results_per_page,
            "Page": page,
        }
        if location_name:
            params["LocationName"] = location_name
        if radius_miles is not None:
            params["Radius"] = radius_miles
        if fields:
            params["Fields"] = fields

        request_dict = {
            "endpoint": "/api/search",
            "params": params,
        }

        # simple bounded retry
        last_exc: Exception | None = None
        for attempt in range(retry + 1):
            try:
                resp = requests.get(
                    self.base_url,
                    headers=self._headers,
                    params=params,
                    timeout=self.timeout,
                )
                payload = (
                    resp.json()
                    if resp.headers.get("Content-Type", "").startswith("application/json")
                    else {}
                )
                response_dict = {
                    "status": resp.status_code,
                    "headers": {
                        k: v
                        for k, v in resp.headers.items()
                        if k.lower().startswith("x-ratelimit") or k.lower() in {"content-type"}
                    },
                    "payload": payload,
                }
                return request_dict, response_dict
            except Exception as e:  # network/transient
                last_exc = e
                if attempt < retry:
                    time.sleep(backoff_sec * (2**attempt))
                else:
                    raise

        # should never reach here
        assert last_exc is not None
        raise last_exc
