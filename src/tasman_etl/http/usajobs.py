"""
A client for the USAJOBS API.
"""

from __future__ import annotations

import logging
import os
import random
import time
from typing import Any

import requests

logger = logging.getLogger("tasman.usajobs")


class UsaJobsClient:
    """USAJOBS Search API client (production focused).

    Environment variables (unless explicitly passed):
      * USAJOBS_HOST          (default: data.usajobs.gov)
      * USAJOBS_USER_AGENT    (required – registered email)
      * USAJOBS_AUTH_KEY      (required – API key)

    Features:
      * Explicit Accept header (vendor + JSON) to avoid empty bodies.
      * Exponential backoff with jitter on network / HTTP >=500.
      * Structured debug logging of attempts, latency, and headers.
      * Raises RuntimeError on persistent empty/invalid JSON despite 200.
    """

    def __init__(
        self,
        host: str | None = None,
        user_agent: str | None = None,
        auth_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 15.0,
        accept: str | None = None,
    ) -> None:
        """
        Initialise the USAJOBS API client.

        :param host: The API host (default: data.usajobs.gov)
        :param user_agent: The User-Agent string (required)
        :param auth_key: The API key (required)
        :param base_url: The base URL for API requests (optional)
        :param timeout: The request timeout in seconds (default: 15.0)
        :param accept: The Accept header for API requests (optional)
        """
        try:  # load .env lazily if available
            from tasman_etl.config import load_env

            load_env()
        except Exception:
            pass

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
            "User-Agent": self.user_agent,
            "Authorization-Key": self.auth_key,
            "Accept": accept or "application/hr+json, application/json;q=0.9, */*;q=0.8",
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
        retry: int = 3,
        backoff_base: float = 0.75,
        backoff_cap: float = 6.0,
    ) -> tuple[dict, dict]:
        """
        Fetch one page from the Search API and return (request_dict, response_dict).

        :param keyword: The search keyword (required)
        :param location_name: The location name (optional)
        :param radius_miles: The search radius in miles (optional)
        :param results_per_page: The number of results per page (default: 50)
        :param page: The page number to retrieve (default: 1)
        :param fields: The fields to include in the response (optional)
        :param retry: The number of retry attempts for transient errors (default: 3)
        :param backoff_base: The base backoff time in seconds (default: 0.75)
        :param backoff_cap: The maximum backoff time in seconds (default: 6.0)
        :return: A tuple containing the request dictionary and the response dictionary
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

        request_dict = {"endpoint": "/api/search", "params": params}

        last_exc: Exception | None = None
        for attempt in range(1, retry + 2):  # attempts = retry + 1
            start = time.perf_counter()
            try:
                resp = requests.get(
                    self.base_url,
                    headers=self._headers,
                    params=params,
                    timeout=self.timeout,
                )
                latency = (time.perf_counter() - start) * 1000
                content_type = resp.headers.get("Content-Type", "")

                logger.debug(
                    "usajobs.request",
                    extra={
                        "status": resp.status_code,
                        "latency_ms": round(latency, 1),
                        "attempt": attempt,
                        "page": page,
                        "results_per_page": results_per_page,
                        "content_type": content_type,
                        "rate_limit": {
                            k: v
                            for k, v in resp.headers.items()
                            if k.lower().startswith("x-ratelimit")
                        },
                    },
                )

                if resp.status_code >= 500:
                    raise RuntimeError(f"HTTP {resp.status_code} server error")

                payload: dict[str, Any] = {}
                if content_type.startswith("application/json") or "hr+json" in content_type:
                    try:
                        payload = resp.json() or {}
                    except Exception as je:  # decode issue
                        logger.warning("json.decode_failed", extra={"error": str(je)})

                if resp.status_code == 200 and not payload:
                    snippet = (resp.text or "")[:200]
                    raise RuntimeError(
                        f"empty_payload: status=200 ct={content_type} snippet={snippet!r}"
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
            except Exception as e:  # network / transient / empty payload / decode
                last_exc = e
                if attempt <= retry:
                    delay = min(backoff_cap, backoff_base * (2 ** (attempt - 1)))
                    jitter = delay * (0.4 * random.random() - 0.2)
                    sleep_for = max(0.05, delay + jitter)
                    logger.warning(
                        "usajobs.retrying",
                        extra={
                            "attempt": attempt,
                            "error": str(e),
                            "sleep_s": round(sleep_for, 2),
                        },
                    )
                    time.sleep(sleep_for)
                    continue
                break

        assert last_exc is not None
        logger.error("usajobs.failed", extra={"error": str(last_exc)})
        raise last_exc
