from __future__ import annotations

from datetime import UTC, datetime

from tasman_etl.models import (
    ApiResponse,
    ApiSearchResultItem,
    JobCategoryRecord,
    JobDetailsRecord,
    JobGradeRecord,
    JobLocationRecord,
    JobRecord,
    normalise_item,
)


def _single_item(payload: dict) -> ApiSearchResultItem:
    parsed = ApiResponse.model_validate(payload)
    return parsed.SearchResult.SearchResultItems[0]


def test_normalise_item_happy_path():
    payload = {
        "LanguageCode": "EN",
        "SearchResult": {
            "SearchResultCount": 1,
            "SearchResultCountAll": 1,
            "SearchResultItems": [
                {
                    "MatchedObjectId": "123",
                    "MatchedObjectDescriptor": {
                        "PositionID": "ABCD-1234",
                        "PositionTitle": "Data Engineer",
                        "PositionURI": "https://www.usajobs.gov/job/123",
                        "ApplyURI": ["https://apply.example/apply"],
                        "PositionLocationDisplay": "Chicago, IL",
                        "PositionLocation": [
                            {
                                "LocationName": "Chicago, Illinois, United States",
                                "CountryCode": "US",
                                "CountrySubDivisionCode": "IL",
                                "CityName": "Chicago",
                                "Longitude": -87.6298,
                                "Latitude": 41.8781,
                            }
                        ],
                        "OrganizationName": "Some Agency",
                        "DepartmentName": "Dept",
                        "JobCategory": [{"Name": "IT Mgmt", "Code": "2210"}],
                        "JobGrade": [{"Code": "GS-13"}],
                        "QualificationSummary": "Do data stuff.",
                        "PositionRemuneration": [
                            {
                                "MinimumRange": "$95,000",
                                "MaximumRange": "120,000",
                                "RateIntervalCode": "PA",
                            }
                        ],
                        "PublicationStartDate": "2025-08-01T00:00:00Z",
                        "ApplicationCloseDate": "2025-08-31T23:59:59Z",
                        "UserArea": {
                            "Details": {
                                "JobSummary": "Summary",
                                "DrugTestRequired": "Yes",
                                "TeleworkEligible": True,
                                "RemoteIndicator": False,
                                "MajorDuties": ["A", "B"],
                            }
                        },
                    },
                }
            ],
        },
    }

    item = _single_item(payload)
    job, jd, locs, cats, grades = normalise_item(
        item, ingest_run_id="RID", source_event_time=datetime.now(UTC)
    )

    assert isinstance(job, JobRecord)
    assert isinstance(jd, JobDetailsRecord)
    assert all(isinstance(x, JobLocationRecord) for x in locs)
    assert all(isinstance(x, JobCategoryRecord) for x in cats)
    assert all(isinstance(x, JobGradeRecord) for x in grades)

    assert job.position_id == "ABCD-1234"
    assert job.pay_min == 95000 and job.pay_max == 120000
    assert job.pay_rate_interval_code == "PA"
    assert jd.drug_test_required is True
    assert jd.major_duties == "A; B"
    assert locs[0].city_name == "Chicago"
    assert cats[0].code == "2210"
    assert grades[0].code == "GS-13"
    # raw_json round trip capture
    assert job.raw_json["MatchedObjectDescriptor"]["PositionID"] == "ABCD-1234"


def test_yes_no_bool_and_alias_position_sensitivity():
    payload = {
        "LanguageCode": "EN",
        "SearchResult": {
            "SearchResultCount": 1,
            "SearchResultCountAll": 1,
            "SearchResultItems": [
                {
                    "MatchedObjectId": "999",
                    "MatchedObjectDescriptor": {
                        "PositionID": "WXYZ-0001",
                        "PositionTitle": "Analyst",
                        "PositionURI": "https://x/job/999",
                        "PublicationStartDate": "2025-01-01T00:00:00Z",
                        "ApplicationCloseDate": "2025-01-02T00:00:00Z",
                        "UserArea": {
                            "Details": {
                                # historic typo alias should map to PositionSensitivity
                                "PositionSensitivitiy": "High",
                                "DrugTestRequired": "no",
                                "RemoteIndicator": "Yes",
                                "TeleworkEligible": "No",
                            }
                        },
                    },
                }
            ],
        },
    }
    item = _single_item(payload)
    job, jd, *_ = normalise_item(item, "RID2", source_event_time=None)

    # Remote/telework propagate
    assert job.remote_indicator is True  # RemoteIndicator "Yes"
    assert job.telework_eligible is False  # TeleworkEligible "No"
    # Position sensitivity flowed into details record
    assert jd.position_sensitivity == "High"
    # DrugTestRequired converted to bool False
    assert jd.drug_test_required is False


def test_missing_userarea_details_graceful():
    payload = {
        "LanguageCode": "EN",
        "SearchResult": {
            "SearchResultCount": 1,
            "SearchResultCountAll": 1,
            "SearchResultItems": [
                {
                    "MatchedObjectId": None,
                    "MatchedObjectDescriptor": {
                        "PositionID": "NO-DETAILS-1",
                        "PositionTitle": "Role",
                        "PositionURI": "https://x/job/1",
                        # No UserArea at all
                    },
                }
            ],
        },
    }
    item = _single_item(payload)
    job, jd, locs, cats, grades = normalise_item(item, "RID3", None)

    assert job.remote_indicator is None and job.telework_eligible is None
    assert jd.major_duties is None
    assert locs == [] and cats == [] and grades == []


def test_currency_and_int_passthrough():
    # Mixed remuneration forms; first one used
    payload = {
        "LanguageCode": "EN",
        "SearchResult": {
            "SearchResultCount": 1,
            "SearchResultCountAll": 1,
            "SearchResultItems": [
                {
                    "MatchedObjectId": "m1",
                    "MatchedObjectDescriptor": {
                        "PositionID": "PAY-1",
                        "PositionTitle": "Engineer",
                        "PositionURI": "https://x/job/pay",
                        "PositionRemuneration": [
                            {
                                "MinimumRange": 100000,
                                "MaximumRange": "$150,500",
                                "RateIntervalCode": "PH",
                            }
                        ],
                    },
                }
            ],
        },
    }
    item = _single_item(payload)
    job, *_ = normalise_item(item, "RID4", None)
    assert job.pay_min == 100000
    # 150,500 -> 150500
    assert job.pay_max == 150500
    assert job.pay_rate_interval_code == "PH"


def test_major_duties_joining_empty_safe():
    payload = {
        "LanguageCode": "EN",
        "SearchResult": {
            "SearchResultCount": 1,
            "SearchResultCountAll": 1,
            "SearchResultItems": [
                {
                    "MatchedObjectId": "m2",
                    "MatchedObjectDescriptor": {
                        "PositionID": "DUTY-1",
                        "PositionTitle": "Engineer",
                        "PositionURI": "https://x/job/duty",
                        "UserArea": {"Details": {"MajorDuties": []}},
                    },
                }
            ],
        },
    }
    item = _single_item(payload)
    _, jd, *_ = normalise_item(item, "RID5", None)
    # Empty list -> None (not blank string)
    assert jd.major_duties is None
