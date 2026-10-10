import { createFileRoute } from "@tanstack/react-router";
import { WorkflowsPage } from "@/components/cube/pages";
export const Route = createFileRoute("/workflows/")({
  head: () => ({
    meta: [
      { title: "Workflows — CUBE Control Tower" },
      {
        name: "description",
        content: "Browse commerce workflows with distinct execution states and final outcomes.",
      },
      { property: "og:title", content: "Workflows — CUBE Control Tower" },
      {
        property: "og:description",
        content: "Browse commerce workflows with distinct execution states and final outcomes.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: WorkflowsPage,
});
