from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from tasman_etl.models import ApiResponse, parse_page_json
from tasman_etl.transform import (
    Bundle,
    as_category_rows,
    as_details_row,
    as_grade_rows,
    as_job_row,
    as_location_rows,
    normalise_page,
)


def _load_sample() -> str:
    # Relative path from repo root when pytest is run there; falls back to absolute resolution.
    p = Path("data/sample_get.json")
    if not p.exists():  # fallback if CWD differs
        p = Path(__file__).resolve().parents[2] / "data" / "sample_get.json"
    return p.read_text(encoding="utf-8")


def test_normalise_page_with_sample():
    sample = _load_sample()
    resp = parse_page_json(sample)
    bundles = normalise_page(
        resp, ingest_run_id="test-run", source_event_time=datetime(2024, 1, 1, tzinfo=UTC)
    )

    assert bundles, "Expected at least one bundle from sample payload"
    b0 = bundles[0]
    assert isinstance(b0, Bundle)
    # Bundle components
    assert b0.job.position_id
    assert b0.details.job_summary or b0.details.agency_marketing_statement is not None
    assert len(b0.locations) >= 1
    assert isinstance(b0.categories, list)
    assert isinstance(b0.grades, list)
    # Pay ranges converted to int (via validators)
    if b0.job.pay_min is not None:
        assert isinstance(b0.job.pay_min, int)

    # Row mapping spot checks
    job_row = as_job_row(b0.job)
    assert job_row["position_id"] == b0.job.position_id
    details_row = as_details_row(b0.details)
    assert "job_summary" in details_row
    loc_rows = as_location_rows(1, b0.locations)
    assert loc_rows and loc_rows[0]["loc_idx"] == 0
    cat_rows = as_category_rows(1, b0.categories)
    grade_rows = as_grade_rows(1, b0.grades)
    # Ensure referential job_id assigned in mapping helpers
    assert all(r["job_id"] == 1 for r in (*loc_rows, *cat_rows, *grade_rows))


def test_normalise_page_minimal_item():
    # Minimal synthetic payload: one result with only required fields
    payload = {
        "LanguageCode": "EN",
        "SearchResult": {
            "SearchResultCount": 1,
            "SearchResultCountAll": 1,
            "SearchResultItems": [
                {
                    "MatchedObjectId": "X1",
                    "MatchedObjectDescriptor": {
                        "PositionID": "PID-1",
                        "PositionTitle": "Engineer",
                        "PositionURI": "https://x.example/job/1",
                    },
                }
            ],
        },
    }
    resp = ApiResponse.model_validate(payload)
    bundles = normalise_page(resp, ingest_run_id="rid", source_event_time=None)
    assert len(bundles) == 1
    b = bundles[0]
    # Defaults
    assert b.job.position_title == "Engineer"
    assert b.job.apply_uri == []  # list default
    assert b.locations == []
    assert b.categories == []
    assert b.grades == []


def test_extra_fields_ignored():
    payload = {
        "LanguageCode": "EN",
        "SearchResult": {
            "SearchResultCount": 1,
            "SearchResultCountAll": 1,
            "SearchResultItems": [
                {
                    "MatchedObjectId": "X2",
                    "MatchedObjectDescriptor": {
                        "PositionID": "PID-2",
                        "PositionTitle": "Data Scientist",
                        "PositionURI": "https://x.example/job/2",
                        "UnknownField": "SHOULD_BE_IGNORED",
                    },
                }
            ],
        },
    }
    resp = ApiResponse.model_validate(payload)
    bundles = normalise_page(resp, ingest_run_id="rid", source_event_time=None)
    assert bundles[0].job.position_title == "Data Scientist"
    # Unknown field should not appear in JobRecord row mapping
    job_row = as_job_row(bundles[0].job)
    assert "UnknownField" not in job_row


def test_translation_of_major_duties_join():
    payload = {
        "SearchResult": {
            "SearchResultCount": 1,
            "SearchResultCountAll": 1,
            "SearchResultItems": [
                {
                    "MatchedObjectId": "Y1",
                    "MatchedObjectDescriptor": {
                        "PositionID": "PID-3",
                        "PositionTitle": "Analyst",
                        "PositionURI": "https://x.example/job/3",
                        "UserArea": {"Details": {"MajorDuties": ["A", "B", "C"]}},
                    },
                }
            ],
        }
    }
    resp = ApiResponse.model_validate(payload)
    bundle = normalise_page(resp, ingest_run_id="rid", source_event_time=None)[0]
    assert bundle.details.major_duties == "A; B; C"
