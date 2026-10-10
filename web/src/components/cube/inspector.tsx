import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { Copy, Check, Fingerprint, FileText, ExternalLink } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { StatusBadge, StageIcon } from "./primitives";
import { useCommerce } from "@/lib/commerce/service";
import type { Stage, Workflow } from "@/lib/commerce/types";
export function EvidenceInspector({
  stage,
  workflow,
  onClose,
}: {
  stage?: Stage | undefined;
  workflow: Workflow;
  onClose: () => void;
}) {
  const { snapshot } = useCommerce();
  const [copied, setCopied] = useState(false);
  return (
    <Sheet
      open={!!stage}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <SheetContent className="inspector-sheet overflow-y-auto w-full sm:max-w-[540px]">
        {stage && (
          <>
            <SheetHeader>
              <span className="eyebrow">
                STAGE INSPECTOR ·{" "}
                {snapshot.source === "example" ? "EXAMPLE DETAILS" : "CONNECTED DATA"}
              </span>
              <SheetTitle className="inspector-title">
                <StageIcon name={stage.name} size={26} />
                {stage.name} inspection
              </SheetTitle>
              <SheetDescription>
                {workflow.id} <span> / </span> {workflow.unit}
              </SheetDescription>
            </SheetHeader>
            <div className="inspector-identity">
              <code>{stage.agent}</code>
              <StatusBadge value={stage.verdict || stage.status} />
            </div>
            <p className="inspector-explanation">{stage.explanation}</p>
            <div className="detail-section">
              <h3>Agent recommendation</h3>
              <strong>{stage.recommendation || "No separate recommendation provided"}</strong>
              {stage.name === "Returns" && (
                <p className="subtle-note">
                  A disposition recommendation is not a refund approval.
                </p>
              )}
            </div>
            <div className="detail-section">
              <h3>
                Checks & verdicts <span>{stage.checks.length}</span>
              </h3>
              {stage.checks.length ? (
                stage.checks.map((check) => (
                  <div className="check-item" key={check.name}>
                    <div>
                      <strong>{check.name}</strong>
                      <StatusBadge value={check.verdict} small />
                    </div>
                    <dl>
                      <dt>Expected</dt>
                      <dd>{check.expected}</dd>
                      <dt>Observed</dt>
                      <dd>{check.observed}</dd>
                      {check.confidence !== undefined && (
                        <>
                          <dt>Confidence</dt>
                          <dd>{Math.round(check.confidence * 100)}%</dd>
                        </>
                      )}
                    </dl>
                  </div>
                ))
              ) : (
                <p className="subtle-note">No checks recorded for this stage.</p>
              )}
            </div>
            <div className="detail-section">
              <h3>
                Persisted evidence <span>{stage.evidence.length}</span>
              </h3>
              {stage.evidence.length ? (
                stage.evidence.map((e) => (
                  <div className="evidence-record" key={e.id}>
                    <FileText size={18} />
                    <div>
                      <strong>{e.label}</strong>
                      <code>{e.id}</code>
                      <small>
                        {e.kind} ·{" "}
                        {e.timestamp
                          ? new Date(e.timestamp).toISOString().replace("T", " ").slice(0, 19) +
                            " UTC"
                          : "No timestamp"}
                      </small>
                      {e.upstream.length > 0 && <small>Upstream: {e.upstream.join(", ")}</small>}
                      {e.hash && (
                        <div className="hash-row">
                          <Fingerprint size={13} />
                          <code>{e.hash}</code>
                          <Button
                            variant="ghost"
                            size="icon"
                            title="Copy content hash"
                            aria-label="Copy content hash"
                            onClick={async () => {
                              await navigator.clipboard.writeText(e.hash || "");
                              setCopied(true);
                            }}
                          >
                            {copied ? <Check /> : <Copy />}
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <p className="subtle-note">No evidence references supplied.</p>
              )}
              <p className="subtle-note">
                Content hashes identify records for traceability; they do not establish tamper-proof
                storage.
              </p>
            </div>
            <div className="detail-section">
              <h3>Model calls & timing</h3>
              {stage.modelCalls.length ? (
                stage.modelCalls.map((call, i) => (
                  <div className="model-call" key={i}>
                    <span>{call.model}</span>
                    <code>
                      {call.cost !== undefined ? `$${call.cost.toFixed(3)}` : "Cost unavailable"}
                    </code>
                    <small>{call.timestamp || "Timestamp unavailable"}</small>
                  </div>
                ))
              ) : (
                <p className="subtle-note">No model call recorded.</p>
              )}
              <dl className="detail-dl">
                <dt>Stage timestamp</dt>
                <dd>{stage.timestamp || "Not provided"}</dd>
              </dl>
            </div>
            {stage.error && (
              <div className="error-box">
                <h3>Error details</h3>
                <code>{stage.error}</code>
              </div>
            )}
            {stage.review && (
              <div className="review-notice">
                <strong>Human review required</strong>
                <p>{workflow.reviewReason || stage.explanation}</p>
                <Button asChild variant="outline" size="sm">
                  <Link to="/review">
                    Open review queue <ExternalLink />
                  </Link>
                </Button>
              </div>
            )}
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
