from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import pandas as pd
from tasman_etl.models import (
    JobRecord,
)


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
