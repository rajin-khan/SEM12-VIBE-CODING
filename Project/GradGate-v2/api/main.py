"""GradGate API — FastAPI application entry point."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.models import HealthResponse
from api.routers import audit, history

load_dotenv()

app = FastAPI(
    title="GradGate API",
    description="NSU Graduation Audit Engine — REST API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# Allow the Vite dev server and Expo dev client during development.
# In production, restrict to your actual Vercel domain.
_allowed_origins = [
    "http://localhost:5173",   # Vite dev server
    "http://localhost:19006",  # Expo web
    "http://localhost:3000",   # any other local frontend
]
_prod_origin = os.environ.get("ALLOWED_ORIGIN")
if _prod_origin:
    _allowed_origins.append(_prod_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(audit.router)
app.include_router(history.router)


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health() -> HealthResponse:
    """Liveness probe — returns 200 if the API is up."""
    return HealthResponse(status="ok")


# ── Test Token (for load testing) ─────────────────────────────────────────
@app.get("/test-token", tags=["meta"])
def get_test_token():
    """Generate a test JWT token for load testing (bypasses real OAuth)."""
    import jwt
    import time
    
    supabase_url = os.environ.get("SUPABASE_URL", "")
    jwt_secret = os.environ.get("SUPABASE_JWT_SECRET", "")
    
    # Create a test payload (sub must be a valid UUID)
    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "email": "loadtest@gradgate.com",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,  # 1 hour expiry
    }
    
    token = jwt.encode(payload, jwt_secret, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}
