import type {
  AgentHealth,
  Check,
  CommerceAdapter,
  CommerceEvent,
  CommerceSnapshot,
  Evidence,
  ModelCall,
  Outcome,
  Stage,
  StageStatus,
  Verdict,
  Workflow,
  WorkflowStatus,
} from "./types";

const STATUSES = new Set<WorkflowStatus>([
  "PENDING",
  "IN_PROGRESS",
  "COMPLETED",
  "FAILED",
  "BLOCKED",
  "RECOVERY_REQUIRED",
]);
const OUTCOMES = new Set<Outcome>([
  "CLEAN",
  "EXCEPTION",
  "INCOMPLETE",
  "NEEDS_REVIEW",
  "CLAIM_RECOMMENDED",
]);
const VERDICTS = new Set<Verdict>(["PASS", "FAIL", "UNCERTAIN"]);
const STAGE_NAMES: Record<string, string> = {
  receiving: "Receiving",
  prep: "Prep",
  pack: "Pack",
  returns: "Returns",
  recovery: "Recovery",
};

type Json = Record<string, unknown>;

function asRecord(value: unknown): Json {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Json) : {};
}

function text(value: unknown): string {
  const raw =
    typeof value === "string" ? value : value == null ? "" : JSON.stringify(value);
  return raw.replace(/\/(?:Users|private|tmp|home)\/\S+/g, "[local folder]");
}

function verdict(value: unknown): Verdict | undefined {
  return typeof value === "string" && VERDICTS.has(value as Verdict)
    ? (value as Verdict)
    : undefined;
}

function stageStatus(row: Json): StageStatus {
  const state = text(row["state"]);
  if (state === "skipped") return "SKIPPED";
  if (state === "completed") return "COMPLETED";
  if (row["started_at"] && !row["finished_at"] && state !== "error") return "RUNNING";
  if (state === "error") {
    const detail = text(row["error"]).toLowerCase();
    if (/unavailable|connection refused|connect/.test(detail)) return "SERVICE_UNAVAILABLE";
    return "FAILED";
  }
  return "WAITING";
}

function checksOf(record: Json): Check[] {
  const rows = Array.isArray(record["checks"]) ? record["checks"] : [];
  return rows.flatMap((item) => {
    const row = asRecord(item);
    const found = verdict(row["verdict"]);
    if (!found) return [];
    const confidence = row["confidence"];
    return [
      {
        name: text(row["check_key"] || row["name"]) || "check",
        verdict: found,
        expected: text(row["expected"]) || "Not recorded",
        observed: text(row["observed"]) || "Not recorded",
        ...(typeof confidence === "number" ? { confidence } : {}),
      },
    ];
  });
}

function evidenceOf(record: Json): Evidence[] {
  const id = text(record["record_id"]);
  if (!id) return [];
  const upstream = Array.isArray(record["upstream_refs"])
    ? record["upstream_refs"].map((item) => text(item)).filter(Boolean)
    : [];
  const items: Evidence[] = [
    {
      id,
      kind: "evidence record",
      label: `${text(record["stage"]) || "stage"} record`,
      upstream,
      hash: text(record["content_hash"]) || undefined,
      timestamp: text(record["produced_at"]) || undefined,
    },
  ];
  const inputs = Array.isArray(record["inputs"]) ? record["inputs"] : [];
  for (const item of inputs) {
    const row = asRecord(item);
    const ref = text(row["ref"]);
    if (!ref) continue;
    items.push({
      id: `${id}:${ref}`,
      kind: text(row["kind"]) || "input",
      label: ref,
      upstream: [],
      hash: text(row["sha256"]) || undefined,
    });
  }
  return items;
}

function modelCallsOf(record: Json): ModelCall[] {
  const model = asRecord(record["model"]);
  const calls = model["calls"];
  if (typeof calls !== "number" || calls < 1) return [];
  const cost = model["cost_usd"];
  const name = [text(model["name"]), text(model["version"])].filter(Boolean).join(" ");
  return [
    {
      model: name || "model",
      ...(typeof cost === "number" ? { cost } : {}),
      timestamp: text(record["produced_at"]) || undefined,
    },
  ];
}

function mapStage(row: Json, records: Record<string, Json>): Stage {
  const stage = text(row["stage"]);
  const record = records[text(row["record_id"])] ?? {};
  const decision = asRecord(record["decision"]);
  const found = verdict(row["verdict"] ?? decision["verdict"]);
  const reason = text(decision["reason"] || row["error"] || row["skipped_reason"]);
  return {
    id: stage || "stage",
    name: STAGE_NAMES[stage] || stage || "Stage",
    agent: text(row["agent_id"] || record["agent_id"]) || stage,
    status: stageStatus(row),
    verdict: found,
    recommendation: text(row["next_step_recommendation"]) || undefined,
    explanation: reason || text(row["state"]) || "No reason recorded",
    timestamp: text(row["finished_at"] || row["started_at"]) || undefined,
    review: row["needs_human"] === true || decision["needs_human"] === true || found === "UNCERTAIN",
    checks: checksOf(record),
    evidence: evidenceOf(record),
    modelCalls: modelCallsOf(record),
    error: text(row["error"]) || undefined,
  };
}

function displayRank(status: WorkflowStatus, review: boolean): "HIGH" | "MEDIUM" | "LOW" {
  if (review || status === "BLOCKED") return "HIGH";
  if (status === "FAILED" || status === "RECOVERY_REQUIRED") return "MEDIUM";
  return "LOW";
}

export function workflowFromBundle(bundle: unknown): Workflow {
  const body = asRecord(bundle);
  const wf = asRecord(body["workflow"] ?? body);
  const evidence = asRecord(body["evidence"]);
  const records: Record<string, Json> = {};
  for (const [key, value] of Object.entries(evidence)) {
    const record = asRecord(value);
    if (Object.keys(record).length) records[key] = record;
  }
  const stages = (Array.isArray(wf["stage_results"]) ? wf["stage_results"] : []).map((row) =>
    mapStage(asRecord(row), records),
  );
  const outcome = asRecord(wf["final_outcome"]);
  const statusText = text(wf["status"]);
  const status: WorkflowStatus = STATUSES.has(statusText as WorkflowStatus)
    ? (statusText as WorkflowStatus)
    : "PENDING";
  const outcomeText = text(outcome["outcome"]);
  const context = asRecord(wf["context"]);
  const overrides = Array.isArray(wf["overrides"]) ? wf["overrides"] : [];
  const last = asRecord(overrides.at(-1));
  const review = outcome["needs_human"] === true || status === "BLOCKED" || stages.some((stage) => stage.review);
  const reason = text(outcome["reason"] || wf["status_reason"]);
  return {
    id: text(wf["workflow_id"]),
    product: text(context["product_name"]) || text(wf["subject_id"]),
    sku: text(context["sku"]),
    unit: text(wf["subject_id"]),
    route: text(context["route"]) || "Not recorded",
    status,
    outcome: OUTCOMES.has(outcomeText as Outcome) ? (outcomeText as Outcome) : undefined,
    updated: text(asRecord(wf["timestamps"])["updated_at"]),
    stages,
    decision: reason || status,
    reviewReason: review ? reason || "A person must decide." : undefined,
    priority: displayRank(status, review),
    ...(text(last["actor"])
      ? {
          override: {
            actor: text(last["actor"]),
            reason: text(last["reason"]),
            timestamp: text(last["at"]),
          },
        }
      : {}),
  };
}

function healthFrom(body: unknown): AgentHealth[] {
  const agents = asRecord(asRecord(body)["agents"]);
  return Object.entries(agents).map(([name, value]) => {
    const row = asRecord(value);
    const status = text(row["status"]);
    const state =
      status === "ok" ? "AVAILABLE" : status === "degraded" ? "DEGRADED" : "UNAVAILABLE";
    const bits = [
      status || "unknown",
      text(row["mode"]),
      text(row["model"]),
      row["db_reachable"] === false ? "database unreachable" : "",
      text(row["error"]),
    ].filter(Boolean);
    return {
      name: STAGE_NAMES[name] || name,
      state,
      detail: bits.join(" · "),
    };
  });
}

function eventsFrom(workflows: Workflow[], bundles: Json[]): CommerceEvent[] {
  const events: CommerceEvent[] = [];
  bundles.forEach((bundle, index) => {
    const wf = asRecord(bundle["workflow"]);
    const id = workflows[index]?.id || text(wf["workflow_id"]);
    const rows = Array.isArray(wf["transitions"]) ? wf["transitions"] : [];
    rows.forEach((item, eventIndex) => {
      const row = asRecord(item);
      const event = text(row["event"]);
      const tone: CommerceEvent["tone"] = /error|halt|fail/i.test(event)
        ? "danger"
        : /override|uncertain|review/i.test(event)
          ? "warning"
          : "info";
      events.push({
        id: `${id}:${eventIndex}`,
        workflowId: id,
        stage: text(row["stage"]) || "orchestrator",
        text: [event, text(row["detail"])].filter(Boolean).join(" · "),
        timestamp: text(row["at"]),
        tone,
      });
    });
  });
  return events.slice(-40);
}

export function snapshotFrom(health: unknown, bundles: unknown[]): CommerceSnapshot {
  const rows = bundles.map((bundle) => asRecord(bundle));
  const workflows = rows.map((bundle) => workflowFromBundle(bundle));
  return {
    source: "backend",
    workflows,
    health: healthFrom(health),
    events: eventsFrom(workflows, rows),
  };
}

function apiBase(): string {
  const configured = import.meta.env.VITE_ORCH_URL?.replace(/\/$/, "");
  if (configured) return configured;
  return typeof window === "undefined" ? "http://127.0.0.1:8100" : "/orch";
}

function apiHeaders(): HeadersInit {
  const key = import.meta.env.VITE_ORCH_API_KEY;
  if (!key || typeof key !== "string") return {};
  return { Authorization: `Bearer ${key}`, "X-API-Key": key };
}

async function readJson(path: string): Promise<unknown> {
  const response = await fetch(`${apiBase()}${path}`, { headers: apiHeaders() });
  if (!response.ok) throw new Error(`${response.status} ${path}`);
  return response.json();
}

export async function loadOrchestratorSnapshot(): Promise<CommerceSnapshot> {
  const listed = asRecord(await readJson("/workflows"));
  const ids = Array.isArray(listed["workflow_ids"])
    ? listed["workflow_ids"].filter((id): id is string => typeof id === "string")
    : [];
  const [health, bundles] = await Promise.all([
    readJson("/health"),
    Promise.all(ids.map((id) => readJson(`/workflows/${encodeURIComponent(id)}/evidence`))),
  ]);
  return snapshotFrom(health, bundles);
}

function signature(snapshot: CommerceSnapshot): string {
  return snapshot.workflows
    .map((workflow) =>
      [
        workflow.id,
        workflow.status,
        workflow.outcome,
        ...workflow.stages.map(
          (stage) => `${stage.id}|${stage.status}|${stage.verdict}|${stage.timestamp}`,
        ),
      ].join(","),
    )
    .join(";");
}

export const orchestratorAdapter: CommerceAdapter = {
  loadSnapshot: loadOrchestratorSnapshot,
  subscribe(receive) {
    let previous = "";
    let stopped = false;
    const tick = async () => {
      try {
        const next = await loadOrchestratorSnapshot();
        if (stopped) return;
        const nextSignature = signature(next);
        if (nextSignature === previous) return;
        previous = nextSignature;
        receive(next);
      } catch {
        /* A failed poll keeps the last stored snapshot. */
      }
    };
    const timer = setInterval(() => void tick(), 4000);
    return () => {
      stopped = true;
      clearInterval(timer);
    };
  },
};
