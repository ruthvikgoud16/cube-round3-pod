import { useState } from "react";
import { Link } from "@tanstack/react-router";
import {
  Search,
  SlidersHorizontal,
  ArrowUpDown,
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
  GitBranch,
  Box,
  Keyboard,
  Cable,
  Watch,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Workflow } from "@/lib/commerce/types";
import { StatusBadge } from "./primitives";
const statuses = ["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED", "BLOCKED", "RECOVERY_REQUIRED"];
export function ProductSymbol({ name }: { name: string }) {
  const Icon = name.includes("Keyboard")
    ? Keyboard
    : name.includes("Hub")
      ? Cable
      : name.includes("Watch")
        ? Watch
        : Box;
  return (
    <span className="product-symbol">
      <Icon size={18} />
    </span>
  );
}
export function WorkflowTable({
  workflows,
  limit = 5,
  onSelect,
  selectedId,
}: {
  workflows: Workflow[];
  limit?: number;
  onSelect?: (workflow: Workflow) => void;
  selectedId?: string | undefined;
}) {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("ALL");
  const [outcome, setOutcome] = useState("ALL");
  const [filters, setFilters] = useState(false);
  const [page, setPage] = useState(0);
  const [ascending, setAscending] = useState(false);
  const filtered = workflows
    .filter(
      (w) =>
        `${w.id} ${w.product} ${w.sku} ${w.unit}`.toLowerCase().includes(search.toLowerCase()) &&
        (status === "ALL" || w.status === status) &&
        (outcome === "ALL" || w.outcome === outcome),
    )
    .sort((a, b) => (ascending ? a.id.localeCompare(b.id) : b.id.localeCompare(a.id)));
  const maxPage = Math.max(0, Math.ceil(filtered.length / limit) - 1);
  const safePage = Math.min(page, maxPage);
  const rows = filtered.slice(safePage * limit, (safePage + 1) * limit);
  return (
    <div className="workflow-table-section">
      <div className="table-controls">
        <div className="table-tabs">
          <Button
            variant="ghost"
            className={status === "ALL" ? "table-tab active" : "table-tab"}
            onClick={() => {
              setStatus("ALL");
              setPage(0);
            }}
          >
            All workflows <span>{workflows.length}</span>
          </Button>
          <Button
            variant="ghost"
            className={status === "IN_PROGRESS" ? "table-tab active" : "table-tab"}
            onClick={() => {
              setStatus("IN_PROGRESS");
              setPage(0);
            }}
          >
            In progress
          </Button>
          <Button
            variant="ghost"
            className={status === "BLOCKED" ? "table-tab active" : "table-tab"}
            onClick={() => {
              setStatus("BLOCKED");
              setPage(0);
            }}
          >
            Blocked
          </Button>
        </div>
        <div className="table-search-tools">
          <label className="search-field">
            <Search size={15} />
            <input
              aria-label="Search workflows"
              placeholder="Search workflows…"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(0);
              }}
            />
          </label>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setFilters(!filters)}
            aria-expanded={filters}
          >
            <SlidersHorizontal />
            Filters
          </Button>
        </div>
      </div>
      {filters && (
        <div className="filter-row">
          <label>
            Status
            <select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(0);
              }}
            >
              <option value="ALL">All statuses</option>
              {statuses.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
          <label>
            Final outcome
            <select
              value={outcome}
              onChange={(e) => {
                setOutcome(e.target.value);
                setPage(0);
              }}
            >
              <option value="ALL">All outcomes</option>
              {["CLEAN", "EXCEPTION", "INCOMPLETE", "NEEDS_REVIEW", "CLAIM_RECOMMENDED"].map(
                (s) => (
                  <option key={s}>{s}</option>
                ),
              )}
            </select>
          </label>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              setSearch("");
              setStatus("ALL");
              setOutcome("ALL");
            }}
          >
            Reset
          </Button>
        </div>
      )}
      <div className="table-scroll">
        <table className="workflow-table">
          <thead>
            <tr>
              <th>
                <Button variant="ghost" size="sm" onClick={() => setAscending(!ascending)}>
                  Workflow ID <ArrowUpDown size={12} />
                </Button>
              </th>
              <th>Product / Unit</th>
              <th>Route</th>
              <th>Workflow status</th>
              <th>Final outcome</th>
              <th>Updated (UTC)</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map((w) => (
              <tr key={w.id} className={selectedId === w.id ? "row-selected" : ""}>
                <td>
                  {onSelect ? (
                    <Button variant="link" className="workflow-id" onClick={() => onSelect(w)}>
                      {w.id}
                    </Button>
                  ) : (
                    <Link
                      className="workflow-id"
                      to="/workflows/$workflowId"
                      params={{ workflowId: w.id }}
                    >
                      {w.id}
                    </Link>
                  )}
                </td>
                <td>
                  <div className="table-product">
                    <ProductSymbol name={w.product} />
                    <div>
                      <strong>{w.product}</strong>
                      <code>
                        {w.sku} <span>·</span> {w.unit}
                      </code>
                    </div>
                  </div>
                </td>
                <td>
                  <span className="route-cell">
                    <GitBranch size={12} />
                    {w.route}
                  </span>
                </td>
                <td>
                  <StatusBadge value={w.status} small />
                </td>
                <td>
                  <StatusBadge value={w.outcome} small />
                </td>
                <td className="time-cell">{w.updated.slice(11, 16)}</td>
                <td>
                  <Button asChild variant="ghost" size="icon" title={`Open ${w.id}`}>
                    <Link
                      to="/workflows/$workflowId"
                      params={{ workflowId: w.id }}
                      aria-label={`Open ${w.id}`}
                    >
                      <ArrowUpRight />
                    </Link>
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!rows.length && (
          <div className="empty-state">
            <Search size={24} />
            <strong>No workflows match these filters</strong>
            <Button
              variant="link"
              onClick={() => {
                setSearch("");
                setStatus("ALL");
                setOutcome("ALL");
              }}
            >
              Clear filters
            </Button>
          </div>
        )}
      </div>
      <div className="table-footer">
        <span>
          {filtered.length ? safePage * limit + 1 : 0}–
          {Math.min((safePage + 1) * limit, filtered.length)} of {filtered.length} workflows
          <span className="subtle-note"> · Example records</span>
        </span>
        <div>
          <Button
            variant="outline"
            size="icon"
            aria-label="Previous page"
            disabled={safePage === 0}
            onClick={() => setPage(safePage - 1)}
          >
            <ChevronLeft />
          </Button>
          <span>{safePage + 1}</span>
          <Button
            variant="outline"
            size="icon"
            aria-label="Next page"
            disabled={safePage === maxPage}
            onClick={() => setPage(safePage + 1)}
          >
            <ChevronRight />
          </Button>
        </div>
      </div>
    </div>
  );
}
