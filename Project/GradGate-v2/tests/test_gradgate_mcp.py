"""Smoke tests for the optional gradgate_mcp package (skipped if [mcp] not installed)."""

from __future__ import annotations

import pytest

pytest.importorskip("mcp")
pytest.importorskip("httpx")


def test_gradgate_mcp_server_imports() -> None:
    from gradgate_mcp.server import mcp

    assert mcp.name == "GradGate"
