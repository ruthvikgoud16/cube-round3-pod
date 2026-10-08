"""How the orchestrator talks to an agent: in-process (Python) or HTTP (any language)."""
from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


class AgentUnavailable(Exception):
    """Connection / 5xx: worth retrying."""


class AgentTimeout(AgentUnavailable):
    """No answer in time: worth retrying."""


class AgentRejected(Exception):
    """4xx other than a schema refusal: unknown subject or wrong tenant. Retrying will not help."""


class AgentSchemaRefusal(Exception):
    """HTTP 422 with no Agent Output envelope. Same stop as a 200 pending envelope. Not a dead process."""


def load_manifest(stage: str) -> dict:
    return json.loads((ROOT / "agents" / stage / "agent.json").read_text())


class InProcClient:
    def __init__(self, manifest: dict):
        self.handle = importlib.import_module(manifest["module"]).handle

    def run(self, request: dict, timeout_s: float) -> dict:  # timeout is not enforced in-process
        try:
            return self.handle(request)
        except LookupError as exc:
            raise AgentRejected(str(exc)) from exc


def classify_http(status_code: int, body) -> tuple[str, dict | str]:
    """Map one agent HTTP result onto the bus signal.

    A 422 that already carries an Agent Output (Prep does this) is the same signal as HTTP 200
    with status pending. A 422 that is only an error string (Receiving, Pack) is a schema refusal,
    not proof the process is down. 404 stays a refusal. 5xx stays unavailable.
    """
    if status_code == 422 and isinstance(body, dict) and body.get("evidence") and body.get("stage"):
        return "output", body
    if status_code == 422:
        detail = body if isinstance(body, str) else json.dumps(body)[:300]
        return "schema_refusal", detail
    if 400 <= status_code < 500:
        detail = body if isinstance(body, str) else json.dumps(body)[:300]
        return "rejected", detail
    if status_code >= 500:
        detail = body if isinstance(body, str) else json.dumps(body)[:300]
        return "unavailable", detail
    if not isinstance(body, dict):
        return "unavailable", "response was not a JSON object"
    return "output", body


class HttpClient:
    def __init__(self, manifest: dict):
        env = f"{manifest['stage'].upper()}_URL"
        self.url = os.environ.get(env, manifest["url"]).rstrip("/")

    def run(self, request: dict, timeout_s: float) -> dict:
        try:
            resp = httpx.post(f"{self.url}/run", json=request, timeout=timeout_s)
        except httpx.TimeoutException as exc:
            raise AgentTimeout(f"{type(exc).__name__}: {exc}") from exc
        except httpx.HTTPError as exc:
            raise AgentUnavailable(f"{type(exc).__name__}: {exc}") from exc
        try:
            body = resp.json()
        except Exception:
            body = resp.text[:300]
        kind, payload = classify_http(resp.status_code, body)
        if kind == "schema_refusal":
            raise AgentSchemaRefusal(f"HTTP 422: {payload}")
        if kind == "rejected":
            raise AgentRejected(f"HTTP {resp.status_code}: {payload}")
        if kind == "unavailable":
            raise AgentUnavailable(f"HTTP {resp.status_code}: {payload}")
        return payload

    def health(self) -> dict:
        return httpx.get(f"{self.url}/health", timeout=5).json()


def client_for(stage: str):
    manifest = load_manifest(stage)
    mode = os.environ.get("ORCH_MODE") or manifest["mode"]
    return InProcClient(manifest) if mode == "inproc" else HttpClient(manifest)
