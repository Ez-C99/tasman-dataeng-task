from tasman_etl.storage.bronze_s3 import bronze_key, put_json_gz, utc_now_iso


def persist_raw_page(run_id: str, page: int, request_dict: dict, response_dict: dict) -> str:
    """
    Persist a raw page of data to S3.

    :param run_id: The ID of the run.
    :param page: The page number.
    :param request_dict: The request metadata.
    :param response_dict: The response payload.
    :return: The S3 key for the bronze job.
    """
    envelope = {
        "request": {**request_dict, "sent_at": request_dict.get("sent_at", utc_now_iso())},
        "response": {
            "status": response_dict.get("status", 200),
            "headers": response_dict.get("headers", {}),
            "received_at": utc_now_iso(),
            "payload": response_dict["payload"],
        },
        "ingest": {"ingest_run_id": run_id},
    }
    key = bronze_key(run_id, page)
    put_json_gz(key, envelope)
    return key
