from __future__ import annotations

from tasman_etl.dq.gx.validate import validate_page_jobs
from tasman_etl.models import JobLocationRecord, JobRecord


def _make_job(
    position_id: str = "123",
    position_title: str = "Data Engineer",
    position_uri: str = "https://example.com/job/123",
    apply_uri: list[str] | None = None,
    pay_min: int | None = 100,
    pay_max: int | None = 200,
) -> JobRecord:
    return JobRecord(
        position_id=position_id,
        position_title=position_title,
        position_uri=position_uri,
        apply_uri=apply_uri or ["https://apply.example.com/123"],
        pay_min=pay_min,
        pay_max=pay_max,
        raw_json={"PositionID": position_id},
    )


def test_validate_happy_path():
    job = _make_job()
    loc = JobLocationRecord(loc_idx=0, city_name="Chicago")
    result = validate_page_jobs([job], [loc])

    # Should pass overall
    assert result.passed is True
    # All rules (apart from location guard) should be successful
    failing = [r for r in result.rules if not r.success]
    assert not failing, f"Expected no failing rules, got: {failing}"
    assert any(r.name == "has_at_least_one_location" for r in result.rules)


def test_validate_empty_jobs_page_fails():
    loc = JobLocationRecord(loc_idx=0, city_name="Chicago")
    result = validate_page_jobs([], [loc])
    assert result.passed is False
    # Expect the non_empty_jobs_page rule to be present and failing
    names = {r.name: r for r in result.rules}
    assert "non_empty_jobs_page" in names
    assert names["non_empty_jobs_page"].success is False


def test_validate_missing_locations_fails():
    job = _make_job()
    result = validate_page_jobs([job], [])
    assert result.passed is False
    # Location guard should fail, but expectations should still have run and succeeded
    loc_rule = next(r for r in result.rules if r.name == "has_at_least_one_location")
    assert loc_rule.success is False
    # Ensure at least one expectation rule is present and successful
    assert any(
        r.name.startswith("expect_") and r.success for r in result.rules
    ), "Expectation rules missing or unsuccessful"


def test_validate_expectation_failures():
    # Create a job that will fail several expectations:
    # - invalid position_uri (regex fail)
    # - negative pay_min (between fail)
    # - invalid apply_uri scheme (apply_uri_ok False)
    job = _make_job(
        position_id="bad1",
        position_title="Bad Job",
        position_uri="ftp://not-http",  # fails regex ^https?://
        apply_uri=["ftp://apply.invalid/123"],  # url_ok -> False
        pay_min=-10,  # below 0
        pay_max=0,
    )
    loc = JobLocationRecord(loc_idx=0, city_name="Chicago")
    result = validate_page_jobs([job], [loc])

    assert result.passed is False
    failing_expectations = [
        r for r in result.rules if r.name.startswith("expect_") and not r.success
    ]
    # We expect at least two different expectation types to fail (regex + between or in_set)
    assert len(failing_expectations) >= 2, failing_expectations
    # Sanity: location rule should succeed
    loc_rule = next(r for r in result.rules if r.name == "has_at_least_one_location")
    assert loc_rule.success is True
