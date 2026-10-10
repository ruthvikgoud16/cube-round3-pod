# CUBE Control Tower

Frontend-only commerce operations console. No database, authentication, LLM, or orchestration backend is added. All initial data is explicitly labeled example data.

## Build with Lovable

Open your project in the [Lovable editor](https://lovable.dev) and keep building.

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: connect the project to GitHub and every change made in Lovable is committed straight to your repository.
- **Full ownership**: this code is yours. Push to your repository and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```

## Built with

- TanStack Start
- TypeScript
- React
- Tailwind CSS

## Start locally

```sh
bun install
bun run dev
```

Use the local URL printed by Vite. `bun run test` runs the tests. Node.js 22+ and Bun are recommended.

## Connect your existing backend in Cursor

`src/lib/commerce/types.ts` defines a **UI-facing domain model**, not your backend response schema. Implement `CommerceAdapter` and map your existing responses into that model. No endpoint paths are assumed.

Pass your adapter to `CommerceProvider` in `src/routes/__root.tsx`. The default `exampleAdapter` loads the isolated `src/lib/commerce/fixtures.ts` snapshot. Your mapped snapshots must set `source: 'backend'`; remove or replace the example-only product illustration when adding real product media. The illustration is not inspection evidence.

- `loadSnapshot()` returns workflows, health and events.
- Optional `subscribe(receive)` receives real backend updates and returns an unsubscribe function. Initial loading does not animate; changed stage status/verdict values animate once when a subscribed backend snapshot arrives.
- Optional `submitOverride({ workflowId, reason })` delegates to your existing authenticated action. The adapter supplies the actual session actor through your backend; the backend must return the persisted actor, reason and timestamp. The preview disables submission rather than fabricating decisions.
- Supply stages in the actual executed order. FBA Prep and direct Pack are alternatives; conditional Returns is omitted when absent or represented with a supplied skipped state. Five-stage integration traces are also supported.
- Model call counts, costs, verdicts, timestamps, evidence and upstream references are displayed only when supplied. No fee/claim amounts are inferred.

The UI does not enforce backend agent contracts or call models. Your existing backend remains authoritative for Prep's exactly-three-photo gate, route validation, return disposition and named-fee-line recovery rules.

## Views

`/` operations overview, `/workflows` workflow list, `/workflows/:workflowId` trace and details, `/evidence` evidence explorer, `/review` review queue, `/health` system health.
