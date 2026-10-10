import type { Stage, Workflow } from "./types";

export const specialists = ["Receiving", "Prep", "Pack", "Returns", "Recovery"] as const;
export type SignalDirection = "inbound" | "outbound" | "none";
// Animation input is independent of presentation and never manufactures events.
export interface OrchestrationMotion {
  changedStages: ReadonlySet<string>;
}
export function signalDirection(stage: Stage | undefined, changed: boolean): SignalDirection {
  if (!stage || !changed || /WAITING|SKIPPED|SERVICE_UNAVAILABLE/.test(stage.status)) return "none";
  if (stage.status === "RUNNING") return "outbound";
  if (stage.verdict || /COMPLETED|FAILED|BLOCKED/.test(stage.status)) return "inbound";
  return "none";
}
export function stationTone(stage?: Stage) {
  if (!stage || /WAITING|SKIPPED|SERVICE_UNAVAILABLE/.test(stage.status)) return "neutral";
  if (stage.verdict === "FAIL" || stage.status === "FAILED") return "danger";
  if (stage.review || stage.verdict === "UNCERTAIN" || stage.status === "BLOCKED") return "warning";
  if (stage.verdict === "PASS") return "success";
  return stage.status === "RUNNING" ? "info" : "neutral";
}
export function orchestrationStations(workflow: Workflow, motion: OrchestrationMotion) {
  return specialists.map((name) => {
    const stage = workflow.stages.find((s) => s.name.toLowerCase() === name.toLowerCase());
    const changed = !!stage && motion.changedStages.has(`${workflow.id}:${stage.id}`);
    return { name, stage, tone: stationTone(stage), signal: signalDirection(stage, changed) };
  });
}
