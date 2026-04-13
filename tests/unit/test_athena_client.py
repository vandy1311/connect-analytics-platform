"""Unit tests for lambda_tools.shared.athena_client."""

import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock boto3 before importing the module under test
sys.modules.setdefault("boto3", MagicMock())

from lambda_tools.shared.athena_client import execute_query  # noqa: E402


@patch("lambda_tools.shared.athena_client._ATHENA")
class TestExecuteQuery:
    """Tests for execute_query with mocked boto3 Athena client."""

    def test_returns_list_of_dicts(self, mock_athena):
        _setup_successful_query(mock_athena, [
            {"queue_name": "Sales", "queue_size": "12"},
        ])
        result = execute_query("SELECT * FROM connect_ctr")
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == {"queue_name": "Sales", "queue_size": "12"}

    def test_uses_workgroup_param(self, mock_athena):
        _setup_successful_query(mock_athena, [])
        execute_query("SELECT 1", workgroup="custom-wg")
        call_kwargs = mock_athena.start_query_execution.call_args[1]
        assert call_kwargs["WorkGroup"] == "custom-wg"

    def test_raises_runtime_error_on_failed_query(self, mock_athena):
        mock_athena.start_query_execution.return_value = {
            "QueryExecutionId": "qid-1"
        }
        mock_athena.get_query_execution.return_value = {
            "QueryExecution": {
                "Status": {
                    "State": "FAILED",
                    "StateChangeReason": "Syntax error",
                }
            }
        }
        with pytest.raises(RuntimeError, match="failed"):
            execute_query("BAD SQL")

    def test_raises_timeout_on_long_running_query(self, mock_athena):
        mock_athena.start_query_execution.return_value = {
            "QueryExecutionId": "qid-2"
        }
        mock_athena.get_query_execution.return_value = {
            "QueryExecution": {"Status": {"State": "RUNNING"}}
        }
        import lambda_tools.shared.athena_client as mod
        original_max = mod._MAX_WAIT
        original_poll = mod._POLL_INTERVAL
        mod._MAX_WAIT = 0.2
        mod._POLL_INTERVAL = 0.05
        try:
            with pytest.raises(TimeoutError):
                execute_query("SELECT 1")
        finally:
            mod._MAX_WAIT = original_max
            mod._POLL_INTERVAL = original_poll

    def test_multiple_rows_returned(self, mock_athena):
        _setup_successful_query(mock_athena, [
            {"id": "1", "name": "Alice"},
            {"id": "2", "name": "Bob"},
        ])
        result = execute_query("SELECT id, name FROM agents")
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"


def _setup_successful_query(mock_athena, rows: list[dict]):
    """Configure mock for a successful query returning the given rows."""
    mock_athena.start_query_execution.return_value = {
        "QueryExecutionId": "qid-ok"
    }
    mock_athena.get_query_execution.return_value = {
        "QueryExecution": {"Status": {"State": "SUCCEEDED"}}
    }
    if rows:
        columns = list(rows[0].keys())
    else:
        columns = []

    column_info = [{"Name": c} for c in columns]
    header_row = {"Data": [{"VarCharValue": c} for c in columns]}
    data_rows = [
        {"Data": [{"VarCharValue": r[c]} for c in columns]}
        for r in rows
    ]

    paginator = MagicMock()
    paginator.paginate.return_value = [
        {
            "ResultSet": {
                "ResultSetMetadata": {"ColumnInfo": column_info},
                "Rows": [header_row] + data_rows,
            }
        }
    ]
    mock_athena.get_paginator.return_value = paginator
