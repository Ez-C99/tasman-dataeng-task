from __future__ import annotations

import types
from typing import Any

import pytest

# Target module under test
from tasman_etl.runner import run as run_mod


class _StubClient:
    def __init__(self):
        self.calls: list[dict[str, Any]] = []

    def fetch_search_page(self, **kwargs):  # signature used in run.ingest_search_page
        self.calls.append(kwargs)
        # Minimal valid API payload matching ApiResponse schema
        payload = {
            "LanguageCode": "EN",
            "SearchResult": {
                "SearchResultCount": 1,
                "SearchResultCountAll": 1,
                "SearchResultItems": [
                    {
                        "MatchedObjectId": "M1",
                        "MatchedObjectDescriptor": {
                            "PositionID": "PID-UNIT-1",
                            "PositionTitle": "Data Engineer",
                            "PositionURI": "https://example/job/1",
                            "PositionLocation": [
                                {"LocationName": "Chicago", "CityName": "Chicago"}
                            ],
                            "JobCategory": [{"Code": "2210", "Name": "IT"}],
                            "JobGrade": [{"Code": "12"}],
                        },
                    }
                ],
            },
        }
        request_dict = {"endpoint": "/api/search", "params": kwargs}
        response_dict = {"status": 200, "headers": {}, "payload": payload}
        return request_dict, response_dict


# (Unused placeholder previously for validator results; removed for clarity.)


def _patch(monkeypatch, name: str, obj):
    monkeypatch.setattr(run_mod, name, obj)


@pytest.fixture()
def stub_client(monkeypatch):
    sc = _StubClient()
    # Patch class name used inside ingest_search_page
    monkeypatch.setattr(run_mod, "UsaJobsClient", lambda: sc)
    return sc


@pytest.fixture()
def capture_bronze(monkeypatch):
    store: dict[str, Any] = {}

    def _fake_put(key: str, doc):  # emulate side effect capture
        store[key] = doc
        return {"mocked": True}

    _patch(monkeypatch, "put_json_gz", _fake_put)
    return store


@pytest.fixture()
def fake_upsert(monkeypatch):
    calls: list[Any] = []

    def _fake_upsert(conn, bundle, **kwargs):
        calls.append(bundle)
        return 42  # stable fake job_id

    _patch(monkeypatch, "upsert_page", _fake_upsert)
    return calls


@pytest.fixture()
def fake_validate(monkeypatch):
    state = {"passed": True}

    def _fake_validate(jobs, locs):
        return types.SimpleNamespace(passed=state["passed"], rules=[])

    _patch(monkeypatch, "validate_page_jobs", _fake_validate)
    return state


@pytest.fixture(autouse=True)
def stub_engine(monkeypatch):
    """Provide a stub engine so unit tests don't open real DB connections."""

    class _StubConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):  # noqa: D401
            return False  # don't suppress

    class _StubEngine:
        def connect(self, **kwargs):  # signature compatibility
            return _StubConn()

    monkeypatch.setattr(run_mod, "engine", _StubEngine())


def test_ingest_search_page_happy(stub_client, capture_bronze, fake_upsert, fake_validate):
    stats = run_mod.ingest_search_page(
        run_id="rid-1",
        page=1,
        keyword="data",
        location_name=None,
        radius_miles=None,
        results_per_page=50,
        fields=None,
    )
    assert stats["jobs"] == 1
    assert stats["locations"] == 1
    assert stats["categories"] == 1
    assert stats["grades"] == 1
    assert len(fake_upsert) == 1
    assert stub_client.calls, "Client should have been invoked"
    assert any(key.endswith("page=0001.json.gz") for key in capture_bronze)


def test_ingest_search_page_dq_gate_blocks(stub_client, capture_bronze, fake_upsert, fake_validate):
    fake_validate["passed"] = False
    with pytest.raises(RuntimeError):
        run_mod.ingest_search_page(
            run_id="rid-2",
            page=1,
            keyword="data",
            location_name=None,
            radius_miles=None,
            dq_enforce=True,  # force gate on
        )
    # ensure we did not persist to DB (no upsert) when gate failed
    assert not fake_upsert, "Upsert should not have occurred on failed DQ gate"


def test_ingest_search_page_dq_gate_disabled(
    stub_client, capture_bronze, fake_upsert, fake_validate
):
    fake_validate["passed"] = False
    stats = run_mod.ingest_search_page(
        run_id="rid-3",
        page=1,
        keyword="data",
        location_name=None,
        radius_miles=None,
        dq_enforce=False,  # disable gate explicitly
    )
    # Should still load
    assert stats["jobs"] == 1
    assert fake_upsert, "Upsert should have occurred with gate disabled"
