from __future__ import annotations

import contextlib
import threading
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, cast

import great_expectations as gx
import pandas as pd
from tasman_etl.models import JobLocationRecord, JobRecord


@dataclass(frozen=True)
class RuleOutcome:
    name: str
    success: bool
    details: str | None = None


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    rules: list[RuleOutcome]


def _jobs_dataframe(rows: Iterable[JobRecord]) -> pd.DataFrame:
    """
    Convert a list of JobRecord objects into a Pandas DataFrame.

    :param rows: The list of JobRecord objects.
    :return: A Pandas DataFrame representing the job records.
    """

    # Derive a few helper booleans for simpler expectations
    def url_ok(urls: list[str]) -> bool:
        """
        Check if all URLs in the list are valid (i.e., start with http:// or https://).

        :param urls: The list of URLs to check.
        :return: True if all URLs are valid, False otherwise.
        """
        if not urls:
            return True
        return all(u.startswith(("http://", "https://")) for u in urls)

    def pay_pair_ok(pmin, pmax) -> bool:
        """
        Check if the pay_min and pay_max values are valid.

        :param pmin: The pay_min value.
        :param pmax: The pay_max value.
        :return: True if the pay_min is less than or equal to the pay_max, False otherwise.
        """
        if pmin is None or pmax is None:
            return True
        return pmin <= pmax

    df = pd.DataFrame(
        {
            "position_id": [r.position_id for r in rows],
            "position_title": [r.position_title for r in rows],
            "position_uri": [r.position_uri for r in rows],
            "apply_uri_ok": [url_ok(r.apply_uri) for r in rows],
            "pay_min": [r.pay_min for r in rows],
            "pay_max": [r.pay_max for r in rows],
            "pay_pair_ok": [pay_pair_ok(r.pay_min, r.pay_max) for r in rows],
            "publication_start_date": [r.publication_start_date for r in rows],
            "application_close_date": [r.application_close_date for r in rows],
        }
    )
    return df


def _has_locations(loc_rows: Iterable[JobLocationRecord]) -> bool:
    """
    Check if there are any location rows present.

    Note:
      For this pipeline, a page represents one logical set of jobs;
      we just require at least one location row overall.

    :param loc_rows: The list of JobLocationRecord objects.
    :return: True if there are location rows, False otherwise.
    """
    # Check if there are any location rows present.
    return next(iter(loc_rows), None) is not None


# Cached context instance (lazy init); keeps repeated page validations cheap in one run.
_GX_CONTEXT: Any | None = None
_GX_CONTEXT_LOCK = threading.Lock()


def _get_gx_context() -> Any:
    global _GX_CONTEXT
    if _GX_CONTEXT is not None:
        return _GX_CONTEXT
    with _GX_CONTEXT_LOCK:
        if _GX_CONTEXT is None:
            getter = getattr(gx, "get_context", None)
            if getter is None:
                from great_expectations.data_context.data_context.context_factory import (
                    get_context as _gc,
                )

                getter = _gc
            if not callable(getter):
                raise RuntimeError("Great Expectations get_context callable not found")
            try:
                _GX_CONTEXT = getter()  # optionally: getter(mode=\"ephemeral\")
            except Exception as exc:  # pragma: no cover
                raise RuntimeError("Failed to initialize Great Expectations context") from exc
    return _GX_CONTEXT


def validate_page_jobs(
    jobs: list[JobRecord],
    locations: list[JobLocationRecord],
) -> ValidationResult:
    """
    Validate a page of normalised jobs + child rows.
    Return a ValidationResult with pass/fail and rule outcomes.

    :param jobs: The list of JobRecord objects.
    :param locations: The list of JobLocationRecord objects.
    :return: A ValidationResult indicating the outcome of the validation.
    """
    rules: list[RuleOutcome] = []

    # Quick Python guard: "≥1 location exists"
    has_loc = _has_locations(locations)
    rules.append(RuleOutcome(name="has_at_least_one_location", success=has_loc))
    if not jobs:
        rules.append(RuleOutcome(name="non_empty_jobs_page", success=False, details="no jobs"))
        return ValidationResult(passed=False, rules=rules)

    df = _jobs_dataframe(jobs)

    # Obtain (or lazily create) Great Expectations Data Context via public API
    context = _get_gx_context()
    # Idempotently obtain pandas datasource (tests call multiple times in one process)
    from great_expectations.exceptions.exceptions import DataContextError as _GXDCError

    # Lightweight Protocols for static typing without ignores
    if TYPE_CHECKING:

        class _PandasDatasource(Protocol):  # pragma: no cover - typing aid
            def add_dataframe_asset(self, name: str): ...
            def get_asset(self, name: str): ...

            assets: list[Any]

        class _DataFrameAsset(Protocol):  # pragma: no cover - typing aid
            def add_batch_definition_whole_dataframe(self, name: str): ...

            batch_definitions: list[Any]

    # Obtain or fetch existing datasource
    try:
        _pandas_ds = context.data_sources.add_pandas("pandas_default")
    except _GXDCError as err:
        get_fn = getattr(context.data_sources, "get", None)
        if not callable(get_fn):
            raise RuntimeError("pandas_default datasource not found") from err
        _pandas_ds = get_fn("pandas_default")

    pandas_ds = cast("_PandasDatasource", _pandas_ds)

    # Idempotent dataframe asset
    try:
        _asset = pandas_ds.add_dataframe_asset("jobs_asset")
    except ValueError:
        get_asset_fn = getattr(pandas_ds, "get_asset", None)
        if callable(get_asset_fn):
            _asset = get_asset_fn("jobs_asset")
        else:
            _asset = next(
                a
                for a in getattr(pandas_ds, "assets", [])
                if getattr(a, "name", None) == "jobs_asset"
            )
            if _asset is None:
                raise RuntimeError(
                    "Failed to create or retrieve jobs_asset from pandas datasource assets list"
                ) from None
    asset = cast("_DataFrameAsset", _asset)

    # Idempotent batch definition retrieval/creation
    try:
        batch_def = asset.add_batch_definition_whole_dataframe("whole_df")
    except ValueError:
        existing_defs = getattr(asset, "batch_definitions", [])
        batch_def = next(
            (bd for bd in existing_defs if getattr(bd, "name", None) == "whole_df"), None
        )
    if batch_def is None:  # defensive typing guard
        raise RuntimeError("Batch definition 'whole_df' could not be resolved")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    # Old (causes type complaint):
    # validator = context.get_validator(batch=batch, expectation_suite_name="jobs_suite")

    # Use the batch_request from the fluent Batch (type-compatible with legacy API)
    # Obtain or create expectation suite lazily so tests (ephemeral context) succeed.
    from great_expectations.core.expectation_suite import ExpectationSuite
    from great_expectations.exceptions.exceptions import DataContextError

    try:
        validator = context.get_validator(
            batch_request=batch.batch_request,  # provides datasource/asset/parameters
            expectation_suite_name="jobs_suite",
        )
    except DataContextError:
        # Suite absent: create empty then retry
        with contextlib.suppress(Exception):
            context.suites.add(ExpectationSuite(name="jobs_suite"))
        validator = context.get_validator(
            batch_request=batch.batch_request,
            expectation_suite_name="jobs_suite",
        )
    validator.expect_column_values_to_not_be_null("position_id")
    validator.expect_column_values_to_not_be_null("position_title")
    validator.expect_column_values_to_match_regex("position_uri", r"^https?://")
    validator.expect_column_values_to_be_between("pay_min", min_value=0, mostly=1.0)
    validator.expect_column_values_to_be_between("pay_max", min_value=0, mostly=1.0)
    validator.expect_column_values_to_be_in_set("apply_uri_ok", value_set=[True])
    validator.expect_column_values_to_be_in_set("pay_pair_ok", value_set=[True])

    # Run validation directly (no ValidationDefinition / Checkpoint abstraction)
    suite = validator.get_expectation_suite()
    # (Optional) persist suite in context if there's a need to reuse
    try:  # prefer unified method
        context.suites.add_or_update(suite)
    except AttributeError:
        # Fallback to add(); ignore if even that is unsupported
        with contextlib.suppress(AttributeError):
            context.suites.add(suite)

    validation_result = validator.validate()
    # Help static type checker
    from great_expectations.core.expectation_validation_result import (
        ExpectationSuiteValidationResult,
    )

    assert isinstance(
        validation_result, ExpectationSuiteValidationResult
    ), f"Unexpected validation result type: {type(validation_result)}"

    gx_pass = validation_result.success
    for evr in validation_result.results:
        cfg = getattr(evr, "expectation_config", None)

        if isinstance(cfg, dict):
            exp_type = cfg.get("expectation_type") or cfg.get("type") or "<unknown>"
        else:
            # ExpectationConfiguration object or None
            exp_type = (
                getattr(cfg, "expectation_type", None)
                or getattr(cfg, "type", None)
                or type(evr).__name__
            )

        unexpected = None
        r = getattr(evr, "result", None)
        if isinstance(r, dict):
            unexpected = r.get("unexpected_count")

        rules.append(
            RuleOutcome(
                name=exp_type,
                success=getattr(evr, "success", False),
                details=None if getattr(evr, "success", False) else str(unexpected),
            )
        )

    passed = has_loc and gx_pass
    return ValidationResult(passed=passed, rules=rules)
