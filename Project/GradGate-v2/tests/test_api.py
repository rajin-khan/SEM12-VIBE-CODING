"""API integration tests using FastAPI TestClient in TEST_MODE.

These tests do NOT need a real Supabase connection — they mock the DB layer
and run with TEST_MODE=true to bypass JWT validation.
"""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Force TEST_MODE before importing the app so auth is bypassed
os.environ["TEST_MODE"] = "true"
os.environ.setdefault("SUPABASE_URL", "https://mock.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "mock-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "mock-secret")

from api.main import app  # noqa: E402 (must be after env setup)

TESTS_DIR = Path(__file__).resolve().parent
TC01 = TESTS_DIR / "tc01_cse_all_pass.csv"
TC02 = TESTS_DIR / "tc02_bba_all_pass.csv"

client = TestClient(app)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _mock_supabase_insert(scan_id: str = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"):
    """Return a mock Supabase client that records inserts and returns empty selects."""
    mock = MagicMock()
    # insert chain: .table().insert().execute()
    mock.table.return_value.insert.return_value.execute.return_value.data = [{"id": scan_id}]
    # select chain for list: .table().select().eq().order().execute()
    mock.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = []
    # select chain for get: .table().select().eq().eq().execute()
    mock.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
    return mock


AUDIT_MOCK = "api.routers.audit.get_supabase"
HISTORY_MOCK = "api.routers.history.get_supabase"


# ── Health ────────────────────────────────────────────────────────────────────

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── Audit ─────────────────────────────────────────────────────────────────────

@pytest.mark.skipif(not TC01.exists(), reason="tc01 fixture missing")
def test_audit_csv_cse():
    """POST /audit/csv with a valid CSE transcript should return 200 + audit result."""
    with patch(AUDIT_MOCK, return_value=_mock_supabase_insert()):
        with open(TC01, "rb") as f:
            resp = client.post(
                "/audit/csv",
                files={"file": ("tc01_cse_all_pass.csv", f, "text/csv")},
                data={"program": "CSE"},
                headers={"Authorization": "Bearer test-token"},
            )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "scan_id" in body
    assert body["program"] == "CSE"
    assert body["input_type"] == "csv"
    result = body["result"]
    assert result["credits"]["total_earned"] > 0
    assert "audit" in result
    assert "cgpa" in result


@pytest.mark.skipif(not TC02.exists(), reason="tc02 fixture missing")
def test_audit_csv_bba():
    """POST /audit/csv with a valid BBA transcript should return 200."""
    with patch(AUDIT_MOCK, return_value=_mock_supabase_insert()):
        with open(TC02, "rb") as f:
            resp = client.post(
                "/audit/csv",
                files={"file": ("tc02_bba_all_pass.csv", f, "text/csv")},
                data={"program": "BBA"},
                headers={"Authorization": "Bearer test-token"},
            )

    assert resp.status_code == 200, resp.text


def test_audit_csv_invalid_program():
    """POST /audit/csv with a bad program should return 422."""
    dummy_csv = b"Course_Code,Credits,Grade,Semester\nCSE115,3,A,Spring 2023\n"
    with patch(AUDIT_MOCK, return_value=_mock_supabase_insert()):
        resp = client.post(
            "/audit/csv",
            files={"file": ("t.csv", io.BytesIO(dummy_csv), "text/csv")},
            data={"program": "INVALID"},
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status_code == 422


def test_audit_csv_not_csv():
    """POST /audit/csv with a non-.csv file should return 400."""
    resp = client.post(
        "/audit/csv",
        files={"file": ("transcript.txt", io.BytesIO(b"hello"), "text/plain")},
        data={"program": "CSE"},
        headers={"Authorization": "Bearer test-token"},
    )
    assert resp.status_code == 400


def test_audit_image_rejects_bad_extension():
    """POST /audit/image with unsupported file type should return 400."""
    resp = client.post(
        "/audit/image",
        files={"file": ("transcript.txt", io.BytesIO(b"hello"), "text/plain")},
        data={"program": "CSE"},
        headers={"Authorization": "Bearer test-token"},
    )
    assert resp.status_code == 400


# ── History ───────────────────────────────────────────────────────────────────

def test_list_history_empty():
    """GET /history with no scans should return empty list."""
    with patch(HISTORY_MOCK, return_value=_mock_supabase_insert()):
        resp = client.get("/history", headers={"Authorization": "Bearer test-token"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_scan_not_found():
    """GET /history/{id} for unknown scan should return 404."""
    with patch(HISTORY_MOCK, return_value=_mock_supabase_insert()):
        resp = client.get(
            "/history/00000000-0000-0000-0000-000000000099",
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status_code == 404


def test_no_auth():
    """Routes without Authorization header should return 403."""
    resp = client.get("/history")
    assert resp.status_code in (401, 403)
