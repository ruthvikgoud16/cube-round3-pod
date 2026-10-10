import { createFileRoute } from "@tanstack/react-router";
import { SystemHealthPage } from "@/components/cube/pages";
export const Route = createFileRoute("/health")({
  head: () => ({
    meta: [
      { title: "System Health — CUBE Control Tower" },
      {
        name: "description",
        content: "Inspect orchestration and specialist agent service health.",
      },
      { property: "og:title", content: "System Health — CUBE Control Tower" },
      {
        property: "og:description",
        content: "Inspect orchestration and specialist agent service health.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: SystemHealthPage,
});
