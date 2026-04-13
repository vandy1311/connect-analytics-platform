"""Athena query execution wrapper with result polling and timeout handling."""

import os
import time

import boto3


_ATHENA = boto3.client("athena")

_WORKGROUP = os.environ.get("WORKGROUP", "connect-analytics")
_BUCKET = os.environ.get("BUCKET", "connect-analytics-demo")
_OUTPUT_LOCATION = f"s3://{_BUCKET}/athena-results/"

_POLL_INTERVAL = 0.5  # seconds between status checks
_MAX_WAIT = 30  # seconds before timeout


def execute_query(query: str, workgroup: str | None = None) -> list[dict]:
    """Execute an Athena SQL query and return results as a list of dicts.

    Args:
        query: SQL query string to execute.
        workgroup: Athena workgroup name. Defaults to WORKGROUP env var.

    Returns:
        List of dicts mapping column names to string values.

    Raises:
        TimeoutError: If query does not complete within 30 seconds.
        RuntimeError: If query execution fails.
    """
    wg = workgroup or _WORKGROUP

    response = _ATHENA.start_query_execution(
        QueryString=query,
        WorkGroup=wg,
        ResultConfiguration={"OutputLocation": _OUTPUT_LOCATION},
    )
    query_execution_id = response["QueryExecutionId"]

    # Poll for completion
    elapsed = 0.0
    while elapsed < _MAX_WAIT:
        status_resp = _ATHENA.get_query_execution(
            QueryExecutionId=query_execution_id
        )
        state = status_resp["QueryExecution"]["Status"]["State"]

        if state == "SUCCEEDED":
            return _fetch_results(query_execution_id)
        if state in ("FAILED", "CANCELLED"):
            reason = status_resp["QueryExecution"]["Status"].get(
                "StateChangeReason", "Unknown error"
            )
            raise RuntimeError(f"Athena query {state.lower()}: {reason}")

        time.sleep(_POLL_INTERVAL)
        elapsed += _POLL_INTERVAL

    raise TimeoutError(
        f"Athena query did not complete within {_MAX_WAIT}s "
        f"(execution_id={query_execution_id})"
    )


def _fetch_results(query_execution_id: str) -> list[dict]:
    """Fetch all result rows for a completed query execution."""
    rows: list[dict] = []
    paginator = _ATHENA.get_paginator("get_query_results")

    for page in paginator.paginate(QueryExecutionId=query_execution_id):
        result_set = page["ResultSet"]
        columns = [
            col["Name"] for col in result_set["ResultSetMetadata"]["ColumnInfo"]
        ]

        for i, row in enumerate(result_set["Rows"]):
            # First row of the first page is the header row — skip it
            if i == 0 and not rows:
                continue
            values = [field.get("VarCharValue", "") for field in row["Data"]]
            rows.append(dict(zip(columns, values)))

    return rows
