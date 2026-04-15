"""JWT authentication dependency for FastAPI.

Validates Supabase-issued JWTs and extracts the user_id.
In TEST_MODE (local dev only), any token is accepted and a fixed user_id is used.
"""

from __future__ import annotations

import os
from typing import Annotated
from pathlib import Path

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

API_DIR = Path(__file__).resolve().parent
load_dotenv(API_DIR.parent / "cli" / ".env")
load_dotenv(API_DIR.parent / ".env")

_bearer = HTTPBearer(auto_error=True)

TEST_MODE = os.environ.get("TEST_MODE", "false").lower() == "true"
TEST_USER_ID = "00000000-0000-0000-0000-000000000001"


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> str:
    """FastAPI dependency — validates Supabase JWT, returns user_id string.

    Raises 401 if the token is missing, expired, or invalid.
    """
    token = credentials.credentials

    # TEST_MODE: skip real JWT validation for local development
    if TEST_MODE:
        return TEST_USER_ID

    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    
    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfiguration: SUPABASE_URL or KEY not set",
        )

    try:
        from api.services.supabase_client import get_supabase
        from supabase import create_client
        client = create_client(supabase_url, supabase_key)
        
        response = client.auth.get_user(token)
        if response and response.user:
            return response.user.id
        else:
            raise Exception("No user found for token")
            
    except Exception as exc:
        print("JWT ERROR:", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        )


# Convenient type alias for routes
CurrentUser = Annotated[str, Depends(get_current_user)]
