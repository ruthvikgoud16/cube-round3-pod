import { useState } from "react";
import { Link, useRouterState } from "@tanstack/react-router";
import {
  Box,
  LayoutDashboard,
  GitBranch,
  ScanSearch,
  UsersRound,
  Activity,
  PanelLeftClose,
  PanelLeftOpen,
  ChevronDown,
  ArrowUpRight,
  Bell,
  Search,
  CircleHelp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCommerce } from "@/lib/commerce/service";
const nav = [
  { to: "/", label: "Operations Overview", icon: LayoutDashboard },
  { to: "/workflows", label: "Workflows", icon: GitBranch },
  { to: "/evidence", label: "Evidence Explorer", icon: ScanSearch },
  { to: "/review", label: "Human Review", icon: UsersRound },
  { to: "/health", label: "System Health", icon: Activity },
] as const;
export function AppShell({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [notice, setNotice] = useState(false);
  const path = useRouterState({ select: (s) => s.location.pathname });
  const { snapshot, error } = useCommerce();
  const reviews = snapshot.workflows.filter((w) => w.reviewReason).length;
  return (
    <div className={collapsed ? "app-shell sidebar-collapsed" : "app-shell"}>
      <aside className="app-sidebar">
        <Link to="/" className="brand">
          <div className="brand-mark">
            <Box size={26} strokeWidth={1.6} />
          </div>
          <div className="brand-copy">
            <strong>
              CUBE<span>®</span>
            </strong>
            <small>CONTROL TOWER</small>
          </div>
        </Link>
        <div className="workspace-switch">
          <div className="workspace-avatar">C</div>
          <div className="sidebar-label">
            <strong>Commerce operations</strong>
            <small>
              {snapshot.source === "example" ? "Example workspace" : "Connected workspace"}
            </small>
          </div>
          <ChevronDown size={14} className="sidebar-label" />
        </div>
        <div className="nav-caption sidebar-label">WORKSPACE</div>
        <nav>
          {nav.map((n) => (
            <Button
              key={n.to}
              variant="ghost"
              asChild
              className={
                path === n.to || (n.to === "/workflows" && path.startsWith("/workflows/"))
                  ? "nav-item nav-active"
                  : "nav-item"
              }
              title={n.label}
            >
              <Link to={n.to}>
                <n.icon size={18} />
                <span className="sidebar-label">{n.label}</span>
                {n.to === "/review" && <span className="nav-count sidebar-label">{reviews}</span>}
              </Link>
            </Button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="environment sidebar-label">
            <span className="health-dot tone-info" />
            <div>
              <strong>
                {snapshot.source === "example" ? "Frontend preview" : "Connected source"}
              </strong>
              <small>
                {snapshot.source === "example" ? "Backend not connected" : "Backend data supplied"}
              </small>
            </div>
          </div>
          <Button
            variant="ghost"
            className="sidebar-help"
            onClick={() => setNotice(!notice)}
            title="Integration information"
          >
            <CircleHelp />
            <span className="sidebar-label">Help & integration</span>
            <ArrowUpRight size={14} className="sidebar-label" />
          </Button>
          <div className="profile">
            <div className="profile-avatar">BR</div>
            <div className="sidebar-label">
              <strong>Bathini Ruthvik</strong>
              <small>Workspace owner</small>
            </div>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="topbar-left">
            <Button
              variant="ghost"
              size="icon"
              title={collapsed ? "Expand navigation" : "Collapse navigation"}
              aria-label="Toggle navigation"
              onClick={() => setCollapsed(!collapsed)}
            >
              {collapsed ? <PanelLeftOpen /> : <PanelLeftClose />}
            </Button>
            <span className="breadcrumb">
              Workspace <span>/</span>{" "}
              <strong>{nav.find((n) => n.to === path)?.label || "Workflow details"}</strong>
            </span>
          </div>
          <div className="topbar-right">
            <span className="example-label">
              <span />
              {snapshot.source === "example" ? "Example data" : "Connected data"}
            </span>
            <Button asChild variant="ghost" size="icon" title="Search workflows">
              <Link to="/workflows" aria-label="Search workflows">
                <Search />
              </Link>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              title="Recent events"
              aria-label="Recent events"
              onClick={() => setNotice(!notice)}
            >
              <Bell />
            </Button>
            <div className="top-avatar">BR</div>
          </div>
        </header>
        {notice && (
          <div className="information-band">
            Frontend preview · all workflows, health values and events are examples. Backend actions
            are unavailable until your adapter is connected.
            <Button size="sm" variant="ghost" onClick={() => setNotice(false)}>
              Dismiss
            </Button>
          </div>
        )}
        {error && (
          <div role="alert" className="information-band">
            {error}
          </div>
        )}
        <main className="workspace-main">{children}</main>
        <footer className="app-footer">
          <span>
            <Box size={12} /> CUBE Control Tower
          </span>
          <span>
            {snapshot.source === "example"
              ? "Example snapshot · 10 Oct 2026, 04:24 UTC"
              : "Connected backend data"}{" "}
            <span className="footer-separator">/</span>{" "}
            {snapshot.source === "example"
              ? "Not connected to production"
              : "Backend is the source of truth"}
          </span>
        </footer>
      </div>
    </div>
  );
}
