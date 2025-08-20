from dataclasses import dataclass
from datetime import datetime

from .models import (
    ApiResponse,
    JobCategoryRecord,
    JobDetailsRecord,
    JobGradeRecord,
    JobLocationRecord,
    JobRecord,
    normalise_item,
)


@dataclass(frozen=True)
class Bundle:
    """
    Represents a bundle of job-related data.
    """

    job: JobRecord
    details: JobDetailsRecord
    locations: list[JobLocationRecord]
    categories: list[JobCategoryRecord]
    grades: list[JobGradeRecord]


def normalise_page(
    resp: ApiResponse,
    ingest_run_id: str,
    source_event_time: datetime | None,
) -> list[Bundle]:
    """
    Convert a parsed API response into normalised bundles (pure transform).

    :param resp: The API response to normalise.
    :param ingest_run_id: The ID of the ingest run.
    :param source_event_time: The source event time.
    :return: A list of normalised bundles.
    """
    out: list[Bundle] = []
    for item in resp.SearchResult.SearchResultItems:
        job, details, locs, cats, grades = normalise_item(item, ingest_run_id, source_event_time)
        out.append(Bundle(job=job, details=details, locations=locs, categories=cats, grades=grades))
    return out


# -------- Optional enrichment via codelists (kept minimal & decoupled) --------


# def enrich_with_codelists(bundles: Iterable[Bundle], codelists: CodelistClient) -> list[Bundle]:
#     """
#     Example: translate pay rate interval code to a label (if present).
#     Extend as needed; keep enrichment optional/pure.

#     :param bundles: The job bundles to enrich.
#     :param codelists: The codelist client to use for enrichment.
#     :return: A list of enriched job bundles.
#     """
#     # rate_map = codelists.get_map("payPlans") if False else {}
# placeholder example; extend later

#     # Currently no extra columns exist for labels; keep codes as-is.
#     # Return the same bundles (no mutation since dataclasses are frozen).
#     return list(bundles)


# -------- Row dict mappers (DB loader will consume these) --------


def as_job_row(j: JobRecord) -> dict:
    """
    Map JobRecord to a database row representation.

    :param j: The JobRecord to map.
    :return: A dictionary representing the database row.
    """
    return {
        "position_id": j.position_id,
        "matched_object_id": j.matched_object_id,
        "position_uri": j.position_uri,
        "position_title": j.position_title,
        "organization_name": j.organization_name,
        "department_name": j.department_name,
        "apply_uri": j.apply_uri,  # psycopg3 adapts Python list -> Postgres text[]
        "position_location_display": j.position_location_display,
        "pay_min": j.pay_min,
        "pay_max": j.pay_max,
        "pay_rate_interval_code": j.pay_rate_interval_code,
        "qualification_summary": j.qualification_summary,
        "publication_start_date": j.publication_start_date,
        "application_close_date": j.application_close_date,
        "position_start_date": j.position_start_date,
        "position_end_date": j.position_end_date,
        "remote_indicator": j.remote_indicator,
        "telework_eligible": j.telework_eligible,
        "source_event_time": j.source_event_time,
        "ingest_run_id": j.ingest_run_id,
        "raw_json": j.raw_json,
    }


def as_details_row(jd: JobDetailsRecord) -> dict:
    """
    Map JobDetailsRecord to a database row representation.

    :param jd: The JobDetailsRecord to map.
    :return: A dictionary representing the database row.
    """
    return {
        "job_summary": jd.job_summary,
        "low_grade": jd.low_grade,
        "high_grade": jd.high_grade,
        "promotion_potential": jd.promotion_potential,
        "organization_codes": jd.organization_codes,
        "relocation": jd.relocation,
        "hiring_path": jd.hiring_path,
        "mco_tags": jd.mco_tags,
        "total_openings": jd.total_openings,
        "agency_marketing_statement": jd.agency_marketing_statement,
        "travel_code": jd.travel_code,
        "apply_online_url": jd.apply_online_url,
        "detail_status_url": jd.detail_status_url,
        "major_duties": jd.major_duties,
        "education": jd.education,
        "requirements": jd.requirements,
        "evaluations": jd.evaluations,
        "how_to_apply": jd.how_to_apply,
        "what_to_expect_next": jd.what_to_expect_next,
        "required_documents": jd.required_documents,
        "benefits": jd.benefits,
        "benefits_url": jd.benefits_url,
        "benefits_display_default_text": jd.benefits_display_default_text,
        "other_information": jd.other_information,
        "key_requirements": jd.key_requirements,
        "within_area": jd.within_area,
        "commute_distance": jd.commute_distance,
        "service_type": jd.service_type,
        "announcement_closing_type": jd.announcement_closing_type,
        "agency_contact_email": jd.agency_contact_email,
        "security_clearance": jd.security_clearance,
        "drug_test_required": jd.drug_test_required,
        "position_sensitivity": jd.position_sensitivity,
        "adjudication_type": jd.adjudication_type,
        "financial_disclosure": jd.financial_disclosure,
        "bargaining_unit_status": jd.bargaining_unit_status,
    }


def as_location_rows(job_id: int, locs: list[JobLocationRecord]) -> list[dict]:
    """
    Map JobLocationRecord to a database row representation.

    :param job_id: The ID of the job.
    :param locs: A list of JobLocationRecord instances.
    :return: A list of dictionaries representing the database rows.
    """
    return [
        {
            "job_id": job_id,
            "loc_idx": x.loc_idx,
            "location_name": x.location_name,
            "country_code": x.country_code,
            "country_sub_division_code": x.country_sub_division_code,
            "city_name": x.city_name,
            "latitude": x.latitude,
            "longitude": x.longitude,
        }
        for x in locs
    ]


def as_category_rows(job_id: int, cats: list[JobCategoryRecord]) -> list[dict]:
    """
    Map JobCategoryRecord to a database row representation.

    :param job_id: The ID of the job.
    :param cats: A list of JobCategoryRecord instances.
    :return: A list of dictionaries representing the database rows.
    """
    return [{"job_id": job_id, "code": c.code, "name": c.name} for c in cats]


def as_grade_rows(job_id: int, grades: list[JobGradeRecord]) -> list[dict]:
    """
    Map JobGradeRecord to a database row representation.

    :param job_id: The ID of the job.
    :param grades: A list of JobGradeRecord instances.
    :return: A list of dictionaries representing the database rows.
    """
    return [{"job_id": job_id, "code": g.code} for g in grades]
