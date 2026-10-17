"""Attach a correlation id to every HTTP request and response.

Agents already receive request_id on Agent Input; this middleware gives the
orchestrator edge the same discipline so logs and desk polls can join a run.
"""
from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from shared.utils.log import get_logger

log = get_logger("request")


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = rid
        log.info(
            "http_request",
            extra={"ctx": {"request_id": rid, "method": request.method, "path": request.url.path}},
        )
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response
