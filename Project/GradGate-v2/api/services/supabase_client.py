"""Supabase admin client — singleton for server-side DB and Storage access."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

_client: Client | None = None


def get_supabase() -> Client:
    """Return the singleton Supabase admin client.

    Uses the service role key (bypasses RLS) for server-side operations.
    The API already enforces auth via JWT — we pass user_id explicitly
    when writing to scan_sessions so RLS policies still make sense.
    """
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_SERVICE_KEY", "")
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env"
            )
        _client = create_client(url, key)
    return _client
