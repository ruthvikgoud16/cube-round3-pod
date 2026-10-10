import { describe, it, expect } from "vitest";
import { fixtureSnapshot } from "@/lib/commerce/fixtures";
import { orchestrationStations, signalDirection, stationTone } from "@/lib/commerce/orchestration";

describe("Orchestration presentation boundary", () => {
  it("shows five specialists without inventing missing stages or signals", () => {
    const workflow = fixtureSnapshot.workflows[0];
    if (!workflow) throw new Error("Expected fixture workflow");
    const stations = orchestrationStations(workflow, { changedStages: new Set() });
    expect(stations).toHaveLength(5);
    expect(stations.every((station) => station.signal === "none")).toBe(true);
    expect(stations.find((station) => station.name === "Pack")?.stage).toBeUndefined();
    expect(workflow.stages.map((stage) => stage.name)).toEqual([
      "Receiving",
      "Prep",
      "Returns",
      "Recovery",
    ]);
  });
  it("only uses transition input to signal confirmed results and running instructions", () => {
    const stage = fixtureSnapshot.workflows[0]?.stages[0];
    if (!stage) throw new Error("Expected fixture stage");
    expect(signalDirection(stage, false)).toBe("none");
    expect(signalDirection(stage, true)).toBe("inbound");
    expect(signalDirection({ ...stage, status: "RUNNING", verdict: undefined }, true)).toBe(
      "outbound",
    );
    for (const status of ["SKIPPED", "WAITING", "SERVICE_UNAVAILABLE"] as const) {
      expect(signalDirection({ ...stage, status }, true)).toBe("none");
      expect(stationTone({ ...stage, status })).toBe("neutral");
    }
  });
  it("keeps failure and review semantics distinct", () => {
    const stage = fixtureSnapshot.workflows[0]?.stages[0];
    if (!stage) throw new Error("Expected fixture stage");
    expect(stationTone({ ...stage, verdict: "FAIL", review: true })).toBe("danger");
    expect(stationTone({ ...stage, verdict: "UNCERTAIN" })).toBe("warning");
  });
});
