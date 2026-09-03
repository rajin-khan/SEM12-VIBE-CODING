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
from api.services.ocr import OCRDependencyError  # noqa: E402

TESTS_DIR = Path(__file__).resolve().parent
TC01 = TESTS_DIR / "happy_cse_default.csv"
TC02 = TESTS_DIR / "happy_bba_finance.csv"
WAIVER_FIXTURE = TESTS_DIR / "waiver_cse_both.csv"

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


def test_audit_options():
    resp = client.get("/audit/options")
    assert resp.status_code == 200
    body = resp.json()
    assert any(program["value"] == "CSE" for program in body["programs"])
    assert any(level["value"] == "all" for level in body["levels"])
    assert "normal" in body["report_modes"]


def test_ocr_status():
    resp = client.get("/audit/ocr-status")
    assert resp.status_code == 200
    body = resp.json()
    assert "ready" in body
    assert "dependencies" in body
    assert "messages" in body
    assert "supported_extensions" in body
    assert "extraction_modes" in body


# ── Audit ─────────────────────────────────────────────────────────────────────

@pytest.mark.skipif(not TC01.exists(), reason="tc01 fixture missing")
def test_audit_csv_cse():
    """POST /audit/csv with a valid CSE transcript should return 200 + audit result."""
    with patch(AUDIT_MOCK, return_value=_mock_supabase_insert()):
        with open(TC01, "rb") as f:
            resp = client.post(
                "/audit/csv",
                files={"file": ("happy_cse_default.csv", f, "text/csv")},
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
    assert "course_statuses" in result["credits"]
    assert result["metadata"]["requested_level"] == "all"


@pytest.mark.skipif(not WAIVER_FIXTURE.exists(), reason="waiver fixture missing")
def test_audit_csv_with_cli_options():
    with patch(AUDIT_MOCK, return_value=_mock_supabase_insert()):
        with open(WAIVER_FIXTURE, "rb") as f:
            resp = client.post(
                "/audit/csv",
                files={"file": ("waiver_cse_both.csv", f, "text/csv")},
                data={
                    "program": "CSE",
                    "level": "2",
                    "waivers": "ENG102,MAT112,INVALID100",
                    "report": "full",
                    "minor": "MATH",
                },
                headers={"Authorization": "Bearer test-token"},
            )

    assert resp.status_code == 200, resp.text
    result = resp.json()["result"]
    assert result["metadata"]["requested_level"] == "2"
    assert result["metadata"]["report_mode"] == "full"
    assert result["waivers_applied"] == ["ENG102", "MAT112"]
    assert "course_statuses" in result["credits"]
    assert len(result["cgpa"]["semesters"]) > 0


@pytest.mark.skipif(not TC02.exists(), reason="tc02 fixture missing")
def test_audit_csv_bba():
    """POST /audit/csv with a valid BBA transcript should return 200."""
    with patch(AUDIT_MOCK, return_value=_mock_supabase_insert()):
        with open(TC02, "rb") as f:
            resp = client.post(
                "/audit/csv",
                files={"file": ("happy_bba_finance.csv", f, "text/csv")},
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


def test_audit_image_pdf_with_cli_options():
    extraction = MagicMock()
    extraction.input_type = "pdf"
    extraction.extracted_csv = "Course_Code,Credits,Grade,Semester\n"
    extraction.review_required = False
    extraction.metadata.return_value = {
        "input_type": "pdf",
        "extraction_mode": "pdf_text",
        "warnings": [],
        "pages_processed": 1,
        "rows_detected": 2,
        "review_required": False,
    }
    mocked_result = {
        "program": "Computer Science & Engineering",
        "program_alias": "CSE",
        "metadata": {
            "requested_level": "3",
            "requested_level_label": "Level 3 — Full Audit",
            "report_mode": "full",
            "selected_concentration": None,
            "selected_minor": "MATH",
            "program_alias": "CSE",
        },
        "non_nsu_courses_flagged": [],
        "waivers_applied": ["ENG102"],
        "credits": {"total_earned": 130, "course_statuses": []},
        "cgpa": {"final": 3.5, "semesters": []},
        "grade_distribution": {},
        "audit": {"eligible": True, "reasons": [], "roadmap": []},
    }

    with patch("api.routers.audit.extract_transcript_document", return_value=extraction):
        with patch("api.routers.audit._run_engine", return_value=mocked_result) as run_engine:
            with patch(AUDIT_MOCK, return_value=_mock_supabase_insert()):
                resp = client.post(
                    "/audit/image",
                    files={"file": ("transcript.pdf", io.BytesIO(b"%PDF"), "application/pdf")},
                    data={
                        "program": "CSE",
                        "level": "3",
                        "waivers": "ENG102",
                        "report": "full",
                        "minor": "MATH",
                    },
                    headers={"Authorization": "Bearer test-token"},
                )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["program"] == "CSE"
    assert body["input_type"] == "pdf"
    assert body["status"] == "audited"
    assert body["result"]["metadata"]["requested_level"] == "3"
    assert body["result"]["metadata"]["report_mode"] == "full"
    assert body["result"]["metadata"]["extraction"]["extraction_mode"] == "pdf_text"
    assert body["result"]["waivers_applied"] == ["ENG102"]
    run_engine.assert_called_once()
    assert run_engine.call_args.kwargs["level"] == "3"
    assert run_engine.call_args.kwargs["report"] == "full"
    assert run_engine.call_args.kwargs["minor"] == "MATH"


def test_audit_image_dependency_failure_returns_503():
    with patch(
        "api.routers.audit.extract_transcript_document",
        side_effect=OCRDependencyError("Image OCR is not available on this machine."),
    ):
        resp = client.post(
            "/audit/image",
            files={"file": ("transcript.png", io.BytesIO(b"fake"), "image/png")},
            data={"program": "CSE"},
            headers={"Authorization": "Bearer test-token"},
        )

    assert resp.status_code == 503
    detail = resp.json()["detail"]
    assert "message" in detail
    assert "ocr_status" in detail


def test_audit_image_review_required_response():
    extraction = MagicMock()
    extraction.input_type = "image"
    extraction.review_required = True
    extraction.review_payload.return_value = {
        "input_type": "image",
        "extraction_mode": "image_ocr",
        "review_required": True,
        "warnings": ["OCR confidence is lower than ideal; please review extracted rows."],
        "pages_processed": 1,
        "rows_detected": 1,
        "extracted_preview_rows": [
            {
                "course_code": "ENG102",
                "credits": "3",
                "grade": "A-",
                "semester": "Spring 2019",
                "confidence": 0.81,
                "raw_line": "ENG102 3 A- Spring 2019",
            }
        ],
        "extracted_csv": "Course_Code,Credits,Grade,Semester\nENG102,3,A-,Spring 2019",
    }

    with patch("api.routers.audit.extract_transcript_document", return_value=extraction):
        resp = client.post(
            "/audit/image",
            files={"file": ("transcript.png", io.BytesIO(b"fake"), "image/png")},
            data={"program": "CSE"},
            headers={"Authorization": "Bearer test-token"},
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "review_required"
    assert body["scan_id"] is None
    assert body["review"]["warnings"]


def test_audit_review_runs_engine_and_saves():
    mocked_result = {
        "program": "Computer Science & Engineering",
        "program_alias": "CSE",
        "metadata": {
            "requested_level": "all",
            "requested_level_label": "All Levels",
            "report_mode": "normal",
            "selected_concentration": None,
            "selected_minor": None,
            "program_alias": "CSE",
        },
        "non_nsu_courses_flagged": [],
        "waivers_applied": [],
        "credits": {"total_earned": 130, "course_statuses": []},
        "cgpa": {"final": 3.5, "semesters": []},
        "grade_distribution": {},
        "audit": {"eligible": True, "reasons": [], "roadmap": []},
    }
    with patch("api.routers.audit._run_engine", return_value=mocked_result):
        with patch(AUDIT_MOCK, return_value=_mock_supabase_insert()):
            resp = client.post(
                "/audit/review",
                json={
                    "program": "CSE",
                    "input_type": "pdf",
                    "file_name": "reviewed.pdf",
                    "extracted_csv": "Course_Code,Credits,Grade,Semester\nENG102,3,A-,Spring 2019",
                    "waivers": [],
                    "level": "all",
                    "report": "normal",
                    "extraction_mode": "pdf_ocr",
                    "warnings": ["foo"],
                },
                headers={"Authorization": "Bearer test-token"},
            )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "audited"
    assert body["input_type"] == "pdf"
    assert body["result"]["metadata"]["extraction"]["review_accepted"] is True


def test_audit_review_saves_pdf_as_legacy_image_input_type():
    mocked_result = {
        "program": "Computer Science & Engineering",
        "program_alias": "CSE",
        "metadata": {
            "requested_level": "all",
            "requested_level_label": "All Levels",
            "report_mode": "normal",
            "selected_concentration": None,
            "selected_minor": None,
            "program_alias": "CSE",
        },
        "non_nsu_courses_flagged": [],
        "waivers_applied": [],
        "credits": {"total_earned": 130, "course_statuses": []},
        "cgpa": {"final": 3.5, "semesters": []},
        "grade_distribution": {},
        "audit": {"eligible": True, "reasons": [], "roadmap": []},
    }
    inserted_payload = {}

    class CaptureTable:
        def insert(self, payload):
            inserted_payload.update(payload)
            return self

        def execute(self):
            response = MagicMock()
            response.data = [{"id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"}]
            return response

    class CaptureSupabase:
        def table(self, _name):
            return CaptureTable()

    with patch("api.routers.audit.TEST_MODE", False):
        with patch("api.routers.audit._run_engine", return_value=mocked_result):
            with patch(AUDIT_MOCK, return_value=CaptureSupabase()):
                resp = client.post(
                    "/audit/review",
                    json={
                        "program": "CSE",
                        "input_type": "pdf",
                        "file_name": "reviewed.pdf",
                        "extracted_csv": "Course_Code,Credits,Grade,Semester\nENG102,3,A-,Spring 2019",
                        "waivers": [],
                        "level": "all",
                        "report": "normal",
                        "extraction_mode": "pdf_ocr",
                        "warnings": ["foo"],
                    },
                    headers={"Authorization": "Bearer test-token"},
                )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["input_type"] == "pdf"
    assert body["result"]["metadata"]["extraction"]["input_type"] == "pdf"
    assert inserted_payload["input_type"] == "image"


def test_audit_review_reports_history_save_failure():
    mocked_result = {
        "program": "Computer Science & Engineering",
        "program_alias": "CSE",
        "metadata": {
            "requested_level": "all",
            "requested_level_label": "All Levels",
            "report_mode": "normal",
            "selected_concentration": None,
            "selected_minor": None,
            "program_alias": "CSE",
        },
        "non_nsu_courses_flagged": [],
        "waivers_applied": [],
        "credits": {"total_earned": 130, "course_statuses": []},
        "cgpa": {"final": 3.5, "semesters": []},
        "grade_distribution": {},
        "audit": {"eligible": True, "reasons": [], "roadmap": []},
    }

    class BrokenTable:
        def insert(self, _payload):
            raise RuntimeError("relation scan_sessions does not exist")

    class BrokenSupabase:
        def table(self, _name):
            return BrokenTable()

    with patch("api.routers.audit.TEST_MODE", False):
        with patch("api.routers.audit._run_engine", return_value=mocked_result):
            with patch(AUDIT_MOCK, return_value=BrokenSupabase()):
                resp = client.post(
                    "/audit/review",
                    json={
                        "program": "CSE",
                        "input_type": "pdf",
                        "file_name": "reviewed.pdf",
                        "extracted_csv": "Course_Code,Credits,Grade,Semester\nENG102,3,A-,Spring 2019",
                        "waivers": [],
                        "level": "all",
                        "report": "normal",
                        "extraction_mode": "pdf_ocr",
                        "warnings": ["foo"],
                    },
                    headers={"Authorization": "Bearer test-token"},
                )

    assert resp.status_code == 502
    assert "saving to Supabase history failed" in resp.json()["detail"]


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
