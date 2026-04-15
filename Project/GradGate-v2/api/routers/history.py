"""History router — list and retrieve past audit scan sessions."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from api.auth import CurrentUser
from api.models import ScanDetail, ScanSummary
from api.services.supabase_client import get_supabase

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[ScanSummary], summary="List past audit scans")
def list_history(user_id: CurrentUser) -> list[ScanSummary]:
    """Return the authenticated user's past scans, newest first."""
    sb = get_supabase()
    response = (
        sb.table("scan_sessions")
        .select("id, created_at, program, input_type, file_name, result_json")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    summaries = []
    for row in response.data:
        result = row.get("result_json")
        if isinstance(result, str):
            import json as _json

            result = _json.loads(result)
        requested_level = None
        if isinstance(result, dict):
            requested_level = result.get("metadata", {}).get("requested_level")
        summaries.append(
            ScanSummary(
                id=row["id"],
                created_at=row["created_at"],
                program=row["program"],
                input_type=row["input_type"],
                file_name=row.get("file_name"),
                requested_level=requested_level,
            )
        )
    return summaries


@router.get("/{scan_id}", response_model=ScanDetail, summary="Get a specific scan result")
def get_scan(user_id: CurrentUser, scan_id: UUID) -> ScanDetail:
    """Return the full audit result for a specific scan.

    Returns 404 if the scan doesn't exist or belongs to another user.
    """
    sb = get_supabase()
    response = (
        sb.table("scan_sessions")
        .select("id, created_at, program, input_type, file_name, result_json")
        .eq("id", str(scan_id))
        .eq("user_id", user_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan '{scan_id}' not found",
        )

    row = response.data[0]
    # result_json is stored as a JSONB string in Supabase; may come back as str or dict
    import json as _json

    result = row["result_json"]
    if isinstance(result, str):
        result = _json.loads(result)

    return ScanDetail(
        id=row["id"],
        created_at=row["created_at"],
        program=row["program"],
        input_type=row["input_type"],
        file_name=row.get("file_name"),
        result=result,
    )
