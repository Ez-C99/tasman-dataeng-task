"""Great Expectations smoke test.

This is a lightweight end-to-end style check that the validation layer
can be invoked in a production-like manner and all current expectations pass
for a minimal, representative job record.
"""

import logging
from datetime import UTC, datetime

from tasman_etl.dq.gx.validate import validate_page_jobs
from tasman_etl.models import JobLocationRecord, JobRecord


def test_dq_smoke() -> None:
    jobs = [
        JobRecord(
            position_id="GX-SMOKE-1",
            position_uri="https://example.com/job/1",
            position_title="Data Engineer",
            apply_uri=["https://example.com/apply"],
            pay_min=90_000,
            pay_max=120_000,
            publication_start_date=datetime.now(UTC),
            raw_json={"smoke": True},
        )
    ]
    locs = [JobLocationRecord(loc_idx=0, city_name="Chicago")]

    res = validate_page_jobs(jobs, locs)

    # Verbose human-readable summary via logging (dq.smoke logger configured in conftest)
    log = logging.getLogger("dq.smoke")
    log.info("Great Expectations passed: %s", res.passed)
    for r in res.rules:
        status = "OK" if r.success else "FAIL"
        detail = "" if r.success else f" ({r.details})"
        log.info("- %s: %s%s", r.name, status, detail)

    # Overall gate should pass
    assert res.passed, "Smoke validation failed: overall gate did not pass"

    # All individual expectations should have succeeded
    failed = [r for r in res.rules if not r.success]
    assert not failed, f"Some expectations failed: {[f.name for f in failed]}"

    # Optional: sanity check on rule names remaining stable (helps detect silent drops)
    expected_rule_prefixes = {
        "has_at_least_one_location",
        "expect_column_values_to_not_be_null",
        "expect_column_values_to_match_regex",
        "expect_column_values_to_be_between",
        "expect_column_values_to_be_in_set",
    }
    observed = {r.name for r in res.rules}
    assert (
        observed & expected_rule_prefixes
    ), "Expected at least one known expectation; got none of the expected names"
