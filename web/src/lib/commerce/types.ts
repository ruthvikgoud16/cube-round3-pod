export type WorkflowStatus =
  "PENDING" | "IN_PROGRESS" | "COMPLETED" | "FAILED" | "BLOCKED" | "RECOVERY_REQUIRED";
export type Outcome = "CLEAN" | "EXCEPTION" | "INCOMPLETE" | "NEEDS_REVIEW" | "CLAIM_RECOMMENDED";
export type StageStatus =
  "WAITING" | "RUNNING" | "COMPLETED" | "BLOCKED" | "SKIPPED" | "SERVICE_UNAVAILABLE" | "FAILED";
export type Verdict = "PASS" | "FAIL" | "UNCERTAIN";
export interface Check {
  name: string;
  verdict: Verdict;
  expected: string;
  observed: string;
  confidence?: number;
}
export interface Evidence {
  id: string;
  kind: string;
  label: string;
  upstream: string[];
  hash?: string;
  timestamp?: string | undefined;
}
export interface ModelCall {
  model: string;
  cost?: number;
  timestamp?: string | undefined;
}
export interface Stage {
  id: string;
  name: string;
  agent: string;
  status: StageStatus;
  verdict?: Verdict | undefined;
  recommendation?: string;
  explanation: string;
  timestamp?: string | undefined;
  review: boolean;
  checks: Check[];
  evidence: Evidence[];
  modelCalls: ModelCall[];
  error?: string;
}
export interface Workflow {
  id: string;
  product: string;
  sku: string;
  unit: string;
  route: string;
  status: WorkflowStatus;
  outcome?: Outcome | undefined;
  updated: string;
  stages: Stage[];
  decision: string;
  reviewReason?: string | undefined;
  priority?: "HIGH" | "MEDIUM" | "LOW" | undefined;
  override?: { actor: string; reason: string; timestamp: string };
}
export interface AgentHealth {
  name: string;
  state: "AVAILABLE" | "DEGRADED" | "UNAVAILABLE";
  latency?: number;
  detail: string;
}
export interface CommerceEvent {
  id: string;
  workflowId: string;
  stage: string;
  text: string;
  timestamp: string;
  tone: "success" | "warning" | "info" | "danger";
}
export interface CommerceSnapshot {
  source: "example" | "backend";
  workflows: Workflow[];
  health: AgentHealth[];
  events: CommerceEvent[];
}
// This is a UI-facing contract, not an assumption about your backend's API.
export interface CommerceAdapter {
  loadSnapshot: () => Promise<CommerceSnapshot>;
  subscribe?: (receive: (snapshot: CommerceSnapshot) => void) => () => void;
  submitOverride?: (input: {
    workflowId: string;
    reason: string;
  }) => Promise<{ actor: string; reason: string; timestamp: string }>;
}
