"""How the orchestrator talks to an agent: in-process (Python) or HTTP (any language)."""
from __future__ import annotations

import importlib
import json
import os
import threading
import time
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


class CircuitOpen(AgentUnavailable):
    """Too many consecutive transport failures; short-circuit until the cooldown ends."""


def load_manifest(stage: str) -> dict:
    return json.loads((ROOT / "agents" / stage / "agent.json").read_text())


class InProcClient:
    def __init__(self, manifest: dict):
        self.handle = importlib.import_module(manifest["module"]).handle
        self.stage = manifest["stage"]

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


class CircuitBreaker:
    """Fail-fast after consecutive transport failures so one dead agent does not stall the bus.

    Threshold and cooldown are env-tunable. Open circuit raises CircuitOpen (a retryable
    AgentUnavailable subclass) so existing on_error / resume paths keep working.
    """

    def __init__(self, stage: str) -> None:
        self.stage = stage
        self.failures = 0
        self.open_until = 0.0
        self._lock = threading.Lock()
        self.threshold = int(os.environ.get("CIRCUIT_FAILURE_THRESHOLD", "3"))
        self.cooldown_s = float(os.environ.get("CIRCUIT_COOLDOWN_S", "30"))

    def before_call(self) -> None:
        with self._lock:
            if time.monotonic() < self.open_until:
                raise CircuitOpen(
                    f"circuit open for {self.stage} until cooldown ends "
                    f"({self.cooldown_s:.0f}s after {self.threshold} failures)"
                )

    def record_success(self) -> None:
        with self._lock:
            self.failures = 0
            self.open_until = 0.0

    def record_failure(self) -> None:
        with self._lock:
            self.failures += 1
            if self.failures >= self.threshold:
                self.open_until = time.monotonic() + self.cooldown_s

    def snapshot(self) -> dict:
        with self._lock:
            open_now = time.monotonic() < self.open_until
            return {
                "stage": self.stage,
                "failures": self.failures,
                "open": open_now,
                "threshold": self.threshold,
                "cooldown_s": self.cooldown_s,
            }


_BREAKERS: dict[str, CircuitBreaker] = {}
_BREAKERS_LOCK = threading.Lock()


def breaker_for(stage: str) -> CircuitBreaker:
    with _BREAKERS_LOCK:
        if stage not in _BREAKERS:
            _BREAKERS[stage] = CircuitBreaker(stage)
        return _BREAKERS[stage]


def reset_breakers() -> None:
    """Test helper."""
    with _BREAKERS_LOCK:
        _BREAKERS.clear()


class HttpClient:
    def __init__(self, manifest: dict):
        env = f"{manifest['stage'].upper()}_URL"
        self.stage = manifest["stage"]
        self.url = os.environ.get(env, manifest["url"]).rstrip("/")
        self.breaker = breaker_for(self.stage)

    def run(self, request: dict, timeout_s: float) -> dict:
        self.breaker.before_call()
        try:
            resp = httpx.post(f"{self.url}/run", json=request, timeout=timeout_s)
        except httpx.TimeoutException as exc:
            self.breaker.record_failure()
            raise AgentTimeout(f"{type(exc).__name__}: {exc}") from exc
        except httpx.HTTPError as exc:
            self.breaker.record_failure()
            raise AgentUnavailable(f"{type(exc).__name__}: {exc}") from exc
        try:
            body = resp.json()
        except Exception:
            body = resp.text[:300]
        kind, payload = classify_http(resp.status_code, body)
        if kind == "schema_refusal":
            # Schema refusal is a judgment stop, not a dead process — do not trip the breaker.
            raise AgentSchemaRefusal(f"HTTP 422: {payload}")
        if kind == "rejected":
            raise AgentRejected(f"HTTP {resp.status_code}: {payload}")
        if kind == "unavailable":
            self.breaker.record_failure()
            raise AgentUnavailable(f"HTTP {resp.status_code}: {payload}")
        self.breaker.record_success()
        return payload

    def health(self) -> dict:
        return httpx.get(f"{self.url}/health", timeout=5).json()


def client_for(stage: str):
    manifest = load_manifest(stage)
    mode = os.environ.get("ORCH_MODE") or manifest["mode"]
    return InProcClient(manifest) if mode == "inproc" else HttpClient(manifest)
