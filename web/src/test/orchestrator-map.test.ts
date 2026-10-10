import { describe, expect, it } from "vitest";
import { workflowFromBundle } from "@/lib/commerce/orchestrator";

describe("orchestrator mapping", () => {
  it("keeps a blocked exception blocked and does not turn uncertain into a pass", () => {
    const workflow = workflowFromBundle({
      workflow: {
        workflow_id: "WF-org_demo_alpha-PRODUCT-04",
        subject_id: "PRODUCT-04",
        status: "BLOCKED",
        status_reason: "a person must decide: receiving, prep, pack",
        context: { route: "fba", product_name: "Oblique Sally tech pouch, Tan", sku: "8906126921460" },
        timestamps: { updated_at: "2026-10-09T16:53:27Z" },
        stage_results: [
          { stage: "receiving", agent_id: "receiving-manager@1.0.0", state: "completed", verdict: "UNCERTAIN", record_id: "RCV-1", needs_human: true, finished_at: "2026-10-09T16:53:00Z" },
          { stage: "prep", agent_id: "prep-manager@1.0.0", state: "completed", verdict: "FAIL", record_id: "PRP-1", needs_human: true },
          { stage: "pack", agent_id: "pack-manager@1.0.0", state: "completed", verdict: "FAIL", record_id: "PCK-1", needs_human: true },
        ],
        final_outcome: { outcome: "EXCEPTION", reason: "Failed verdict from: prep, pack.", needs_human: true, claimable_usd: null },
        overrides: [],
        transitions: [],
      },
      evidence: {
        "RCV-1": {
          record_id: "RCV-1",
          stage: "receiving",
          content_hash: "abc",
          decision: { verdict: "UNCERTAIN", reason: "Holding for a person. Path /Users/ruthvikgoud/secret", needs_human: true },
          checks: [{ check_key: "identity_match", verdict: "PASS", expected: "sku", observed: "yes", confidence: 0.9 }],
          model: { name: "claude", version: "claude-sonnet-4-5", calls: 1, cost_usd: null },
          inputs: [{ ref: "PRODUCT-04/receiving/01.jpg", kind: "image", sha256: "def", data_base64: "hidden" }],
          upstream_refs: [],
        },
        "RCY-1": {
          record_id: "RCY-1",
          stage: "recovery",
          decision: { verdict: "UNCERTAIN", reason: "No fee report lines were supplied.", needs_human: false },
          model: { name: "rules", calls: 0, cost_usd: null },
          checks: [],
          inputs: [],
        },
      },
    });
    expect(workflow.status).toBe("BLOCKED");
    expect(workflow.outcome).toBe("EXCEPTION");
    expect(workflow.stages[0]?.verdict).toBe("UNCERTAIN");
    expect(workflow.stages[0]?.review).toBe(true);
    expect(workflow.stages[0]?.explanation).toContain("[local folder]");
    expect(workflow.stages[0]?.explanation).not.toContain("/Users/");
    expect(workflow.stages[0]?.modelCalls).toHaveLength(1);
    expect(workflow.stages[0]?.modelCalls[0]?.cost).toBeUndefined();
    expect(JSON.stringify(workflow)).not.toContain("hidden");
    expect(workflow.stages[1]?.verdict).toBe("FAIL");
  });
});
