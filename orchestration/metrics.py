"""In-process counters for the orchestrator bus.

Interview angle: operational visibility without a metrics vendor. Prometheus text
is enough for Render/Railway scrapers; JSON is for the desk and demos.
"""
from __future__ import annotations

import threading
from collections import defaultdict
from typing import DefaultDict


class Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.counters: DefaultDict[str, int] = defaultdict(int)
        self.agent_calls: DefaultDict[str, int] = defaultdict(int)
        self.agent_failures: DefaultDict[str, int] = defaultdict(int)
        self.outcomes: DefaultDict[str, int] = defaultdict(int)
        self.statuses: DefaultDict[str, int] = defaultdict(int)

    def inc(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self.counters[name] += amount

    def record_agent(self, stage: str, *, ok: bool) -> None:
        with self._lock:
            self.agent_calls[stage] += 1
            if not ok:
                self.agent_failures[stage] += 1

    def record_workflow(self, status: str, outcome: str | None) -> None:
        with self._lock:
            self.statuses[status or "unknown"] += 1
            if outcome:
                self.outcomes[outcome] += 1

    def as_dict(self) -> dict:
        with self._lock:
            return {
                "counters": dict(sorted(self.counters.items())),
                "agent_calls": dict(sorted(self.agent_calls.items())),
                "agent_failures": dict(sorted(self.agent_failures.items())),
                "workflow_statuses": dict(sorted(self.statuses.items())),
                "final_outcomes": dict(sorted(self.outcomes.items())),
            }

    def as_prometheus(self) -> str:
        data = self.as_dict()
        lines = [
            "# HELP cube_orchestrator_info Cube Round 3 orchestrator counters",
            "# TYPE cube_orchestrator_info gauge",
            "cube_orchestrator_info 1",
        ]
        for name, value in data["counters"].items():
            safe = name.replace("-", "_").replace(".", "_")
            lines.append(f'cube_counter{{name="{safe}"}} {value}')
        for stage, value in data["agent_calls"].items():
            lines.append(f'cube_agent_calls_total{{stage="{stage}"}} {value}')
        for stage, value in data["agent_failures"].items():
            lines.append(f'cube_agent_failures_total{{stage="{stage}"}} {value}')
        for status, value in data["workflow_statuses"].items():
            lines.append(f'cube_workflow_status_total{{status="{status}"}} {value}')
        for outcome, value in data["final_outcomes"].items():
            lines.append(f'cube_final_outcome_total{{outcome="{outcome}"}} {value}')
        return "\n".join(lines) + "\n"


METRICS = Metrics()
