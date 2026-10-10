import { useState } from "react";
import { Link } from "@tanstack/react-router";
import {
  Activity,
  ArrowUpRight,
  ArrowRight,
  GitBranch,
  CheckCheck,
  UsersRound,
  ChevronDown,
  CalendarDays,
  Download,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCommerce } from "@/lib/commerce/service";
import { StatusBadge, HealthIndicator, SectionHeading } from "./primitives";
import { WorkflowTable } from "./workflow-table";
import { EvidenceChain } from "./evidence-chain";
import type { CommerceEvent, Outcome, Workflow } from "@/lib/commerce/types";
export function PageHeading({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <span className="eyebrow">
          <span className="eyebrow-line" />
          COMMERCE INTELLIGENCE
        </span>
        <h1>
          {title}
          <span className="heading-dot">.</span>
        </h1>
        <p>{subtitle}</p>
      </div>
      <div className="page-heading-actions">{children}</div>
    </div>
  );
}
export function EventTimeline({ events }: { events: CommerceEvent[] }) {
  return (
    <div className="event-timeline">
      {events.map((e) => (
        <div className="timeline-event" key={e.id}>
          <span className={`event-dot tone-${e.tone}`} />
          <div>
            <strong>{e.text}</strong>
            <span>
              <Link to="/workflows/$workflowId" params={{ workflowId: e.workflowId }}>
                {e.workflowId}
              </Link>
              <span>·</span>
              {e.stage}
            </span>
          </div>
          <time>{e.timestamp.slice(11, 16)}</time>
        </div>
      ))}
    </div>
  );
}
export function FinalOutcomeSummary({ workflows }: { workflows: Workflow[] }) {
  const outcomes: Outcome[] = [
    "CLEAN",
    "EXCEPTION",
    "INCOMPLETE",
    "NEEDS_REVIEW",
    "CLAIM_RECOMMENDED",
  ];
  const decided = workflows.filter((w) => w.outcome).length;
  return (
    <div className="outcome-summary">
      <div className="outcome-stacked-bar">
        {outcomes.map((o) => (
          <span
            key={o}
            className={`outcome-bar-${o.toLowerCase()}`}
            style={{ flexGrow: workflows.filter((w) => w.outcome === o).length }}
          />
        ))}
      </div>
      <div className="outcome-list">
        {outcomes.map((o) => (
          <div key={o}>
            <span>
              <i className={`outcome-bar-${o.toLowerCase()}`} />
              {o
                .replaceAll("_", " ")
                .toLowerCase()
                .replace(/^./, (s) => s.toUpperCase())}
            </span>
            <strong>
              {workflows.filter((w) => w.outcome === o).length}
              <small>
                {decided
                  ? Math.round((workflows.filter((w) => w.outcome === o).length / decided) * 100)
                  : 0}
                %
              </small>
            </strong>
          </div>
        ))}
      </div>
    </div>
  );
}
export function Overview() {
  const { snapshot } = useCommerce();
  const [selectedId, setSelectedId] = useState(snapshot.workflows[0]?.id || "");
  const [showAll, setShowAll] = useState(false);
  const [dateOpen, setDateOpen] = useState(false);
  const orchestrator = snapshot.health.find((h) => h.name === "Orchestrator");
  const selected = snapshot.workflows.find((w) => w.id === selectedId) || snapshot.workflows[0];
  const completed = snapshot.workflows.filter((w) => w.status === "COMPLETED").length;
  const reviews = snapshot.workflows.filter((w) => w.reviewReason).length;
  const exportSnapshot = () => {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(snapshot, null, 2)], { type: "application/json" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = `cube-${snapshot.source}-snapshot.json`;
    a.click();
    URL.revokeObjectURL(url);
  };
  return (
    <div className="overview-layout">
      <PageHeading
        title="Operations overview"
        subtitle="Every agent. Every decision. One clear view."
      >
        <div className="date-filter-wrap">
          <Button variant="outline" size="sm" onClick={() => setDateOpen(!dateOpen)}>
            <CalendarDays />
            10 Oct 2026
            <ChevronDown />
          </Button>
          {dateOpen && (
            <div className="date-popup">
              <strong>Example snapshot</strong>
              <p>10 October 2026 · 04:24 UTC</p>
              <span>No live history source connected.</span>
            </div>
          )}
        </div>
        <Button variant="outline" size="sm" onClick={exportSnapshot}>
          <Download />
          Export
        </Button>
      </PageHeading>
      <div className="metric-grid">
        <div className="metric-card">
          <div className="metric-label">
            <span>Orchestrator</span>
            <Activity size={16} />
          </div>
          <div className="metric-value health-value">
            <span
              className={`health-dot ${orchestrator?.state === "AVAILABLE" ? "tone-success" : "tone-warning"}`}
            />
            {orchestrator?.state === "AVAILABLE"
              ? "Operational"
              : orchestrator?.state === "DEGRADED"
                ? "Degraded"
                : "Unavailable"}
          </div>
          <div className="metric-foot">
            <span>
              {snapshot.source === "example"
                ? "Example service status"
                : "Connected service status"}
            </span>
            <code>{orchestrator?.latency !== undefined ? `${orchestrator.latency} ms` : "—"}</code>
          </div>
          <div className="metric-mini-line">
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">
            <span>Stored workflows</span>
            <GitBranch size={16} />
          </div>
          <div className="metric-value">
            {snapshot.workflows.length.toString().padStart(2, "0")}
            <span className="metric-unit">workflows</span>
          </div>
          <div className="metric-foot">
            <span>
              <i className="tiny-dot tone-info" />
              {snapshot.workflows.filter((w) => w.status === "IN_PROGRESS").length} in progress
            </span>
            <span>{snapshot.workflows.filter((w) => w.status === "PENDING").length} pending</span>
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">
            <span>Completed workflows</span>
            <CheckCheck size={16} />
          </div>
          <div className="metric-value">
            {completed.toString().padStart(2, "0")}
            <span className="metric-unit">completed</span>
          </div>
          <div className="metric-foot">
            <span>
              <i className="tiny-dot tone-success" />
              {snapshot.workflows.filter((w) => w.outcome === "CLEAN").length} clean outcome
            </span>
            <span className="text-warning">
              {
                snapshot.workflows.filter((w) => w.status === "COMPLETED" && w.outcome !== "CLEAN")
                  .length
              }{" "}
              with exception
            </span>
          </div>
        </div>
        <div className="metric-card metric-review">
          <div className="metric-label">
            <span>Human review</span>
            <UsersRound size={16} />
          </div>
          <div className="metric-value">
            {reviews.toString().padStart(2, "0")}
            <span className="metric-unit">open cases</span>
          </div>
          <div className="metric-foot">
            <span className="text-warning">
              {snapshot.workflows.filter((w) => w.priority === "HIGH").length} high priority
            </span>
            <Link to="/review">
              View queue <ArrowUpRight size={12} />
            </Link>
          </div>
        </div>
      </div>
      <div className="agents-strip">
        <span className="agents-strip-label">
          <Activity size={14} />
          AGENT FLEET
        </span>
        {snapshot.health
          .filter((h) => h.name !== "Orchestrator")
          .map((h) => (
            <HealthIndicator agent={h} key={h.name} />
          ))}
        <Button asChild variant="ghost" size="icon" title="View system health">
          <Link to="/health" aria-label="View system health">
            <ArrowUpRight />
          </Link>
        </Button>
      </div>
      <section className="evidence-section">
        <SectionHeading title="Agent orchestration" eyebrow="THE COMMERCE INTELLIGENCE CORE">
          <div className="section-tools">
            <span className="static-snapshot">
              <span className="health-dot tone-info" />
              {snapshot.source === "example" ? "Example snapshot" : "Connected source"}
            </span>
            <select
              aria-label="Select workflow"
              value={selected?.id}
              onChange={(e) => setSelectedId(e.target.value)}
            >
              {snapshot.workflows.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.id} · {w.product}
                </option>
              ))}
            </select>
            <Button asChild variant="ghost" size="icon" title="Open workflow">
              <Link
                to="/workflows/$workflowId"
                params={{ workflowId: selected?.id || "" }}
                aria-label="Open selected workflow"
              >
                <ArrowUpRight />
              </Link>
            </Button>
          </div>
        </SectionHeading>
        {selected ? (
          <EvidenceChain key={selected.id} workflow={selected} />
        ) : (
          <p>No workflows supplied.</p>
        )}
      </section>
      <div className="overview-secondary">
        <section className="outcomes-section">
          <SectionHeading title="Commerce outcomes">
            <span className="section-caption">
              {snapshot.workflows.filter((w) => w.outcome).length} decided
            </span>
          </SectionHeading>
          <FinalOutcomeSummary workflows={snapshot.workflows} />
        </section>
        <section className="recent-section">
          <SectionHeading title="Recent activity">
            <Button variant="ghost" size="sm" onClick={() => setShowAll(!showAll)}>
              {showAll ? "Show less" : "View all"}
              <ArrowRight />
            </Button>
          </SectionHeading>
          <EventTimeline events={showAll ? snapshot.events : snapshot.events.slice(0, 4)} />
        </section>
        <section className="attention-section">
          <div className="attention-icon">
            <UsersRound size={21} />
          </div>
          <span className="eyebrow">HUMAN IN THE LOOP</span>
          <h2>
            A decision needs
            <br />
            your perspective.
          </h2>
          <p>
            {reviews} cases are awaiting review.
            <br />
            Keep exceptions from becoming blind spots.
          </p>
          <div className="attention-priorities">
            <span>
              <i className="tiny-dot tone-danger" />
              {snapshot.workflows.filter((w) => w.priority === "HIGH").length} high priority
            </span>
            <span>
              <i className="tiny-dot tone-warning" />
              {snapshot.workflows.filter((w) => w.priority === "MEDIUM").length} medium
            </span>
          </div>
          <Button asChild variant="outline">
            <Link to="/review">
              Open review queue
              <ArrowRight />
            </Link>
          </Button>
        </section>
      </div>
      <section className="workflows-section">
        <SectionHeading title="Workflows">
          <Button asChild variant="ghost" size="sm">
            <Link to="/workflows">
              View all workflows
              <ArrowRight />
            </Link>
          </Button>
        </SectionHeading>
        <WorkflowTable
          workflows={snapshot.workflows}
          onSelect={(w) => setSelectedId(w.id)}
          selectedId={selected?.id}
        />
      </section>
      <div className="status-counts">
        {["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED", "BLOCKED", "RECOVERY_REQUIRED"].map(
          (status) => (
            <span key={status}>
              <StatusBadge value={status} small />
              <strong>{snapshot.workflows.filter((w) => w.status === status).length}</strong>
            </span>
          ),
        )}
      </div>
    </div>
  );
}
