"""One observation call: live Claude OR fixture mock. Never chooses disposition."""
from __future__ import annotations

import base64
import json
import os
import time
from typing import Any

from .schema import OBSERVATION_SCHEMA, validate_observation

SYSTEM = """You are the observation stage of a Receiving Manager for supplier inbound dock photos.
You do NOT choose accept, reject, or pending_review.
Report only what the photographs show against the purchase-order context.

Rules:
- identity_match:
  - yes: the focus carton / unit matches the PO product_name or brand family (e.g. Nutrabay carton for a Nutrabay PO; Innovist carton for Innovist; ONYC tape for Onyc; AJIO for AJIO; headphones photo for headphones PO). Background piles of other brands do NOT flip this to no.
  - no: the focus carton clearly shows a different brand OR product class than the PO (examples: PlatinumRx / medicines vs whey protein; PlatinumRx vs insulated bottle). When that wrong brand is readable on the focus carton, answer no — do NOT answer uncertain.
  - uncertain: only when the focus brand/product cannot be read (blur, dark, occlusion).
- carton_count:
  - Count cardboard shipping cartons that belong to this PO brand/SKU family when branding is readable.
  - Ignore courier polybags and unrelated brands in a mixed dock pile.
  - If the wide shot is mixed and you cannot isolate how many PO-brand cartons are present, carton_count_visible=uncertain and cartons_observed=null.
  - If only one PO-brand carton is clearly in frame and the PO ordered more, set cartons_observed to the number clearly visible (e.g. 1) with carton_count_visible=yes.
- quantity: yes only if units can be counted from open contents or a readable packing list. Sealed with no packing-list count → quantity_visible=uncertain, units_observed=null.
- carton_damage / unit_damage: none | crushing | water | tears | uncertain. Crushed corners, caved tops, torn edges, FRAGILE wear → crushing or tears, not none.
- quality_flags: empty if none. Use wrong_variant / wrong_colour when PO colour/variant disagrees with visible goods. Use missing_components when a required PO part is visibly absent.
- Never invent counts, brands, or damage. NOT in frame is uncertain, not no/none — except wrong brand when the other brand is clearly readable (then identity_match=no).
- evidence: two short sentences citing brands, counts, and damage you actually saw.
"""


def observe_receiving(*, po: dict, photos: list[dict]) -> tuple[dict, dict]:
    mode = _mode()
    if mode == "mock":
        from .mock_observer import observe_mock

        return observe_mock(po=po, photos=photos)
    return _observe_live(po=po, photos=photos)


def _mode() -> str:
    forced = (os.environ.get("RECEIVING_MODE") or "").strip().lower()
    if forced in {"mock", "live"}:
        return forced
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return "mock"
    return "live"


def _observe_live(*, po: dict, photos: list[dict]) -> tuple[dict, dict]:
    from anthropic import Anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set for live mode")

    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
    client = Anthropic(api_key=api_key)
    started = time.time()

    content: list[dict[str, Any]] = []
    for photo in photos[:8]:
        media = photo.get("media_type") or "image/jpeg"
        if media not in {"image/jpeg", "image/png", "image/gif", "image/webp"}:
            media = "image/jpeg"
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media,
                    "data": base64.b64encode(photo["bytes"]).decode("ascii"),
                },
            }
        )
    content.append(
        {
            "type": "text",
            "text": json.dumps(
                {
                    "po_number": po.get("po_number"),
                    "po_line": po.get("po_line"),
                    "sku": po.get("sku"),
                    "asin": po.get("asin"),
                    "product_name": po.get("product_name"),
                    "spec_colour": po.get("spec_colour"),
                    "spec_variant": po.get("spec_variant"),
                    "spec_components": po.get("spec_components"),
                    "qty_ordered": po.get("qty_ordered"),
                    "cartons_ordered": po.get("cartons_ordered"),
                    "units_per_carton_ordered": po.get("units_per_carton_ordered"),
                    "note": "Inbound receiving inspection. Prefer uncertain over guessing.",
                },
                ensure_ascii=True,
            ),
        }
    )

    response = client.messages.create(
        model=model,
        max_tokens=1200,
        system=SYSTEM,
        tools=[
            {
                "name": "submit_receiving_observation",
                "description": "Submit visual receiving observations only. No disposition.",
                "input_schema": OBSERVATION_SCHEMA,
            }
        ],
        tool_choice={"type": "tool", "name": "submit_receiving_observation"},
        messages=[{"role": "user", "content": content}],
    )

    block = next((b for b in response.content if getattr(b, "type", None) == "tool_use"), None)
    if block is None:
        raise RuntimeError("Claude returned no tool_use observation")
    observation = validate_observation(dict(block.input))
    latency_ms = int((time.time() - started) * 1000)
    meta = {
        "name": "claude",
        "version": model,
        "latency_ms": latency_ms,
        "prompt_version": "receiving-observe-v4",
        "calls": 1,
    }
    return observation, meta
