"""Optional API-key gate for the orchestrator HTTP surface.

When ORCH_API_KEY is unset, every route stays open (local demo / CI).
When set, mutating and data routes require Bearer or X-API-Key.
Public always: /health, /desk, /live, /metrics (ops probes).
"""
from __future__ import annotations

import hmac
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


PUBLIC_PREFIXES = (
    "/health",
    "/ready",
    "/desk",
    "/live",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/redoc",
)


def api_key_configured() -> str | None:
    key = (os.environ.get("ORCH_API_KEY") or "").strip()
    return key or None


def extract_api_key(request: Request) -> str | None:
    header = request.headers.get("x-api-key")
    if header:
        return header.strip()
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


def is_public_path(path: str) -> bool:
    if path == "/" or path.startswith("/assets"):
        return True
    return any(path == p or path.startswith(p + "/") for p in PUBLIC_PREFIXES)


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        expected = api_key_configured()
        if expected is None or request.method == "OPTIONS" or is_public_path(request.url.path):
            return await call_next(request)
        provided = extract_api_key(request)
        if provided is None or not hmac.compare_digest(provided, expected):
            return JSONResponse(
                {"detail": "Unauthorized. Send Authorization: Bearer <ORCH_API_KEY> or X-API-Key."},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
        return await call_next(request)
