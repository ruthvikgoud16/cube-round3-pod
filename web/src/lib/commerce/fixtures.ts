import type { CommerceSnapshot, Stage, Workflow, Verdict } from "./types";
const time = "2026-10-10T04:24:18Z";
const makeStage = (name: string, verdict?: Verdict, patch: Partial<Stage> = {}): Stage => ({
  id: name.toLowerCase(),
  name,
  agent: `${name.toLowerCase()}_agent`,
  status: verdict ? "COMPLETED" : "WAITING",
  verdict,
  explanation:
    verdict === "PASS"
      ? "All required checks passed. Evidence is consistent with the expected unit."
      : "Waiting for upstream evidence.",
  timestamp: verdict ? time : undefined,
  review: false,
  checks: verdict
    ? [
        {
          name: "Product identity",
          verdict,
          expected: "SKU matches the workflow unit",
          observed: "Identity matches the supplied example reference",
          confidence: 0.97,
        },
      ]
    : [],
  evidence: verdict
    ? [
        {
          id: `EX-${name.toUpperCase()}-001`,
          kind: "Inspection record",
          label: `${name} inspection example`,
          upstream: name === "Receiving" ? [] : ["EX-RECEIVING-001"],
          hash: "example:9d84a27c5b61e03f",
          timestamp: time,
        },
      ]
    : [],
  modelCalls: verdict ? [{ model: "Example vision model", cost: 0.014, timestamp: time }] : [],
  ...patch,
});
const receiving = makeStage("Receiving", "PASS", {
  explanation: "Identity, quantity and carton condition match. No visible unit damage.",
  checks: [
    {
      name: "Product identity",
      verdict: "PASS",
      expected: "CUBE H1 · Graphite",
      observed: "Product and label match",
      confidence: 0.98,
    },
    {
      name: "Quantity",
      verdict: "PASS",
      expected: "1 unit",
      observed: "1 unit visible",
      confidence: 0.99,
    },
    {
      name: "Carton condition",
      verdict: "PASS",
      expected: "No damage",
      observed: "Intact carton",
      confidence: 0.95,
    },
    {
      name: "Unit damage",
      verdict: "PASS",
      expected: "No visible damage",
      observed: "No visible damage in example photos",
      confidence: 0.96,
    },
  ],
});
const prep = makeStage("Prep", "PASS", {
  explanation: "Exactly three required photos supplied. Label and preparation checks passed.",
  checks: [
    {
      name: "Photo count gate",
      verdict: "PASS",
      expected: "Exactly 3: front, back, label",
      observed: "3 photos: front, back, label",
      confidence: 1,
    },
    {
      name: "Product label",
      verdict: "PASS",
      expected: "Readable matching label",
      observed: "Matching label visible",
      confidence: 0.98,
    },
  ],
});
const returns = makeStage("Returns", "UNCERTAIN", {
  review: true,
  recommendation: "Manual condition inspection",
  explanation: "Identity confirmed. A surface mark cannot be distinguished from a reflection.",
  checks: [
    {
      name: "Identity",
      verdict: "PASS",
      expected: "Original unit",
      observed: "Serial and product match",
      confidence: 0.98,
    },
    {
      name: "Completeness",
      verdict: "PASS",
      expected: "Headphones, cable, case",
      observed: "All expected items visible",
      confidence: 0.96,
    },
    {
      name: "Condition",
      verdict: "UNCERTAIN",
      expected: "No surface damage",
      observed: "Possible mark on left ear cup",
      confidence: 0.61,
    },
  ],
});
const recovery = makeStage("Recovery", undefined, {
  status: "BLOCKED",
  review: true,
  explanation: "Condition review is required before fee reconciliation can proceed.",
  error: "UPSTREAM_REVIEW_REQUIRED",
  checks: [],
  modelCalls: [],
});
const primary: Workflow = {
  id: "WF-10482",
  product: "Studio Wireless Headphones",
  sku: "CUBE-H1-GR",
  unit: "UNIT-008421",
  route: "FBA · Returned",
  status: "BLOCKED",
  outcome: "NEEDS_REVIEW",
  updated: time,
  stages: [receiving, prep, returns, recovery],
  decision:
    "Hold for human review. Return condition is uncertain; downstream recovery remains blocked.",
  reviewReason: "Return condition requires visual verification",
  priority: "HIGH",
};
export const fixtureSnapshot: CommerceSnapshot = {
  source: "example",
  workflows: [
    primary,
    {
      ...primary,
      id: "WF-10481",
      product: "Arc Mechanical Keyboard",
      sku: "ARC-K2-SL",
      unit: "UNIT-008420",
      route: "Direct fulfilment",
      status: "COMPLETED",
      outcome: "CLEAN",
      reviewReason: undefined,
      priority: undefined,
      stages: [
        receiving,
        makeStage("Pack", "PASS", {
          recommendation: "Seal",
          explanation: "Open-box contents match the order. Sealing recommended.",
        }),
        makeStage("Recovery", "PASS", {
          recommendation: "No claim",
          explanation: "Named fee line matches upstream evidence. No discrepancy found.",
        }),
      ],
      decision: "All inspections passed. No reconciliation discrepancy.",
    },
    {
      ...primary,
      id: "WF-10480",
      product: "Orbit USB-C Hub",
      sku: "ORB-U7-BK",
      unit: "UNIT-008419",
      route: "Direct fulfilment",
      status: "RECOVERY_REQUIRED",
      outcome: "CLAIM_RECOMMENDED",
      stages: [
        receiving,
        makeStage("Pack", "PASS", { recommendation: "Seal" }),
        makeStage("Recovery", "FAIL", {
          recommendation: "Claim recommended",
          explanation: "Named handling fee line conflicts with the recorded received quantity.",
          review: true,
        }),
      ],
      reviewReason: "Named fee discrepancy requires claim review",
      priority: "MEDIUM",
      decision: "Claim recommended for the named fee discrepancy. Amount not supplied.",
    },
    {
      ...primary,
      id: "WF-10479",
      product: "Studio Wireless Headphones",
      sku: "CUBE-H1-GR",
      unit: "UNIT-008418",
      route: "FBA",
      status: "IN_PROGRESS",
      outcome: undefined,
      stages: [
        receiving,
        makeStage("Prep", undefined, {
          status: "RUNNING",
          explanation: "Example snapshot: preparation inspection was in progress when captured.",
        }),
        makeStage("Recovery"),
      ],
      reviewReason: undefined,
      priority: undefined,
      decision: "No final decision available.",
    },
    {
      ...primary,
      id: "WF-10478",
      product: "Pulse Smart Watch",
      sku: "PLS-W4-SV",
      unit: "UNIT-008417",
      route: "FBA",
      status: "FAILED",
      outcome: "INCOMPLETE",
      stages: [
        receiving,
        makeStage("Prep", "FAIL", {
          status: "FAILED",
          review: true,
          explanation: "Two photos supplied. Exactly three required; model was not called.",
          checks: [
            {
              name: "Photo count gate",
              verdict: "FAIL",
              expected: "Exactly 3: front, back, label",
              observed: "2 photos; product label absent",
            },
          ],
          modelCalls: [],
          error: "INVALID_PHOTO_COUNT",
        }),
        makeStage("Recovery", undefined, {
          status: "SKIPPED",
          explanation: "Skipped because preparation failed.",
        }),
      ],
      reviewReason: "Missing required product label photo",
      priority: "HIGH",
      decision: "Workflow incomplete. Preparation input gate failed.",
    },
    {
      ...primary,
      id: "WF-10477",
      product: "Arc Mechanical Keyboard",
      sku: "ARC-K2-SL",
      unit: "UNIT-008416",
      route: "Integration trace",
      status: "COMPLETED",
      outcome: "EXCEPTION",
      stages: [
        receiving,
        prep,
        makeStage("Pack", "FAIL", {
          recommendation: "Stop",
          explanation: "An additional object is visible in the open box. Stop recommended.",
        }),
        makeStage("Returns", undefined, {
          status: "SKIPPED",
          explanation: "No return was recorded.",
        }),
        makeStage("Recovery", undefined, {
          status: "SKIPPED",
          explanation:
            "No valid named fee line provided. A sale invoice cannot be reconciled as a fee line.",
          modelCalls: [],
        }),
      ],
      reviewReason: "Extra object identified during pack inspection",
      priority: "MEDIUM",
      decision:
        "Inspection trace completed with a packing exception. Completion does not imply a clean outcome.",
    },
    {
      ...primary,
      id: "WF-10476",
      product: "Orbit USB-C Hub",
      sku: "ORB-U7-BK",
      unit: "UNIT-008415",
      route: "FBA",
      status: "PENDING",
      outcome: undefined,
      stages: [makeStage("Receiving"), makeStage("Prep"), makeStage("Recovery")],
      reviewReason: undefined,
      priority: undefined,
      decision: "Waiting for receiving evidence.",
    },
    {
      ...primary,
      id: "WF-10475",
      product: "Pulse Smart Watch",
      sku: "PLS-W4-SV",
      unit: "UNIT-008414",
      route: "Direct fulfilment",
      status: "BLOCKED",
      outcome: "INCOMPLETE",
      stages: [
        receiving,
        makeStage("Pack", undefined, {
          status: "SERVICE_UNAVAILABLE",
          explanation: "Pack service was unavailable in this example snapshot.",
          error: "SERVICE_UNAVAILABLE",
        }),
        makeStage("Recovery"),
      ],
      reviewReason: "Pack inspection service unavailable",
      priority: "LOW",
      decision: "Paused pending service availability.",
    },
  ],
  health: [
    {
      name: "Orchestrator",
      state: "AVAILABLE",
      latency: 42,
      detail: "Accepting orchestration requests",
    },
    { name: "Receiving", state: "AVAILABLE", latency: 218, detail: "Inspection service available" },
    { name: "Prep", state: "AVAILABLE", latency: 184, detail: "Preparation service available" },
    {
      name: "Pack",
      state: "DEGRADED",
      latency: 892,
      detail: "One example workflow blocked by service availability",
    },
    {
      name: "Returns",
      state: "AVAILABLE",
      latency: 246,
      detail: "Return inspection service available",
    },
    {
      name: "Recovery",
      state: "AVAILABLE",
      latency: 163,
      detail: "Fee reconciliation service available",
    },
  ],
  events: [
    {
      id: "e1",
      workflowId: "WF-10482",
      stage: "Returns",
      text: "Human review requested",
      timestamp: time,
      tone: "warning",
    },
    {
      id: "e2",
      workflowId: "WF-10481",
      stage: "Orchestrator",
      text: "Final outcome: CLEAN",
      timestamp: "2026-10-10T04:22:42Z",
      tone: "success",
    },
    {
      id: "e3",
      workflowId: "WF-10480",
      stage: "Recovery",
      text: "Fee discrepancy identified",
      timestamp: "2026-10-10T04:20:11Z",
      tone: "warning",
    },
    {
      id: "e4",
      workflowId: "WF-10479",
      stage: "Prep",
      text: "Inspection snapshot: running",
      timestamp: "2026-10-10T04:18:36Z",
      tone: "info",
    },
    {
      id: "e5",
      workflowId: "WF-10478",
      stage: "Prep",
      text: "Photo count validation failed",
      timestamp: "2026-10-10T04:16:09Z",
      tone: "danger",
    },
  ],
};
