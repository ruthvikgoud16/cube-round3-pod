import { createFileRoute } from "@tanstack/react-router";
import { EvidencePage } from "@/components/cube/pages";
export const Route = createFileRoute("/evidence")({
  head: () => ({
    meta: [
      { title: "Evidence Explorer — CUBE Control Tower" },
      {
        name: "description",
        content: "Explore inspection evidence, upstream references and traceability values.",
      },
      { property: "og:title", content: "Evidence Explorer — CUBE Control Tower" },
      {
        property: "og:description",
        content: "Explore inspection evidence, upstream references and traceability values.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: EvidencePage,
});
