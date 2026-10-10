import { describe, expect, it } from "vitest";
import { createRouter } from "@tanstack/react-router";
import { QueryClient } from "@tanstack/react-query";
import { routeTree } from "@/routeTree.gen";
import { fixtureSnapshot } from "@/lib/commerce/fixtures";
import { exampleAdapter } from "@/lib/commerce/service";
describe("CUBE commerce frontend", () => {
  it("matches every workspace URL and workflow details", () => {
    const router = createRouter({ routeTree, context: { queryClient: new QueryClient() } });
    for (const path of [
      "/",
      "/workflows",
      "/workflows/WF-10477",
      "/evidence",
      "/review",
      "/health",
    ]) {
      expect(router.matchRoutes(path).at(-1)?.routeId).not.toBe("__root__");
    }
    expect(router.matchRoutes("/workflows/WF-10477").at(-1)?.routeId).toBe(
      "/workflows/$workflowId",
    );
  });
  it("does not equate completion with a clean outcome", () => {
    expect(
      fixtureSnapshot.workflows.some((w) => w.status === "COMPLETED" && w.outcome === "EXCEPTION"),
    ).toBe(true);
  });
  it("supports alternative paths and five-stage integration traces", () => {
    expect(
      fixtureSnapshot.workflows
        .find((w) => w.route === "Integration trace")
        ?.stages.map((s) => s.name),
    ).toEqual(["Receiving", "Prep", "Pack", "Returns", "Recovery"]);
    const direct = fixtureSnapshot.workflows.find((w) => w.route === "Direct fulfilment");
    expect(direct?.stages.some((s) => s.name === "Prep")).toBe(false);
  });
  it("never calls a model after the invalid Prep photo-count gate", () => {
    const invalid = fixtureSnapshot.workflows
      .flatMap((w) => w.stages)
      .find((s) => s.error === "INVALID_PHOTO_COUNT");
    expect(invalid?.modelCalls).toHaveLength(0);
  });
  it("keeps examples explicit and override actions unavailable", async () => {
    expect((await exampleAdapter.loadSnapshot()).source).toBe("example");
    expect(exampleAdapter.submitOverride).toBeUndefined();
    expect(fixtureSnapshot.workflows.every((w) => !w.override)).toBe(true);
  });
});
