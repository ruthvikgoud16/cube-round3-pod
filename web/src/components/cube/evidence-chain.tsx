import { useId, useState } from "react";
import {
  ArrowRight,
  ChevronRight,
  Cpu,
  FileText,
  GitBranch,
  PanelRightOpen,
  UsersRound,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { useCommerce } from "@/lib/commerce/service";
import type { Workflow } from "@/lib/commerce/types";
import { orchestrationStations } from "@/lib/commerce/orchestration";
import { ProductSymbol } from "./workflow-table";
import { cn } from "@/lib/utils";
import { EvidenceInspector } from "./inspector";
import { StatusBadge, StageIcon } from "./primitives";
import headphones from "@/assets/headphones.jpg";

const paths = [
  "M 500 205 L 500 145",
  "M 395 255 C 335 255 325 224 265 224",
  "M 605 255 C 665 255 675 224 735 224",
  "M 425 327 C 405 388 355 420 315 420",
  "M 575 327 C 595 388 645 420 685 420",
];
const mobilePaths = [
  "M 500 486 V 247",
  "M 387 520 C 240 505 240 410 240 382",
  "M 613 520 C 760 505 760 410 760 382",
  "M 380 675 C 330 710 270 705 240 705",
  "M 620 675 C 670 710 730 705 760 705",
];

export function EvidenceChain({
  workflow,
  compact = false,
}: {
  workflow: Workflow;
  compact?: boolean;
}) {
  const { snapshot, changedStages } = useCommerce();
  const [selection, setSelection] = useState<string>();
  const [coreOpen, setCoreOpen] = useState(false);
  const [offRoute, setOffRoute] = useState<string>();
  const uid = useId().replaceAll(":", "");
  const stations = orchestrationStations(workflow, { changedStages });
  const selected = workflow.stages.find((stage) => stage.id === selection);
  const records = workflow.stages.reduce((total, stage) => total + stage.evidence.length, 0);
  const events = snapshot.events.filter((event) => event.workflowId === workflow.id).slice(0, 3);
  const active = stations.some((station) => station.signal !== "none");
  const closeCore = () => {
    setCoreOpen(false);
    setOffRoute(undefined);
  };
  return (
    <div
      className={cn(
        "evidence-chain-section orchestration-hero",
        compact && "orchestration-compact",
      )}
    >
      <div className="selected-product">
        <div className="product-identity">
          {workflow.product.includes("Headphones") ? (
            <img
              src={headphones}
              alt="Illustrative catalog product, not inspection evidence"
              width={37}
              height={37}
            />
          ) : (
            <ProductSymbol name={workflow.product} />
          )}
          <div>
            <strong>{workflow.product}</strong>
            <div>
              <code>{workflow.id}</code>
              <span>·</span>
              <span>{workflow.unit}</span>
            </div>
          </div>
        </div>
        <div className="product-route">
          <GitBranch size={13} />
          <span>{workflow.route}</span>
          <StatusBadge value={workflow.status} small />
        </div>
      </div>
      <div className="orchestration-viewport" aria-label="Commerce agent orchestration">
        <div className="orbit-caption">
          <span className="eyebrow">CUBE / ORCHESTRATION FIELD</span>
          <span>
            {snapshot.source === "example" ? "FIXTURE SNAPSHOT · NOT LIVE" : "BACKEND SNAPSHOT"}
          </span>
        </div>
        <div className="orbit-legend">
          <span className="orbit-legend-line" /> Evidence & decisions
        </div>
        <svg
          className="orbit-network"
          viewBox="0 0 1000 560"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <defs>
            <marker
              id={`${uid}-arrow`}
              viewBox="0 0 8 8"
              refX="6"
              refY="4"
              markerWidth="5"
              markerHeight="5"
              orient="auto-start-reverse"
            >
              <path d="M 1 1 L 6 4 L 1 7" fill="none" stroke="context-stroke" />
            </marker>
          </defs>
          <ellipse className="orbit-guide" cx="500" cy="285" rx="320" ry="175" />
          <ellipse className="orbit-guide orbit-guide-inner" cx="500" cy="285" rx="244" ry="118" />
          <path className="orbit-axis" d="M 500 40 V 525 M 50 285 H 950" />
          {stations.map((station, i) => (
            <g
              key={station.name}
              className={cn(
                "orbit-connection",
                `tone-${station.tone}`,
                !station.stage && "connection-off-route",
                station.stage?.status === "RUNNING" && "connection-running",
              )}
            >
              <path
                id={`${uid}-path-${i}`}
                d={paths[i]}
                markerStart={`url(#${uid}-arrow)`}
                markerEnd={`url(#${uid}-arrow)`}
              />
              {station.signal !== "none" && (
                <path
                  key={`${workflow.id}-${station.stage?.status}-${station.stage?.verdict}`}
                  className={cn("orbit-signal", station.signal === "inbound" && "signal-inbound")}
                  d={paths[i]}
                  pathLength="100"
                />
              )}
            </g>
          ))}
        </svg>
        <svg
          className="orbit-network orbit-network-mobile"
          viewBox="0 0 1000 1000"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <defs>
            <marker
              id={`${uid}-mobile-arrow`}
              viewBox="0 0 8 8"
              refX="6"
              refY="4"
              markerWidth="5"
              markerHeight="5"
              orient="auto-start-reverse"
            >
              <path d="M 1 1 L 6 4 L 1 7" fill="none" stroke="context-stroke" />
            </marker>
          </defs>
          {stations.map((station, i) => (
            <g
              key={station.name}
              className={cn(
                "orbit-connection",
                `tone-${station.tone}`,
                !station.stage && "connection-off-route",
              )}
            >
              <path
                d={mobilePaths[i]}
                markerStart={`url(#${uid}-mobile-arrow)`}
                markerEnd={`url(#${uid}-mobile-arrow)`}
              />
              {station.signal !== "none" && (
                <path
                  className={cn("orbit-signal", station.signal === "inbound" && "signal-inbound")}
                  d={mobilePaths[i]}
                  pathLength="100"
                />
              )}
            </g>
          ))}
        </svg>
        <Button
          variant="ghost"
          className={cn(
            "orchestrator-core",
            active && "core-received",
            coreOpen && "core-selected",
          )}
          aria-label="Inspect orchestrator decision"
          aria-pressed={coreOpen}
          onClick={() => {
            setOffRoute(undefined);
            setCoreOpen(true);
          }}
        >
          <span className="core-ring core-ring-outer" />
          <span className="core-ring core-ring-middle" />
          <span className="core-ring core-ring-inner" />
          <span className="core-content">
            <span className="core-chip">
              <Cpu size={28} />
            </span>
            <span className="core-kicker">CENTRAL INTELLIGENCE</span>
            <strong>Orchestrator</strong>
            <span className="core-records">{records} evidence records</span>
            <StatusBadge value={workflow.outcome} small />
          </span>
          <span className="core-coordinate">CUBE · O / 01</span>
        </Button>
        {stations.map(({ name, stage, tone, signal }, i) => (
          <Button
            key={name}
            variant="ghost"
            title={
              stage
                ? `${stage.status.replaceAll("_", " ")} · ${stage.explanation}`
                : "Not present in the supplied route"
            }
            className={cn(
              "agent-station",
              `station-${i}`,
              `tone-${tone}`,
              !stage && "station-off-route",
              stage?.status === "SKIPPED" && "station-off-route",
              selected?.id === stage?.id && stage && "station-selected",
              signal !== "none" && "station-received",
            )}
            aria-label={`Inspect ${name}${stage ? "" : " — not on this route"}`}
            aria-pressed={!!stage && selected?.id === stage.id}
            onClick={() => {
              if (stage) setSelection(stage.id);
              else {
                setOffRoute(name);
                setCoreOpen(true);
              }
            }}
          >
            <span className="station-heading">
              <span className="station-emblem">
                <StageIcon name={name} size={21} />
              </span>
              <span>
                <span className="station-index">SPECIALIST / 0{i + 1}</span>
                <strong>{name}</strong>
              </span>
              <ChevronRight size={13} />
            </span>
            <span className="station-verdict">
              {stage ? (
                <StatusBadge value={stage.verdict || stage.status} small />
              ) : (
                <span className="off-route-label">NOT ON THIS ROUTE</span>
              )}
              {stage?.review && <UsersRound size={13} aria-label="Human review required" />}
            </span>
            <span className="station-footer">
              <span>
                <FileText size={11} /> {stage?.evidence.length || 0} records
              </span>
              <span>{stage?.status.replaceAll("_", " ").toLowerCase() || "off route"}</span>
            </span>
            <span className="station-port" />
          </Button>
        ))}
        <div className="orbit-bottom-label">
          <span className="health-dot tone-neutral" /> {workflow.stages.length} supplied stages ·{" "}
          {stations.filter((s) => !s.stage).length} off-route specialists
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="orbit-inspect-toggle"
          title="Open decision inspector"
          aria-label="Open decision inspector"
          onClick={() => setCoreOpen(true)}
        >
          <PanelRightOpen size={17} />
        </Button>
      </div>
      <div className="orchestration-route">
        <span className="eyebrow">EXECUTION ROUTE</span>
        <ol>
          {workflow.stages.map((stage, index) => (
            <li key={stage.id}>
              <Button
                variant="ghost"
                onClick={() => setSelection(stage.id)}
                title={`Inspect ${stage.name}`}
              >
                <span
                  className={cn(
                    "route-dot",
                    `tone-${stations.find((s) => s.stage?.id === stage.id)?.tone || "neutral"}`,
                  )}
                />
                {stage.name}
              </Button>
              {index < workflow.stages.length - 1 && <ArrowRight size={11} />}
            </li>
          ))}
        </ol>
        <span className="route-outcome">
          <StatusBadge value={workflow.outcome} small />
        </span>
      </div>
      <div className="orchestration-decision-summary">
        <Cpu size={13} />
        <strong>Orchestrator decision</strong>
        <span>{workflow.decision}</span>
      </div>
      <div className="orchestration-event-strip">
        <span className="eyebrow">
          {snapshot.source === "example" ? "EXAMPLE EVENTS" : "RECORDED EVENTS"}
        </span>
        {events.length ? (
          events.map((event) => (
            <span className="orbit-event" key={event.id}>
              <time>{event.timestamp.slice(11, 16)}</time>
              <i className={`route-dot tone-${event.tone}`} />
              <span>{event.text}</span>
            </span>
          ))
        ) : (
          <span className="orbit-no-events">No events supplied for this workflow.</span>
        )}
      </div>
      <EvidenceInspector
        stage={selected}
        workflow={workflow}
        onClose={() => setSelection(undefined)}
      />
      <Sheet
        open={coreOpen}
        onOpenChange={(open) => {
          if (!open) closeCore();
        }}
      >
        <SheetContent className="inspector-sheet overflow-y-auto w-full sm:max-w-[540px]">
          <SheetHeader>
            <span className="eyebrow">
              ORCHESTRATOR · {snapshot.source === "example" ? "EXAMPLE DETAILS" : "CONNECTED DATA"}
            </span>
            <SheetTitle className="inspector-title">
              <Cpu size={25} />
              Workflow decision
            </SheetTitle>
            <SheetDescription>
              {workflow.id} / {workflow.unit}
            </SheetDescription>
          </SheetHeader>
          {offRoute && (
            <div className="detail-section">
              <h3>{offRoute}</h3>
              <p>
                This specialist is not present in the supplied workflow route. No execution or
                evidence is inferred.
              </p>
            </div>
          )}
          <div className="detail-section">
            <h3>Workflow status</h3>
            <StatusBadge value={workflow.status} />
          </div>
          <div className="detail-section">
            <h3>Final commerce outcome</h3>
            <StatusBadge value={workflow.outcome} />
            <p className="inspector-explanation">{workflow.decision}</p>
          </div>
          <div className="detail-section">
            <h3>Supplied route · {workflow.route}</h3>
            <ol className="core-route-list">
              {workflow.stages.map((stage) => (
                <li key={stage.id}>
                  <StageIcon name={stage.name} size={16} />
                  <strong>{stage.name}</strong>
                  <StatusBadge value={stage.verdict || stage.status} small />
                  <span>{stage.evidence.length} records</span>
                </li>
              ))}
            </ol>
          </div>
          <div className="detail-section">
            <h3>Accumulated evidence · {records}</h3>
            {workflow.stages.flatMap((stage) =>
              stage.evidence.map((record) => (
                <div className="core-evidence-reference" key={`${stage.id}:${record.id}`}>
                  <FileText size={14} />
                  <div>
                    <strong>{record.label}</strong>
                    <code>
                      {record.id} · {stage.name}
                    </code>
                    {record.upstream.length > 0 && (
                      <small>Upstream: {record.upstream.join(", ")}</small>
                    )}
                  </div>
                </div>
              )),
            )}
            {!records && <p>No evidence references supplied.</p>}
          </div>
          {workflow.reviewReason && (
            <div className="review-notice">
              <strong>Human review required</strong>
              <p>{workflow.reviewReason}</p>
            </div>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}
