"""
The main entry point and overall orchestration logic for the ETL process.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TypedDict

from tasman_etl.config import Settings
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
    settings = Settings()
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
    with engine.connect() as conn:  # or `psycopg.connect(engine.dsn) as conn``
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
