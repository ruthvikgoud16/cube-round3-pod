import {
  Check,
  Circle,
  CircleAlert,
  CircleDashed,
  Ban,
  LoaderCircle,
  SkipForward,
  WifiOff,
  X,
  Box,
  PackageCheck,
  ScanLine,
  RotateCcw,
  ReceiptText,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { AgentHealth } from "@/lib/commerce/types";
export function StatusBadge({
  value,
  small = false,
}: {
  value?: string | undefined;
  small?: boolean;
}) {
  const text = value || "NOT DECIDED";
  const tone =
    /^PASS$|^CLEAN$|^AVAILABLE$|^COMPLETED$/.test(text) && !/UNAVAILABLE/.test(text)
      ? "success"
      : /FAIL|EXCEPTION|UNAVAILABLE/.test(text)
        ? "danger"
        : /BLOCKED|REVIEW|UNCERTAIN|RECOVERY|CLAIM|DEGRADED/.test(text)
          ? "warning"
          : /RUNNING|IN_PROGRESS/.test(text)
            ? "info"
            : "neutral";
  const Icon = /SKIPPED/.test(text)
    ? SkipForward
    : /UNAVAILABLE/.test(text)
      ? WifiOff
      : /BLOCKED/.test(text)
        ? Ban
        : /PASS|CLEAN|COMPLETED/.test(text)
          ? Check
          : tone === "danger"
            ? X
            : tone === "warning"
              ? CircleAlert
              : /RUNNING|IN_PROGRESS/.test(text)
                ? LoaderCircle
                : CircleDashed;
  return (
    <span className={cn("status-badge", `tone-${tone}`, small && "badge-small")}>
      <Icon size={12} />
      <span>{text.replaceAll("_", " ")}</span>
    </span>
  );
}
export function HealthIndicator({ agent }: { agent: AgentHealth }) {
  return (
    <div className="health-indicator">
      <span
        className={cn(
          "health-dot",
          agent.state === "AVAILABLE"
            ? "tone-success"
            : agent.state === "DEGRADED"
              ? "tone-warning"
              : "tone-danger",
        )}
      />
      <span>{agent.name}</span>
      <span className="health-latency">
        {agent.latency !== undefined ? `${agent.latency} ms` : "—"}
      </span>
    </div>
  );
}
export const stageIcons = {
  Receiving: ScanLine,
  Prep: PackageCheck,
  Pack: Box,
  Returns: RotateCcw,
  Recovery: ReceiptText,
};
export function StageIcon({ name, size = 20 }: { name: string; size?: number }) {
  const Icon = stageIcons[name as keyof typeof stageIcons] || Circle;
  return <Icon size={size} />;
}
export function SectionHeading({
  title,
  eyebrow,
  children,
}: {
  title: string;
  eyebrow?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="section-heading">
      <div>
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <h2>{title}</h2>
      </div>
      {children}
    </div>
  );
}
