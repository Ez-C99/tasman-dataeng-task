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
