"""Tests for lambda_tools/shared/auth.py — authentication and RBAC."""

import json
import os
import unittest
from unittest.mock import patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lambda_tools.shared import auth


class TestAuthenticate(unittest.TestCase):
    def setUp(self):
        auth._TOKEN_STORE = None  # Reset cached store

    def test_valid_supervisor_token(self):
        result = auth.authenticate("demo-supervisor-token")
        self.assertTrue(result["authenticated"])
        self.assertEqual(result["user_id"], "supervisor-001")
        self.assertEqual(result["role"], "supervisor")

    def test_valid_qa_token(self):
        result = auth.authenticate("demo-qa-token")
        self.assertTrue(result["authenticated"])
        self.assertEqual(result["role"], "qa_analyst")

    def test_valid_wfm_token(self):
        result = auth.authenticate("demo-wfm-token")
        self.assertTrue(result["authenticated"])
        self.assertEqual(result["role"], "wfm_planner")

    def test_none_token_rejected(self):
        result = auth.authenticate(None)
        self.assertFalse(result["authenticated"])
        self.assertEqual(result["status_code"], 401)

    def test_empty_token_rejected(self):
        result = auth.authenticate("")
        self.assertFalse(result["authenticated"])
        self.assertEqual(result["status_code"], 401)

    def test_invalid_token_rejected(self):
        result = auth.authenticate("bogus-token-xyz")
        self.assertFalse(result["authenticated"])
        self.assertEqual(result["status_code"], 401)

    @patch.dict(os.environ, {"AUTH_TOKENS": json.dumps({
        "custom-token": {"user_id": "custom-user", "role": "supervisor"}
    })})
    def test_custom_tokens_from_env(self):
        auth._TOKEN_STORE = None
        result = auth.authenticate("custom-token")
        self.assertTrue(result["authenticated"])
        self.assertEqual(result["user_id"], "custom-user")

    @patch.dict(os.environ, {"AUTH_TOKENS": "not-valid-json"})
    def test_invalid_json_falls_back_to_defaults(self):
        auth._TOKEN_STORE = None
        result = auth.authenticate("demo-supervisor-token")
        self.assertTrue(result["authenticated"])


class TestAuthorize(unittest.TestCase):
    def test_supervisor_allowed(self):
        result = auth.authorize("supervisor", "Supervisor_Agent")
        self.assertTrue(result["authorized"])

    def test_qa_allowed(self):
        result = auth.authorize("qa_analyst", "Quality_Agent")
        self.assertTrue(result["authorized"])

    def test_wfm_allowed(self):
        result = auth.authorize("wfm_planner", "WFM_Agent")
        self.assertTrue(result["authorized"])

    def test_cross_role_denied(self):
        result = auth.authorize("qa_analyst", "WFM_Agent")
        self.assertFalse(result["authorized"])
        self.assertEqual(result["status_code"], 403)

    def test_unknown_role_denied(self):
        result = auth.authorize("unknown_role", "Supervisor_Agent")
        self.assertFalse(result["authorized"])
        self.assertEqual(result["status_code"], 403)


class TestAuthGate(unittest.TestCase):
    def setUp(self):
        auth._TOKEN_STORE = None

    def test_valid_token_matching_agent(self):
        result = auth.auth_gate("demo-supervisor-token", "Supervisor_Agent")
        self.assertTrue(result["allowed"])
        self.assertEqual(result["user_id"], "supervisor-001")
        self.assertEqual(result["role"], "supervisor")

    def test_no_token(self):
        result = auth.auth_gate(None, "Supervisor_Agent")
        self.assertFalse(result["allowed"])
        self.assertEqual(result["status_code"], 401)

    def test_invalid_token(self):
        result = auth.auth_gate("bad-token", "Supervisor_Agent")
        self.assertFalse(result["allowed"])
        self.assertEqual(result["status_code"], 401)

    def test_valid_token_wrong_agent(self):
        result = auth.auth_gate("demo-qa-token", "WFM_Agent")
        self.assertFalse(result["allowed"])
        self.assertEqual(result["status_code"], 403)


if __name__ == "__main__":
    unittest.main()
