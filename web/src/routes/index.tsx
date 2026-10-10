import { createFileRoute } from "@tanstack/react-router";
import { Overview } from "@/components/cube/overview";
export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Operations Overview — CUBE Control Tower" },
      {
        name: "description",
        content:
          "Commerce operations, agent health and traceable workflow decisions in CUBE Control Tower.",
      },
      { property: "og:title", content: "Operations Overview — CUBE Control Tower" },
      {
        property: "og:description",
        content: "A unified view of commerce workflows, evidence and human review.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Overview,
});
