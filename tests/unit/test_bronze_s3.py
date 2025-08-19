import datetime as dt
import gzip
import hashlib
import importlib
import json
from types import ModuleType

import pytest
import tasman_etl.storage.bronze_s3 as bronze_s3


@pytest.fixture()
def bronze_env(monkeypatch) -> ModuleType:
    """Set required env vars and reload the module so globals pick them up."""
    monkeypatch.setenv("BRONZE_S3_BUCKET", "unit-test-bucket")
    # Provide a custom prefix with trailing slash to test rstrip behaviour
    monkeypatch.setenv("BRONZE_S3_PREFIX", "bronze/custom/")
    # Import / reload module after env vars set

    importlib.reload(bronze_s3)
    return bronze_s3


def test_bronze_key_with_explicit_date(bronze_env):
    d = dt.date(2025, 8, 19)
    key = bronze_env.bronze_key("RUN123", 7, date=d)
    assert key.startswith("bronze/custom/date=2025/08/19/run=RUN123/")
    assert key.endswith("page=0007.json.gz")


def test_bronze_key_defaults_today(monkeypatch, bronze_env):
    fake_today = dt.date(2030, 1, 2)
    monkeypatch.setattr(
        bronze_env.dt, "date", type("_D", (), {"today": staticmethod(lambda: fake_today)})()
    )
    key = bronze_env.bronze_key("RID", 1)
    assert "date=2030/01/02" in key


def test_to_gz_bytes_roundtrip(bronze_env):
    doc = {"a": 1, "b": "unicodé"}
    gz_bytes = bronze_env._to_gz_bytes(doc)
    # Decompress and compare JSON object
    decompressed = gzip.decompress(gz_bytes).decode("utf-8")
    # Ensure it is minified (no spaces) due to separators setting
    assert decompressed == json.dumps(doc, separators=(",", ":"), ensure_ascii=False)


def test_put_json_gz_parameters(monkeypatch, bronze_env):
    captured = {}

    class FakeS3:
        def put_object(self, **kwargs):
            captured.update(kwargs)
            return {"ETag": '"deadbeef"'}

    monkeypatch.setattr(bronze_env, "s3_client", lambda: FakeS3())
    doc = {"x": 42}
    key = bronze_env.bronze_key("RUNID", 12, date=dt.date(2024, 5, 6))
    resp = bronze_env.put_json_gz(key, doc)
    assert resp["ETag"] == '"deadbeef"'
    # Bucket / Key
    assert captured["Bucket"] == "unit-test-bucket"
    assert captured["Key"] == key
    # Gzip content & checksum
    body = captured["Body"]
    assert isinstance(body, (bytes, bytearray))
    raw = gzip.decompress(body).decode()
    assert json.loads(raw) == doc
    expected_sha = hashlib.sha256(body).hexdigest()
    assert captured["Metadata"]["sha256_hex"] == expected_sha
    # Content type & encoding
    assert captured["ContentType"] == "application/json"
    assert captured["ContentEncoding"] == "gzip"
    assert captured["ChecksumAlgorithm"] == "SHA256"
    assert captured["ServerSideEncryption"] == "AES256"


def test_utc_now_iso_format(bronze_env):
    ts = bronze_env.utc_now_iso()
    # Basic shape: 2025-08-19T12:34:56.123456Z
    assert ts.endswith("Z")
    prefix, z = ts[:-1], ts[-1]
    assert z == "Z"
    # Microseconds present
    date_part, time_part = prefix.split("T")
    assert len(time_part.split(".")) == 2
    # Parse (allow variable microsecond precision trimming trailing zeros)
    from datetime import datetime

    datetime.strptime(prefix, "%Y-%m-%dT%H:%M:%S.%f")
