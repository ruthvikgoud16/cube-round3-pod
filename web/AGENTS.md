<!-- LOVABLE:BEGIN -->

> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.

<!-- LOVABLE:END -->

## CUBE frontend architecture

- Keep commerce fixtures isolated in `src/lib/commerce/fixtures.ts` and access data through the typed `CommerceAdapter` provider; this preserves the separately owned backend and avoids assuming its transport or schema.
- Use a spatial specialist-station hero with the backend-supplied stage array preserved in an ordered route strip and core inspector; absent specialists remain explicitly off-route so spatial placement never implies an invented execution sequence.
- Keep shareable workspace views in TanStack leaf routes, with shared chrome in the root and an Outlet-only workflows parent; this supports direct links and nested workflow detail navigation.
- Animate only stage differences received through a backend adapter subscription, never initial snapshots or fixture timers; this prevents fabricated execution.
- Keep graph presentation and signal direction in a browser-safe orchestration view model separate from the commerce adapter; the visualization never writes workflow decisions.
