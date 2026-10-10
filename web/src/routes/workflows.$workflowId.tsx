import { createFileRoute } from "@tanstack/react-router";
import { WorkflowDetail } from "@/components/cube/pages";
export const Route = createFileRoute("/workflows/$workflowId")({
  head: ({ params }) => ({
    meta: [
      { title: `${params.workflowId} — CUBE Workflow Trace` },
      {
        name: "description",
        content:
          "Inspect ordered commerce stages, evidence and orchestrator decisions for this workflow.",
      },
      { property: "og:title", content: `${params.workflowId} — CUBE Workflow Trace` },
      {
        property: "og:description",
        content: "Trace specialist inspections and their final commerce outcome.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: WorkflowDetailPage,
});
function WorkflowDetailPage() {
  const { workflowId } = Route.useParams();
  return <WorkflowDetail id={workflowId} />;
}
