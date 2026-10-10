import { useState } from "react";
import { Link } from "@tanstack/react-router";
import {
  ArrowLeft,
  ArrowUpRight,
  Search,
  FileText,
  Fingerprint,
  ShieldCheck,
  Activity,
  PlugZap,
  UsersRound,
  CircleAlert,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCommerce } from "@/lib/commerce/service";
import { PageHeading, EventTimeline } from "./overview";
import { WorkflowTable, ProductSymbol } from "./workflow-table";
import { EvidenceChain } from "./evidence-chain";
import { EvidenceInspector } from "./inspector";
import { SectionHeading, StatusBadge, StageIcon } from "./primitives";
import type { Stage, Workflow } from "@/lib/commerce/types";
export function WorkflowsPage() {
  const { snapshot } = useCommerce();
  return (
    <>
      <PageHeading
        title="Workflows"
        subtitle="Execution state and commerce outcomes, kept in focus."
      />
      <div className="list-summary">
        {["All workflows", "In progress", "Completed", "Blocked"].map((label, i) => (
          <div key={label}>
            <span>{label}</span>
            <strong>
              {i === 0
                ? snapshot.workflows.length
                : snapshot.workflows.filter(
                    (w) => w.status === ["ALL", "IN_PROGRESS", "COMPLETED", "BLOCKED"][i],
                  ).length}
            </strong>
          </div>
        ))}
      </div>
      <WorkflowTable workflows={snapshot.workflows} limit={8} />
    </>
  );
}
export function WorkflowDetail({ id }: { id: string }) {
  const { snapshot } = useCommerce();
  const w = snapshot.workflows.find((w) => w.id === id);
  if (!w)
    return (
      <div className="empty-state">
        <FileText />
        <h1>Workflow not found</h1>
        <Button asChild variant="outline">
          <Link to="/workflows">Back to workflows</Link>
        </Button>
      </div>
    );
  return (
    <>
      <Button asChild variant="ghost" size="sm" className="back-link">
        <Link to="/workflows">
          <ArrowLeft />
          All workflows
        </Link>
      </Button>
      <PageHeading title={w.id} subtitle={`${w.product} · ${w.unit}`}>
        <StatusBadge value={w.status} />
      </PageHeading>
      <div className="workflow-detail-meta">
        <div>
          <span>Fulfilment route</span>
          <strong>{w.route}</strong>
        </div>
        <div>
          <span>Product identifier</span>
          <code>{w.sku}</code>
        </div>
        <div>
          <span>Final commerce outcome</span>
          <StatusBadge value={w.outcome} />
        </div>
        <div>
          <span>Source</span>
          <strong>
            {snapshot.source === "example" ? "Frontend example" : "Connected backend"}
          </strong>
        </div>
      </div>
      <section>
        <SectionHeading title="Execution & evidence trace" eyebrow="ORDERED BY SUPPLIED ROUTE" />
        <EvidenceChain workflow={w} />
      </section>
      <div className="detail-columns">
        <section>
          <SectionHeading title="Decision record" />
          <div className="decision-record">
            <ShieldCheck />
            <div>
              <span className="eyebrow">ORCHESTRATOR DECISION</span>
              <h3>{w.decision}</h3>
              <dl>
                <dt>Human override</dt>
                <dd>
                  {w.override
                    ? `${w.override.actor} · ${w.override.reason} · ${w.override.timestamp}`
                    : "No human override recorded"}
                </dd>
                <dt>Final outcome</dt>
                <dd>
                  <StatusBadge value={w.outcome} />
                </dd>
                <dt>Human review</dt>
                <dd>{w.reviewReason || "Not required"}</dd>
              </dl>
              {w.reviewReason && (
                <Button asChild variant="outline" size="sm">
                  <Link to="/review">
                    Review case
                    <ArrowUpRight />
                  </Link>
                </Button>
              )}
            </div>
          </div>
        </section>
        <section>
          <SectionHeading title="Workflow activity" />
          <EventTimeline events={snapshot.events.filter((e) => e.workflowId === w.id)} />
          {!snapshot.events.some((e) => e.workflowId === w.id) && (
            <p className="subtle-note">No events supplied for this workflow.</p>
          )}
        </section>
      </div>
    </>
  );
}
export function EvidencePage() {
  const { snapshot } = useCommerce();
  const [query, setQuery] = useState("");
  const [stageFilter, setStageFilter] = useState("ALL");
  const [selected, setSelected] = useState<{ workflow: Workflow; stage: Stage }>();
  const records = snapshot.workflows
    .flatMap((workflow) =>
      workflow.stages.flatMap((stage) =>
        stage.evidence.map((evidence) => ({ workflow, stage, evidence })),
      ),
    )
    .filter(
      (r) =>
        (stageFilter === "ALL" || r.stage.name === stageFilter) &&
        `${r.workflow.id} ${r.evidence.id} ${r.evidence.label} ${r.evidence.hash}`
          .toLowerCase()
          .includes(query.toLowerCase()),
    );
  return (
    <>
      <PageHeading
        title="Evidence explorer"
        subtitle="Trace the records behind every agent recommendation."
      />
      <div className="explorer-tools">
        <label className="search-field">
          <Search />
          <input
            placeholder="Search workflow, evidence or hash…"
            aria-label="Search evidence"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>
        <select
          aria-label="Filter evidence by stage"
          value={stageFilter}
          onChange={(e) => setStageFilter(e.target.value)}
        >
          <option value="ALL">All stages</option>
          {["Receiving", "Prep", "Pack", "Returns", "Recovery"].map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
        <span>{records.length} example references</span>
      </div>
      <div className="evidence-grid">
        {records.map((r, i) => (
          <div className="evidence-explorer-item" key={`${r.workflow.id}-${r.evidence.id}-${i}`}>
            <div className="evidence-item-top">
              <span className="evidence-item-icon">
                <StageIcon name={r.stage.name} />
              </span>
              <StatusBadge value={r.stage.verdict || r.stage.status} small />
            </div>
            <span className="eyebrow">
              {r.stage.name} · {r.evidence.kind}
            </span>
            <h3>{r.evidence.label}</h3>
            <code>{r.evidence.id}</code>
            <div className="evidence-item-workflow">
              <Link to="/workflows/$workflowId" params={{ workflowId: r.workflow.id }}>
                {r.workflow.id}
              </Link>
              <span>{r.workflow.unit}</span>
            </div>
            <div className="evidence-hash">
              <Fingerprint size={13} />
              {r.evidence.hash || "Hash not supplied"}
            </div>
            <Button
              variant="ghost"
              onClick={() => setSelected({ workflow: r.workflow, stage: r.stage })}
            >
              Inspect record
              <ArrowUpRight />
            </Button>
          </div>
        ))}
      </div>
      {!records.length && (
        <div className="empty-state">
          <Search />
          <strong>No evidence matches your search.</strong>
        </div>
      )}
      {selected && (
        <EvidenceInspector
          workflow={selected.workflow}
          stage={selected.stage}
          onClose={() => setSelected(undefined)}
        />
      )}
    </>
  );
}
export function ReviewQueue() {
  const { snapshot, adapter } = useCommerce();
  const [filter, setFilter] = useState("ALL");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string>();
  const [reason, setReason] = useState("");
  const [result, setResult] = useState<{ actor: string; reason: string; timestamp: string }>();
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const rows = snapshot.workflows.filter(
    (w) =>
      w.reviewReason &&
      (filter === "ALL" || w.priority === filter) &&
      `${w.product} ${w.id} ${w.reviewReason}`.toLowerCase().includes(query.toLowerCase()),
  );
  const selected = snapshot.workflows.find((w) => w.id === selectedId);
  const submit = async () => {
    if (!selected || !reason.trim() || !adapter.submitOverride) return;
    setSubmitting(true);
    setError("");
    try {
      setResult(await adapter.submitOverride({ workflowId: selected.id, reason: reason.trim() }));
    } catch {
      setError("The override could not be submitted. No decision was recorded.");
    } finally {
      setSubmitting(false);
    }
  };
  return (
    <>
      <PageHeading title="Human review" subtitle="Human judgment, precisely where it matters." />
      <div className="review-summary">
        <UsersRound />
        <div>
          <strong>
            {snapshot.workflows.filter((w) => w.reviewReason).length} cases need attention
          </strong>
          <p>Agent recommendations are awaiting human review. No overrides have been invented.</p>
        </div>
        <span className="example-label">Example queue</span>
      </div>
      <div className="review-tools">
        <div className="segmented-tabs">
          {["ALL", "HIGH", "MEDIUM", "LOW"].map((f) => (
            <Button
              variant="ghost"
              key={f}
              className={filter === f ? "active" : ""}
              onClick={() => setFilter(f)}
            >
              {f === "ALL" ? "All cases" : f[0] + f.slice(1).toLowerCase() + " priority"}
              <span>
                {
                  snapshot.workflows.filter(
                    (w) => w.reviewReason && (f === "ALL" || w.priority === f),
                  ).length
                }
              </span>
            </Button>
          ))}
        </div>
        <label className="search-field">
          <Search size={15} />
          <input
            aria-label="Search review cases"
            placeholder="Search cases…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>
      </div>
      <div className="review-layout">
        <div className="review-list">
          {rows.map((w) => (
            <div
              className={selectedId === w.id ? "review-case selected" : "review-case"}
              key={w.id}
            >
              <div className="review-case-top">
                <code>{w.id}</code>
                <StatusBadge
                  value={w.priority === "HIGH" ? "HIGH PRIORITY" : `${w.priority} PRIORITY`}
                  small
                />
              </div>
              <h3>
                <ProductSymbol name={w.product} />
                {w.product}
              </h3>
              <p>{w.reviewReason}</p>
              <div className="review-case-foot">
                <StatusBadge value={w.outcome} small />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSelectedId(w.id);
                    setResult(undefined);
                    setReason("");
                    setError("");
                  }}
                >
                  Review case
                  <ArrowUpRight />
                </Button>
              </div>
            </div>
          ))}
          {!rows.length && (
            <div className="empty-state">
              <ShieldCheck />
              <strong>No cases match these filters.</strong>
            </div>
          )}
        </div>
        <section className="review-detail">
          {selected ? (
            <>
              <span className="eyebrow">REVIEW CASE · {selected.id}</span>
              <h2>{selected.product}</h2>
              <h3>Agent recommendation</h3>
              <p>
                {selected.stages.find((s) => s.review)?.recommendation ||
                  selected.stages.find((s) => s.review)?.explanation}
              </p>
              <h3>Orchestrator decision</h3>
              <p>{selected.decision}</p>
              <Button asChild variant="outline" size="sm">
                <Link to="/workflows/$workflowId" params={{ workflowId: selected.id }}>
                  View evidence trace
                  <ArrowUpRight />
                </Link>
              </Button>
              <div className="review-override">
                <h3>Human override</h3>
                <label>
                  Reason
                  <textarea
                    aria-label="Override reason"
                    placeholder="Record the reason for your decision…"
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                  />
                </label>
                <Button
                  disabled={!adapter.submitOverride || !reason.trim() || submitting}
                  onClick={submit}
                >
                  {submitting ? "Submitting…" : "Submit override"}
                </Button>
                {!adapter.submitOverride && (
                  <p className="subtle-note">
                    Unavailable in frontend preview. Connect the backend override action to submit a
                    decision.
                  </p>
                )}
                <p className="subtle-note">Actor and timestamp must be returned by your backend.</p>
                {error && <p role="alert">{error}</p>}
                {result && (
                  <div className="recorded-override">
                    <strong>Backend-recorded override</strong>
                    <p>{result.actor}</p>
                    <p>{result.reason}</p>
                    <time>{result.timestamp}</time>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="review-detail-empty">
              <UsersRound size={32} />
              <h2>Select a review case</h2>
              <p>No human decision has been recorded.</p>
            </div>
          )}
        </section>
      </div>
    </>
  );
}
export function SystemHealthPage() {
  const { snapshot } = useCommerce();
  return (
    <>
      <PageHeading
        title="System health"
        subtitle="A clear signal across the orchestration layer."
      />
      <div className="health-banner">
        <Activity size={25} />
        <div>
          <span className="eyebrow">EXAMPLE FLEET STATUS</span>
          <h2>
            {snapshot.health.some((h) => h.state !== "AVAILABLE")
              ? "Operating with a degraded service"
              : "All services available"}
          </h2>
          <p>Health values are fixture snapshots, not verified live telemetry.</p>
        </div>
        <StatusBadge
          value={snapshot.health.some((h) => h.state !== "AVAILABLE") ? "DEGRADED" : "AVAILABLE"}
        />
      </div>
      <div className="health-grid">
        {snapshot.health.map((h) => (
          <div className="service-health-item" key={h.name}>
            <div>
              <span className="service-icon">
                {h.name === "Orchestrator" ? <Activity /> : <StageIcon name={h.name} />}
              </span>
              <StatusBadge value={h.state} small />
            </div>
            <h2>{h.name}</h2>
            <p>{h.detail}</p>
            <dl>
              <dt>Response latency</dt>
              <dd>{h.latency !== undefined ? `${h.latency} ms` : "Not supplied"}</dd>
              <dt>Data source</dt>
              <dd>Example snapshot</dd>
            </dl>
          </div>
        ))}
      </div>
      <section className="integration-status">
        <PlugZap />
        <div>
          <h2>Backend connection</h2>
          <p>
            No backend endpoints are configured. The typed commerce adapter is the integration
            boundary for your existing system.
          </p>
          <span className="subtle-note">
            Health checks, workflow updates and human overrides will use the source you connect in
            Cursor.
          </span>
        </div>
        <StatusBadge value="NOT CONNECTED" />
      </section>
      <section>
        <SectionHeading title="Recent service & workflow events" />
        <EventTimeline events={snapshot.events} />
      </section>
    </>
  );
}
