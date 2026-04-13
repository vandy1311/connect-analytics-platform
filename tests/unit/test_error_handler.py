"""Unit tests for lambda_tools.shared.error_handler."""

import uuid

from lambda_tools.shared.error_handler import sanitize_error


class TestSanitizeError:
    """Tests for sanitize_error function."""

    def test_returns_dict_with_required_keys(self):
        result = sanitize_error(Exception("something broke"))
        assert "error" in result
        assert "correlation_id" in result

    def test_correlation_id_is_valid_uuid(self):
        result = sanitize_error(Exception("oops"))
        uuid.UUID(result["correlation_id"])  # raises if invalid

    def test_strips_sql_select(self):
        err = Exception("Error in SELECT * FROM connect_ctr WHERE queue='Sales'")
        result = sanitize_error(err)
        msg = result["error"].upper()
        assert "SELECT" not in msg
        assert "FROM" not in msg
        assert "WHERE" not in msg

    def test_strips_table_names(self):
        err = Exception("Table connect_ctr not found, also connect_agent_events")
        result = sanitize_error(err)
        assert "connect_ctr" not in result["error"]
        assert "connect_agent_events" not in result["error"]

    def test_strips_contact_lens_table(self):
        err = Exception("connect_contact_lens partition missing")
        result = sanitize_error(err)
        assert "connect_contact_lens" not in result["error"]

    def test_strips_python_traceback(self):
        tb = (
            "Traceback (most recent call last):\n"
            '  File "handler.py", line 10, in handler\n'
            "    raise ValueError('bad')\n"
            "ValueError: bad"
        )
        result = sanitize_error(Exception(tb))
        assert "Traceback" not in result["error"]
        assert "handler.py" not in result["error"]

    def test_strips_java_stack_trace(self):
        err = Exception("at com.amazonaws.athena.QueryExecutor(QueryExecutor.java:42)")
        result = sanitize_error(err)
        assert "com.amazonaws" not in result["error"]

    def test_strips_arn(self):
        err = Exception(
            "Access denied for arn:aws:iam::123456789012:role/MyRole"
        )
        result = sanitize_error(err)
        assert "arn:aws" not in result["error"]
        assert "123456789012" not in result["error"]

    def test_strips_account_id(self):
        err = Exception("Account 123456789012 not authorized")
        result = sanitize_error(err)
        assert "123456789012" not in result["error"]

    def test_generic_message_on_empty_sanitization(self):
        # An error that is entirely SQL keywords should produce a fallback
        err = Exception("SELECT FROM WHERE")
        result = sanitize_error(err)
        assert len(result["error"]) > 0

    def test_preserves_safe_content(self):
        err = Exception("Query timed out after 30 seconds")
        result = sanitize_error(err)
        assert "timed out" in result["error"]

    def test_strips_join_keyword(self):
        err = Exception("Error in JOIN clause on connect_ctr")
        result = sanitize_error(err)
        msg = result["error"].upper()
        assert "JOIN" not in msg
