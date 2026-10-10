import { createFileRoute, Outlet } from "@tanstack/react-router";
export const Route = createFileRoute("/workflows")({ component: WorkflowsLayout });
function WorkflowsLayout() {
  return <Outlet />;
}
