"""
The main entry point and overall orchestration logic for the ETL process.
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import UTC, datetime
from typing import TypedDict

from tasman_etl.config import get_settings
from tasman_etl.db.engine import engine
from tasman_etl.db.repository import PageBundle, upsert_page
from tasman_etl.dq.gx.validate import validate_page_jobs
from tasman_etl.http.usajobs import UsaJobsClient
from tasman_etl.models import ApiResponse
from tasman_etl.storage.bronze_s3 import bronze_key, put_json_gz, utc_now_iso
from tasman_etl.transform import normalise_page

logging.basicConfig(level=logging.INFO)


class IngestStats(TypedDict):
    bronze_key: str
    jobs: int
    locations: int
    categories: int
    grades: int


def persist_raw_page(run_id: str, page: int, request_dict: dict, response_dict: dict) -> str:
    """
    Persist a raw page of data to S3.

    :param run_id: The ID of the run.
    :param page: The page number.
    :param request_dict: The request metadata.
    :param response_dict: The response payload.
    :return: The S3 key for the bronze job.
    """
    envelope = {
        "request": {**request_dict, "sent_at": request_dict.get("sent_at", utc_now_iso())},
        "response": {
            "status": response_dict.get("status", 200),
            "headers": response_dict.get("headers", {}),
            "received_at": utc_now_iso(),
            "payload": response_dict["payload"],
        },
        "ingest": {"ingest_run_id": run_id},
    }
    key = bronze_key(run_id, page)
    put_json_gz(key, envelope)
    return key


def ingest_search_page(
    *,
    run_id: str,
    page: int,
    keyword: str,
    location_name: str | None,
    radius_miles: int | None,
    results_per_page: int = 50,
    fields: str | None = None,
    dq_enforce: bool | None = None,  # override Settings() if desired
) -> IngestStats:
    """
    End-to-end for one Search page:
      1) fetch page (HTTP)
      2) persist bronze
      3) validate (GX)
      4) normalise -> bundles
      5) upsert into DB
    Returns simple run stats.

    :param run_id: The ID of the run.
    :param page: The page number.
    :param keyword: The search keyword.
    :param location_name: The location name (optional).
    :param radius_miles: The search radius in miles (optional).
    :param results_per_page: The number of results per page (default: 50).
    :param fields: The fields to include in the response (default: None).
    :param dq_enforce: Whether to enforce data quality checks (default: None).
    :return: A dictionary of run statistics.
    """
    # 1) fetch
    client = UsaJobsClient()
    request_dict, response_dict = client.fetch_search_page(
        keyword=keyword,
        location_name=location_name,
        radius_miles=radius_miles,
        results_per_page=results_per_page,
        page=page,
        fields=fields,
    )

    # 2) bronze
    bronze_key_out = persist_raw_page(run_id, page, request_dict, response_dict)

    # 3) parse & normalise
    resp = ApiResponse.model_validate(response_dict["payload"])
    bundles = normalise_page(resp, ingest_run_id=run_id, source_event_time=datetime.now(UTC))

    # 4) validation (GX)
    jobs = [b.job for b in bundles]
    locs = [loc for b in bundles for loc in b.locations]
    vx = validate_page_jobs(jobs, locs)
    settings = get_settings()
    enforce = settings.dq_enforce if dq_enforce is None else dq_enforce
    if enforce and not vx.passed:
        # Fail hard if gate is on
        failed = [r.name for r in vx.rules if not r.success]
        raise RuntimeError(f"Validation failed (gate on). Failed rules: {failed}")

    # 5) load
    stats: IngestStats = {
        "bronze_key": bronze_key_out,
        "jobs": 0,
        "locations": 0,
        "categories": 0,
        "grades": 0,
    }
    with engine.connect() as conn:  # or `psycopg.connect(engine.dsn) as conn`
        for b in bundles:
            # If using Pydantic for PageBundle in future, uncomment the line below
            # page_bundle = PageBundle(**b.model_dump())
            page_bundle = PageBundle(
                job=b.job,
                details=b.details,
                locations=list(b.locations),  # ensure list (defensive copy)
                categories=list(b.categories),
                grades=list(b.grades),
            )
            upsert_page(conn, page_bundle)
            stats["jobs"] += 1
            stats["locations"] += len(b.locations)
            stats["categories"] += len(b.categories)
            stats["grades"] += len(b.grades)

    return stats


def _env_int(name: str, default: int | None = None) -> int | None:
    v = os.getenv(name)
    if v is None or v == "":
        return default
    try:
        return int(v)
    except ValueError as e:
        raise RuntimeError(f"Invalid int for {name}: {v}") from e


def _derive_run_id() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")


def main() -> int:
    """Executable entrypoint for batch ingestion.

    Controlled by environment variables (all optional unless noted):
      KEYWORD (required)                – USAJOBS search keyword.
      LOCATION_NAME                     – Location filter (e.g. "Chicago, Illinois").
      RADIUS_MILES                      – Integer radius in miles.
      RESULTS_PER_PAGE (default 50)     – Page size requested from API.
      MAX_PAGES (default 1)             – Max pages to request (stop early on empty page).
      FIELDS                            – Optional API Fields parameter.
      DQ_ENFORCE                        – Override data quality gate (true/false).

    Returns process exit code (0 success, 1 failure / validation fail / config error).
    """
    logger = logging.getLogger("tasman.main")

    keyword = os.getenv("KEYWORD")
    if not keyword:
        logger.error("missing KEYWORD env var")
        return 1

    location_name = os.getenv("LOCATION_NAME") or None
    radius_miles = _env_int("RADIUS_MILES")
    results_per_page = _env_int("RESULTS_PER_PAGE", 50) or 50
    max_pages = _env_int("MAX_PAGES", 1) or 1
    fields = os.getenv("FIELDS") or None

    dq_env = os.getenv("DQ_ENFORCE")
    dq_override: bool | None = None
    if dq_env is not None:
        dq_override = dq_env.lower() in {"1", "true", "yes", "on"}

    run_id = os.getenv("RUN_ID") or _derive_run_id()
    logger.info(
        "ingest.start",
        extra={
            "run_id": run_id,
            "keyword": keyword,
            "location_name": location_name,
            "radius_miles": radius_miles,
            "results_per_page": results_per_page,
            "max_pages": max_pages,
            "fields": fields,
            "dq_override": dq_override,
        },
    )

    total = {"jobs": 0, "locations": 0, "categories": 0, "grades": 0}
    pages_fetched = 0
    try:
        for page in range(1, max_pages + 1):
            stats = ingest_search_page(
                run_id=run_id,
                page=page,
                keyword=keyword,
                location_name=location_name,
                radius_miles=radius_miles,
                results_per_page=results_per_page,
                fields=fields,
                dq_enforce=dq_override,
            )
            pages_fetched += 1
            # Explicit aggregation to satisfy mypy (TypedDict requires literal keys)
            total["jobs"] += stats["jobs"]
            total["locations"] += stats["locations"]
            total["categories"] += stats["categories"]
            total["grades"] += stats["grades"]
            # Heuristic stop: if fewer jobs than page size, assume last page.
            if stats["jobs"] < results_per_page:
                break
    except Exception as e:  # pragma: no cover - top level failure
        logger.error("ingest.failed", extra={"error": str(e), "run_id": run_id})
        return 1

    logger.info(
        "ingest.complete",
        extra={"run_id": run_id, "pages": pages_fetched, **total},
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - integration path
    sys.exit(main())
