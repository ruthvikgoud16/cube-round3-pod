#!/usr/bin/env bash
# Publish the live-run site against the current tunnel.
#   scripts/publish_live_site.sh https://xxxx.trycloudflare.com [netlify-site-id]
# The tunnel URL changes every time cloudflared restarts, so it is substituted at deploy time
# and never committed.
set -euo pipefail
TUNNEL="${1:?tunnel url required}"
SITE="${2:-${LIVE_SITE_ID:-}}"
TUNNEL="${TUNNEL%/}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="$(mktemp -d)"
cp "$ROOT/web-live/index.html" "$STAGE/"
sed "s#TUNNEL_URL#$TUNNEL#g" "$ROOT/web-live/netlify.toml" > "$STAGE/netlify.toml"
NETLIFY="$(command -v netlify)"
if [ -z "$NETLIFY" ]; then
  echo "netlify CLI is not on PATH" >&2
  exit 1
fi
if [ -n "$SITE" ]; then
  "$NETLIFY" deploy --prod --dir "$STAGE" --site "$SITE" --no-build
else
  "$NETLIFY" deploy --prod --dir "$STAGE" --no-build
fi
rm -rf "$STAGE"
