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


class SavedAuditRequest(BaseModel):
    """Request payload for persisting a locally computed audit result."""

    program: str
    input_type: str
    file_name: str | None = None
    result: dict[str, Any]


class AuditOptionsResponse(BaseModel):
    """Metadata used by web/mobile clients to build audit forms."""

    programs: list[dict[str, Any]]
    levels: list[dict[str, str]]
    report_modes: list[str]
    supported_minors: list[str]
    bba_concentrations: list[dict[str, str]]


class OCRHealthResponse(BaseModel):
    """Local OCR/PDF capability metadata."""

    ready: bool
    image_ocr_ready: bool
    scanned_pdf_ready: bool
    text_pdf_ready: bool
    dependencies: dict[str, bool]
    messages: list[str]


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
    requested_level: str | None = None


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
