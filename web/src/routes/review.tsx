import { createFileRoute } from "@tanstack/react-router";
import { ReviewQueue } from "@/components/cube/pages";
export const Route = createFileRoute("/review")({
  head: () => ({
    meta: [
      { title: "Human Review — CUBE Control Tower" },
      {
        name: "description",
        content: "Review agent uncertainty, exceptions and human decision records.",
      },
      { property: "og:title", content: "Human Review — CUBE Control Tower" },
      {
        property: "og:description",
        content: "Review agent uncertainty, exceptions and human decision records.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: ReviewQueue,
});
