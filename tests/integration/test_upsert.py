import os
from datetime import UTC, datetime

import psycopg
from tasman_etl.db.repository import PageBundle, upsert_page
from tasman_etl.models import (
    JobCategoryRecord,
    JobDetailsRecord,
    JobGradeRecord,
    JobLocationRecord,
    JobRecord,
)

DB_URL = os.getenv("DB_URL", "postgresql://postgres:localpw@localhost:5432/usajobs")


def _bundle(position_id: str) -> PageBundle:
    job = JobRecord(
        position_id=position_id,
        matched_object_id="X1",
        position_uri="http://example/job",
        position_title="Data Engineer",
        organization_name="Org",
        department_name=None,
        apply_uri=["http://apply"],
        position_location_display="Chicago, IL",
        pay_min=90000,
        pay_max=120000,
        pay_rate_interval_code="PA",
        qualification_summary=None,
        publication_start_date=datetime.now(UTC),
        application_close_date=None,
        position_start_date=None,
        position_end_date=None,
        remote_indicator=True,
        telework_eligible=True,
        source_event_time=datetime.now(UTC),
        ingest_run_id="run-1",
        raw_json={"demo": True},
    )
    details = JobDetailsRecord()
    locs = [JobLocationRecord(loc_idx=0, city_name="Chicago")]
    cats = [JobCategoryRecord(code="2210", name="IT")]
    grades = [JobGradeRecord(code="12")]
    return PageBundle(job, details, locs, cats, grades)


def test_upsert_idempotent():
    with psycopg.connect(DB_URL) as conn:
        b = _bundle("CHI-DEMO-1")
        job_id_1 = upsert_page(conn, b)
        # change a field and re-upsert
        b.job.position_title = "Senior Data Engineer"
        job_id_2 = upsert_page(conn, b)
        assert job_id_1 == job_id_2

        with conn.cursor() as cur:
            cur.execute("select count(*) from job where position_id = %s", (b.job.position_id,))
            row = cur.fetchone()
            assert row is not None, "Expected a row from COUNT(*) query"
            assert row[0] == 1
