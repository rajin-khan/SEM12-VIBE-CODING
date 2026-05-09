"""HTTP client for the GradGate FastAPI — same behavior as web/mobile clients."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

DEFAULT_API_URL = "http://127.0.0.1:8000"

_TOKEN_HELP = (
    "Set GRADGATE_API_TOKEN to a valid Bearer token "
    "(e.g. Supabase session JWT or GET /test-token in dev with TEST_MODE)."
)


def api_base_url() -> str:
    return os.environ.get("GRADGATE_API_URL", DEFAULT_API_URL).rstrip("/")


def _bearer_headers() -> dict[str, str]:
    token = os.environ.get("GRADGATE_API_TOKEN", "").strip()
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def _auth_required_error() -> dict[str, Any]:
    return {"ok": False, "error": _TOKEN_HELP}


def request_json(
    method: str,
    path: str,
    *,
    require_token: bool,
    timeout: float = 120.0,
    **kwargs: Any,
) -> dict[str, Any]:
    """Perform an HTTP request and return a JSON-serialisable result dict."""
    if require_token and not os.environ.get("GRADGATE_API_TOKEN", "").strip():
        return _auth_required_error()

    headers = {**_bearer_headers(), **kwargs.pop("headers", {})}
    url = f"{api_base_url()}{path}"
    with httpx.Client(timeout=timeout) as client:
        response = client.request(method, url, headers=headers, **kwargs)
    body = _json_or_text(response)
    if response.is_success:
        return {"ok": True, "status_code": response.status_code, "data": body}
    return {
        "ok": False,
        "status_code": response.status_code,
        "error": body,
    }


def _json_or_text(response: httpx.Response) -> Any:
    try:
        return response.json()
    except json.JSONDecodeError:
        return response.text


def post_audit_csv(
    csv_content: str,
    filename: str,
    program: str,
    *,
    waivers: str = "",
    level: str = "all",
    report: str = "normal",
    concentration: str | None = None,
    minor: str | None = None,
) -> dict[str, Any]:
    """POST /audit/csv — multipart form matching the FastAPI route."""
    files = {
        "file": (filename or "transcript.csv", csv_content.encode("utf-8"), "text/csv"),
    }
    data: dict[str, Any] = {
        "program": program,
        "waivers": waivers,
        "level": level,
        "report": report,
    }
    if concentration is not None and concentration != "":
        data["concentration"] = concentration
    if minor is not None and minor != "":
        data["minor"] = minor

    return request_json(
        "POST",
        "/audit/csv",
        require_token=True,
        files=files,
        data=data,
    )
