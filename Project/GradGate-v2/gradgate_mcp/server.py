"""FastMCP entrypoint: tools proxy the GradGate API; resources read local curriculum data."""

from __future__ import annotations

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from gradgate_mcp import api_client

REPO_ROOT = Path(__file__).resolve().parent.parent

mcp = FastMCP("GradGate", json_response=True)


@mcp.tool()
def gradgate_health() -> dict:
    """Check GradGate API liveness (GET /health). No auth required."""
    return api_client.request_json("GET", "/health", require_token=False)


@mcp.tool()
def gradgate_audit_options() -> dict:
    """Return audit form metadata: programs, levels, report modes, minors (GET /audit/options)."""
    return api_client.request_json("GET", "/audit/options", require_token=False)


@mcp.tool()
def gradgate_ocr_status() -> dict:
    """Return OCR/PDF readiness on the API host (GET /audit/ocr-status)."""
    return api_client.request_json("GET", "/audit/ocr-status", require_token=False)


@mcp.tool()
def gradgate_audit_csv(
    csv_content: str,
    program: str,
    waivers: str = "",
    level: str = "all",
    report: str = "normal",
    concentration: str | None = None,
    minor: str | None = None,
    filename: str = "transcript.csv",
) -> dict:
    """Run a graduation audit from transcript CSV text. Requires GRADGATE_API_TOKEN."""
    return api_client.post_audit_csv(
        csv_content,
        filename,
        program,
        waivers=waivers,
        level=level,
        report=report,
        concentration=concentration,
        minor=minor,
    )


@mcp.tool()
def gradgate_history_list() -> dict:
    """List past audit scans for the authenticated user (GET /history). Requires GRADGATE_API_TOKEN."""
    return api_client.request_json("GET", "/history", require_token=True)


@mcp.tool()
def gradgate_history_get(scan_id: str) -> dict:
    """Fetch full result for one scan (GET /history/{scan_id}). Requires GRADGATE_API_TOKEN."""
    return api_client.request_json("GET", f"/history/{scan_id}", require_token=True)


@mcp.resource("gradgate://curriculum/catalog")
def resource_curriculum_catalog() -> str:
    """Read-only NSU curriculum catalog JSON used by the audit engine (large file)."""
    path = REPO_ROOT / "data" / "curriculum" / "catalog.json"
    if not path.is_file():
        return json.dumps({"error": f"Missing file: {path}"})
    return path.read_text(encoding="utf-8")


@mcp.resource("gradgate://curriculum/official-bucket-models")
def resource_official_bucket_models() -> str:
    """Read-only official bucket models JSON for curriculum fixtures."""
    path = REPO_ROOT / "data" / "curriculum" / "official_bucket_models.json"
    if not path.is_file():
        return json.dumps({"error": f"Missing file: {path}"})
    return path.read_text(encoding="utf-8")