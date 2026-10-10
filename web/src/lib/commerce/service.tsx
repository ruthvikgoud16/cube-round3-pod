import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { fixtureSnapshot } from "./fixtures";
import type { CommerceAdapter, CommerceSnapshot } from "./types";
export const exampleAdapter: CommerceAdapter = { loadSnapshot: async () => fixtureSnapshot };
const CommerceContext = createContext<{
  snapshot: CommerceSnapshot;
  adapter: CommerceAdapter;
  changedStages: Set<string>;
  error?: string | undefined;
}>({ snapshot: fixtureSnapshot, adapter: exampleAdapter, changedStages: new Set() });
export function CommerceProvider({
  children,
  adapter = exampleAdapter,
}: {
  children: ReactNode;
  adapter?: CommerceAdapter;
}) {
  const [snapshot, setSnapshot] = useState<CommerceSnapshot>(
    adapter === exampleAdapter
      ? fixtureSnapshot
      : { source: "backend", workflows: [], health: [], events: [] },
  );
  const [changedStages, setChangedStages] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string>();
  const previous = useRef<CommerceSnapshot | undefined>(undefined);
  useEffect(() => {
    let active = true;
    previous.current = undefined;
    adapter
      .loadSnapshot()
      .then((data) => {
        if (active) {
          previous.current = data;
          setSnapshot(data);
          setChangedStages(new Set());
        }
      })
      .catch(() => {
        if (active)
          setError(
            adapter === exampleAdapter
              ? "The connected source could not be loaded. Example data remains visible."
              : "The orchestrator could not be loaded. No example products were substituted.",
          );
      });
    const unsubscribe = adapter.subscribe?.((next) => {
      if (!active) return;
      const changes = new Set<string>();
      if (previous.current && next.source === "backend")
        for (const w of next.workflows)
          for (const stage of w.stages) {
            const old = previous.current.workflows
              .find((item) => item.id === w.id)
              ?.stages.find((item) => item.id === stage.id);
            if (old && (old.status !== stage.status || old.verdict !== stage.verdict))
              changes.add(`${w.id}:${stage.id}`);
          }
      previous.current = next;
      setSnapshot(next);
      setChangedStages(changes);
    });
    return () => {
      active = false;
      unsubscribe?.();
    };
  }, [adapter]);
  return (
    <CommerceContext.Provider value={{ snapshot, adapter, changedStages, error }}>
      {children}
    </CommerceContext.Provider>
  );
}
export const useCommerce = () => useContext(CommerceContext);
