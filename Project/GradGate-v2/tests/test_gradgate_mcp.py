"""Smoke tests for the optional gradgate_mcp package (skipped if [mcp] not installed)."""

from __future__ import annotations

import pytest

pytest.importorskip("mcp")
pytest.importorskip("httpx")


def test_gradgate_mcp_server_imports() -> None:
    from gradgate_mcp.server import mcp

    assert mcp.name == "GradGate"


def test_gradgate_mcp_document_tool_delegates(monkeypatch, tmp_path) -> None:
    from gradgate_mcp import api_client
    from gradgate_mcp.server import gradgate_audit_document

    transcript = tmp_path / "transcript.pdf"
    transcript.write_bytes(b"%PDF-1.4")
    captured = {}

    def fake_post_audit_document(file_path, program, **kwargs):
        captured.update({"file_path": file_path, "program": program, **kwargs})
        return {"ok": True, "data": {"status": "review_required"}}

    monkeypatch.setattr(api_client, "post_audit_document", fake_post_audit_document)

    response = gradgate_audit_document(
        str(transcript),
        "CSE",
        waivers="ENG102",
        level="3",
        report="full",
        minor="MATH",
    )

    assert response["ok"] is True
    assert captured["file_path"] == str(transcript)
    assert captured["program"] == "CSE"
    assert captured["waivers"] == "ENG102"
    assert captured["level"] == "3"
    assert captured["report"] == "full"
    assert captured["minor"] == "MATH"


def test_gradgate_mcp_review_tool_delegates(monkeypatch) -> None:
    from gradgate_mcp import api_client
    from gradgate_mcp.server import gradgate_audit_reviewed_document

    captured = {}

    def fake_post_reviewed_audit(**kwargs):
        captured.update(kwargs)
        return {"ok": True, "data": {"status": "audited"}}

    monkeypatch.setattr(api_client, "post_reviewed_audit", fake_post_reviewed_audit)

    response = gradgate_audit_reviewed_document(
        program="CSE",
        input_type="pdf",
        extracted_csv="Course_Code,Credits,Grade,Semester\nCSE115,3,A,Spring 2024",
        waivers=["ENG102"],
        extraction_mode="pdf_ocr",
    )

    assert response["ok"] is True
    assert captured["program"] == "CSE"
    assert captured["input_type"] == "pdf"
    assert captured["waivers"] == ["ENG102"]
    assert captured["extraction_mode"] == "pdf_ocr"
