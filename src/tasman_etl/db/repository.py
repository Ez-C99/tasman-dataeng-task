"""
This module contains database repository functions for managing job data.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import psycopg
from psycopg.types.json import Json

from tasman_etl.models import (
    JobCategoryRecord,
    JobDetailsRecord,
    JobGradeRecord,
    JobLocationRecord,
    JobRecord,
)


@dataclass(frozen=True)
class PageBundle:
    job: JobRecord
    details: JobDetailsRecord
    locations: list[JobLocationRecord]
    categories: list[JobCategoryRecord]
    grades: list[JobGradeRecord]


def upsert_page(
    conn: psycopg.Connection,
    bundle: PageBundle,
    *,
    statement_timeout: str = "5s",
) -> int:
    """
    Upsert one job and fully synchronise its children in a single txn.
    Returns job_id.

    :param conn: The database connection.
    :param bundle: The job bundle to upsert.
    :param statement_timeout: The statement timeout to use.
    :return: The job ID of the upserted job.
    """
    with conn.transaction(), conn.cursor() as cur:  # combined contexts (SIM117)
        # keep the txn bounded (LOCAL scope for this txn)
        cur.execute("SET LOCAL statement_timeout = '5s'")  # literal, not a %s param

        job_id = _upsert_job(cur, bundle.job)

        # Replace children for determinism
        cur.execute("DELETE FROM job_location WHERE job_id = %s;", (job_id,))
        cur.execute("DELETE FROM job_category WHERE job_id = %s;", (job_id,))
        cur.execute("DELETE FROM job_grade WHERE job_id = %s;", (job_id,))

        _insert_locations(cur, job_id, bundle.locations)
        _insert_categories(cur, job_id, bundle.categories)
        _insert_grades(cur, job_id, bundle.grades)

        _upsert_details(cur, job_id, bundle.details)

        return job_id


# ---------- helpers ----------


def _upsert_job(cur: psycopg.Cursor, j: JobRecord) -> int:
    """
    Upsert a job record into the database.

    :param cur: The database cursor.
    :param j: The job record to upsert.
    :return: The job ID of the upserted job.
    """
    sql = """
    INSERT INTO job (
        position_id,
        matched_object_id,
        position_uri,
        position_title,
        organization_name,
        department_name,
        apply_uri,
        position_location_display,
        pay_min,
        pay_max,
        pay_rate_interval_code,
        qualification_summary,
        publication_start_date,
        application_close_date,
        position_start_date,
        position_end_date,
        remote_indicator,
        telework_eligible,
        source_event_time,
        ingest_run_id,
        raw_json
    )
    VALUES (
        %(position_id)s,
        %(matched_object_id)s,
        %(position_uri)s,
        %(position_title)s,
        %(organization_name)s,
        %(department_name)s,
        %(apply_uri)s,
        %(position_location_display)s,
        %(pay_min)s,
        %(pay_max)s,
        %(pay_rate_interval_code)s,
        %(qualification_summary)s,
        %(publication_start_date)s,
        %(application_close_date)s,
        %(position_start_date)s,
        %(position_end_date)s,
        %(remote_indicator)s,
        %(telework_eligible)s,
        %(source_event_time)s,
        %(ingest_run_id)s,
        %(raw_json)s
    )
    ON CONFLICT (position_id) DO UPDATE SET
        matched_object_id = EXCLUDED.matched_object_id,
        position_uri = EXCLUDED.position_uri,
        position_title = EXCLUDED.position_title,
        organization_name = EXCLUDED.organization_name,
        department_name = EXCLUDED.department_name,
        apply_uri = EXCLUDED.apply_uri,
        position_location_display = EXCLUDED.position_location_display,
        pay_min = EXCLUDED.pay_min,
        pay_max = EXCLUDED.pay_max,
        pay_rate_interval_code = EXCLUDED.pay_rate_interval_code,
        qualification_summary = EXCLUDED.qualification_summary,
        publication_start_date = EXCLUDED.publication_start_date,
        application_close_date = EXCLUDED.application_close_date,
        position_start_date = EXCLUDED.position_start_date,
        position_end_date = EXCLUDED.position_end_date,
        remote_indicator = EXCLUDED.remote_indicator,
        telework_eligible = EXCLUDED.telework_eligible,
        source_event_time = EXCLUDED.source_event_time,
        ingest_run_id = EXCLUDED.ingest_run_id,
        raw_json = EXCLUDED.raw_json,
        updated_at = now()
    RETURNING job_id;
    """
    cur.execute(
        sql,
        {
            **j.model_dump(mode="python"),
            "raw_json": Json(j.raw_json),  # ensure proper JSONB
        },
    )
    row = cur.fetchone()
    if row is None:
        raise RuntimeError(
            "Upsert of job failed to return job_id (no row from RETURNING). "
            "Verify SQL still ends with 'RETURNING job_id;' and that ON CONFLICT uses DO UPDATE."
        )
    return int(row[0])


def _insert_locations(cur: psycopg.Cursor, job_id: int, rows: Sequence[JobLocationRecord]) -> None:
    """
    Insert or update job location records for a specific job.

    :param cur: The database cursor.
    :param job_id: The ID of the job to update.
    :param rows: The job location records to upsert.
    """
    if not rows:
        return
    sql = """
    INSERT INTO job_location (
        job_id, loc_idx, location_name, country_code, country_sub_division_code,
        city_name, latitude, longitude
    )
    VALUES (
        %(job_id)s, %(loc_idx)s, %(location_name)s, %(country_code)s, %(country_sub_division_code)s,
        %(city_name)s, %(latitude)s, %(longitude)s
    )
    ON CONFLICT (job_id, loc_idx) DO UPDATE SET
        location_name = EXCLUDED.location_name,
        country_code = EXCLUDED.country_code,
        country_sub_division_code = EXCLUDED.country_sub_division_code,
        city_name = EXCLUDED.city_name,
        latitude = EXCLUDED.latitude,
        longitude = EXCLUDED.longitude,
        updated_at = now();
    """
    for r in rows:
        cur.execute(sql, {"job_id": job_id, **r.model_dump(mode="python")})


def _insert_categories(cur: psycopg.Cursor, job_id: int, rows: Sequence[JobCategoryRecord]) -> None:
    """
    Insert or update job category records for a specific job.

    :param cur: The database cursor.
    :param job_id: The ID of the job to update.
    :param rows: The job category records to upsert.
    """
    if not rows:
        return
    sql = """
    INSERT INTO job_category (job_id, code, name)
    VALUES (%(job_id)s, %(code)s, %(name)s)
    ON CONFLICT (job_id, code) DO UPDATE SET
        name = EXCLUDED.name,
        updated_at = now();
    """
    for r in rows:
        cur.execute(sql, {"job_id": job_id, **r.model_dump(mode="python")})


def _insert_grades(cur: psycopg.Cursor, job_id: int, rows: Sequence[JobGradeRecord]) -> None:
    """
    Insert or update job grade records for a specific job.

    :param cur: The database cursor.
    :param job_id: The ID of the job to update.
    :param rows: The job grade records to upsert.
    """
    if not rows:
        return
    sql = """
    INSERT INTO job_grade (job_id, code)
    VALUES (%(job_id)s, %(code)s)
    ON CONFLICT (job_id, code) DO NOTHING;
    """
    for r in rows:
        cur.execute(sql, {"job_id": job_id, **r.model_dump(mode="python")})


def _upsert_details(cur: psycopg.Cursor, job_id: int, d: JobDetailsRecord) -> None:
    sql = """
    INSERT INTO job_details (
        job_id,
        job_summary,
        low_grade,
        high_grade,
        promotion_potential,
        organization_codes,
        relocation,
        hiring_path,
        mco_tags,
        total_openings,
        agency_marketing_statement,
        travel_code,
        apply_online_url,
        detail_status_url,
        major_duties,
        education,
        requirements,
        evaluations,
        how_to_apply,
        what_to_expect_next,
        required_documents,
        benefits,
        benefits_url,
        benefits_display_default_text,
        other_information,
        key_requirements,
        within_area,
        commute_distance,
        service_type,
        announcement_closing_type,
        agency_contact_email,
        security_clearance,
        drug_test_required,
        position_sensitivity,
        adjudication_type,
        financial_disclosure,
        bargaining_unit_status
    )
    VALUES (
        %(job_id)s,
        %(job_summary)s,
        %(low_grade)s,
        %(high_grade)s,
        %(promotion_potential)s,
        %(organization_codes)s,
        %(relocation)s,
        %(hiring_path)s,
        %(mco_tags)s,
        %(total_openings)s,
        %(agency_marketing_statement)s,
        %(travel_code)s,
        %(apply_online_url)s,
        %(detail_status_url)s,
        %(major_duties)s,
        %(education)s,
        %(requirements)s,
        %(evaluations)s,
        %(how_to_apply)s,
        %(what_to_expect_next)s,
        %(required_documents)s,
        %(benefits)s,
        %(benefits_url)s,
        %(benefits_display_default_text)s,
        %(other_information)s,
        %(key_requirements)s,
        %(within_area)s,
        %(commute_distance)s,
        %(service_type)s,
        %(announcement_closing_type)s,
        %(agency_contact_email)s,
        %(security_clearance)s,
        %(drug_test_required)s,
        %(position_sensitivity)s,
        %(adjudication_type)s,
        %(financial_disclosure)s,
        %(bargaining_unit_status)s
    )
    ON CONFLICT (job_id) DO UPDATE SET
        job_summary = EXCLUDED.job_summary,
        low_grade = EXCLUDED.low_grade,
        high_grade = EXCLUDED.high_grade,
        promotion_potential = EXCLUDED.promotion_potential,
        organization_codes = EXCLUDED.organization_codes,
        relocation = EXCLUDED.relocation,
        hiring_path = EXCLUDED.hiring_path,
        mco_tags = EXCLUDED.mco_tags,
        total_openings = EXCLUDED.total_openings,
        agency_marketing_statement = EXCLUDED.agency_marketing_statement,
        travel_code = EXCLUDED.travel_code,
        apply_online_url = EXCLUDED.apply_online_url,
        detail_status_url = EXCLUDED.detail_status_url,
        major_duties = EXCLUDED.major_duties,
        education = EXCLUDED.education,
        requirements = EXCLUDED.requirements,
        evaluations = EXCLUDED.evaluations,
        how_to_apply = EXCLUDED.how_to_apply,
        what_to_expect_next = EXCLUDED.what_to_expect_next,
        required_documents = EXCLUDED.required_documents,
        benefits = EXCLUDED.benefits,
        benefits_url = EXCLUDED.benefits_url,
        benefits_display_default_text = EXCLUDED.benefits_display_default_text,
        other_information = EXCLUDED.other_information,
        key_requirements = EXCLUDED.key_requirements,
        within_area = EXCLUDED.within_area,
        commute_distance = EXCLUDED.commute_distance,
        service_type = EXCLUDED.service_type,
        announcement_closing_type = EXCLUDED.announcement_closing_type,
        agency_contact_email = EXCLUDED.agency_contact_email,
        security_clearance = EXCLUDED.security_clearance,
        drug_test_required = EXCLUDED.drug_test_required,
        position_sensitivity = EXCLUDED.position_sensitivity,
        adjudication_type = EXCLUDED.adjudication_type,
        financial_disclosure = EXCLUDED.financial_disclosure,
        bargaining_unit_status = EXCLUDED.bargaining_unit_status,
        updated_at = now();
    """
    cur.execute(sql, {"job_id": job_id, **d.model_dump(mode="python")})
