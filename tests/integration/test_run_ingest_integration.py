from __future__ import annotations

import os

import psycopg
import pytest
from tasman_etl.runner import run as run_mod

DB_URL = os.getenv("DB_URL", "postgresql://postgres:localpw@localhost:5432/usajobs")


class _StubClient:
    def __init__(self, position_id: str):
        self.position_id = position_id

    def fetch_search_page(self, **kwargs):  # same shape as real client output
        payload = {
            "LanguageCode": "EN",
            "SearchResult": {
                "SearchResultCount": 1,
                "SearchResultCountAll": 1,
                "SearchResultItems": [
                    {
                        "MatchedObjectId": f"MO-{self.position_id}",
                        "MatchedObjectDescriptor": {
                            "PositionID": self.position_id,
                            "PositionTitle": "Integration Engineer",
                            "PositionURI": f"https://example/job/{self.position_id}",
                            "PositionLocation": [
                                {"LocationName": "New York", "CityName": "New York"}
                            ],
                            "JobCategory": [{"Code": "2210", "Name": "IT"}],
                            "JobGrade": [{"Code": "13"}],
                        },
                    }
                ],
            },
        }
        request_dict = {"endpoint": "/api/search", "params": kwargs}
        response_dict = {"status": 200, "headers": {}, "payload": payload}
        return request_dict, response_dict


@pytest.fixture()
def patch_client(monkeypatch):
    def _factory(position_id: str):
        stub = _StubClient(position_id)
        monkeypatch.setattr(run_mod, "UsaJobsClient", lambda: stub)
        return stub

    return _factory


@pytest.fixture(autouse=True)
def mock_bronze(monkeypatch):
    # Avoid real S3 interaction
    store = {}

    def _fake_put_json_gz(key: str, doc):
        store[key] = doc
        return {"mocked": True}

    monkeypatch.setattr(run_mod, "put_json_gz", _fake_put_json_gz)
    return store


@pytest.fixture(autouse=True)
def fast_validate(monkeypatch):
    def _validate(jobs, locs):
        return type("R", (), {"passed": True, "rules": []})()

    monkeypatch.setattr(run_mod, "validate_page_jobs", _validate)


@pytest.mark.integration
@pytest.mark.parametrize("pid", ["INT-1001", "INT-1002"])
def test_ingest_search_page_integration_roundtrip(pid, patch_client):
    patch_client(pid)
    stats = run_mod.ingest_search_page(
        run_id="int-run",
        page=1,
        keyword="data",
        location_name=None,
        radius_miles=None,
        results_per_page=25,
        fields=None,
    )
    assert stats["jobs"] == 1

    # Verify DB row exists
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute("SELECT position_title FROM job WHERE position_id = %s", (pid,))
        row = cur.fetchone()
        assert row is not None, "Job not persisted"
        assert "Engineer" in row[0]


@pytest.mark.integration
def test_ingest_search_page_idempotent(patch_client):
    pid = "INT-IDEMP-1"
    patch_client(pid)
    run_mod.ingest_search_page(
        run_id="idemp-run",
        page=1,
        keyword="data",
        location_name=None,
        radius_miles=None,
    )

    # Second ingest with modified title through new stub instance (simulate changed upstream)
    class _StubClient2(_StubClient):
        def fetch_search_page(self, **kwargs):
            request_dict, response_dict = super().fetch_search_page(**kwargs)
            response_dict["payload"]["SearchResult"]["SearchResultItems"][0][
                "MatchedObjectDescriptor"
            ]["PositionTitle"] = "Integration Engineer Senior"
            return request_dict, response_dict

    stub2 = _StubClient2(pid)
    # Rebind to new stub2
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(run_mod, "UsaJobsClient", lambda: stub2)
    run_mod.ingest_search_page(
        run_id="idemp-run",
        page=1,
        keyword="data",
        location_name=None,
        radius_miles=None,
    )

    # Confirm still single row, updated title
    with psycopg.connect(DB_URL) as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*), max(position_title) FROM job WHERE position_id = %s", (pid,))
        row = cur.fetchone()
        assert row is not None
        assert row[0] == 1
        assert "Senior" in row[1]
