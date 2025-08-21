"""
This module provides utilities for interacting with AWS S3, specifically for uploading
gzipped JSON documents to a "bronze" storage layer.
"""

from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import io
import json
import os
from collections.abc import Mapping
from typing import Any

import boto3
from botocore.config import Config

BRONZE_BUCKET = os.environ.get("BRONZE_S3_BUCKET")
BRONZE_PREFIX = os.environ.get("BRONZE_S3_PREFIX", "bronze/usajobs").rstrip("/")


def s3_client():
    """
    A boto3 S3 client with custom configuration.
    """
    return boto3.client(
        "s3",
        config=Config(
            retries={
                "max_attempts": 5,
                "mode": "standard",
            },  # Configure retry behaviour with exponential backoff
            user_agent_extra="tasman-etl/bronze",
        ),
    )


def utc_now_iso() -> str:
    """
    Get the current UTC time in ISO 8601 format.

    :return: The current UTC time in ISO 8601 format.
    """
    return dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def bronze_key(run_id: str, page: int, date: dt.date | None = None) -> str:
    """
    Get the S3 key for a bronze job.

    :param run_id: The ID of the run.
    :param page: The page number.
    :param date: The date of the job.
    :return: The S3 key for the bronze job.
    """
    d = date or dt.date.today()
    return f"{BRONZE_PREFIX}/date={d:%Y/%m/%d}/run={run_id}/page={page:04d}.json.gz"


def _to_gz_bytes(doc: Mapping[str, Any]) -> bytes:
    """
    Convert a document to gzipped JSON bytes.

    Note:
        mtime=0 makes the gzip output deterministic (no timestamp), enabling reproducible builds and
        stable tests.
    :param doc: The document to convert.
    :return: The gzipped JSON bytes.
    """
    raw = json.dumps(doc, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
        gz.write(raw)
    return buf.getvalue()


def put_json_gz(key: str, doc: Mapping[str, Any]) -> dict:
    """
    Upload a gzipped JSON document to S3 with local dev fallback.

    Preflight logic:
      - If BRONZE_S3_BUCKET and AWS creds appear available -> upload to S3.
      - Else write deterministically gzipped JSON to ./bronze_local/<key> and return a stub
        response.

    This enables running the ingest end-to-end locally without exporting AWS credentials yet.

    :param key: The S3 key for the object.
    :param doc: The document to upload.
    :return: The response from the S3 put_object call.
    """
    body = _to_gz_bytes(doc)
    sha256_hex = hashlib.sha256(body).hexdigest()

    have_bucket = bool(BRONZE_BUCKET)
    # Basic heuristic: both access key & secret or a session token OR a profile (skip check).
    have_creds_env = bool(
        os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")
    ) or os.getenv("AWS_SESSION_TOKEN")

    if not (have_bucket and have_creds_env):
        # Local fallback
        root = os.path.abspath("bronze_local")
        local_path = os.path.join(root, key)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(body)
        return {
            "local_fallback": True,
            "path": local_path,
            "sha256_hex": sha256_hex,
            "reason": "missing bucket or creds",
        }

    return s3_client().put_object(
        Bucket=BRONZE_BUCKET,
        Key=key,
        Body=body,
        ContentType="application/json",
        ContentEncoding="gzip",
        ChecksumAlgorithm="SHA256",  # S3 verifies checksum on upload
        Metadata={"sha256_hex": sha256_hex},
        ServerSideEncryption="AES256",
    )
