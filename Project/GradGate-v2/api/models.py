"""Pydantic schemas for GradGate API request/response models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

# ── Request models ───────────────────────────────────────────────────────────


class AuditOptions(BaseModel):
    """Optional parameters for an audit run."""

    waivers: list[str] = Field(default_factory=list, description="Course codes to waive")
    report: str = Field(default="normal", pattern="^(normal|full)$")
    concentration: str | None = None
    minor: str | None = None


# ── Response models ──────────────────────────────────────────────────────────


class AuditResponse(BaseModel):
    """Returned after a successful audit run."""

    scan_id: UUID
    program: str
    input_type: str
    result: dict[str, Any]


class ScanSummary(BaseModel):
    """Lightweight scan entry for history list."""

    id: UUID
    created_at: datetime
    program: str
    input_type: str
    file_name: str | None


class ScanDetail(BaseModel):
    """Full scan detail including result JSON."""

    id: UUID
    created_at: datetime
    program: str
    input_type: str
    file_name: str | None
    result: dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    version: str = "2.0.0"
