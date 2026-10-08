/* global fetch, document */
const CHECK_LABELS = {
  identity_match: "Identity",
  carton_count: "Carton count",
  quantity: "Quantity",
  carton_damage: "Carton damage",
  unit_damage: "Unit damage",
  quality_flags: "Quality flags",
};

function fmtVal(v) {
  if (v == null) return "—";
  if (Array.isArray(v)) return v.length ? v.join(", ") : "none";
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}

function outcomeClass(o) {
  return (o || "empty").replace(/[^a-z_]/gi, "");
}

const ReceivingDesk = {
  cases: [],
  lastOut: null,
  batchState: {},

  async init() {
    const meta = await (await fetch("/api/project")).json();
    this.cases = meta.cases || [];
    const modeEl = document.getElementById("mode");
    const dot = document.getElementById("modeDot");
    modeEl.textContent = meta.mode;
    dot.className = "dot " + (meta.mode === "live" ? "live" : "mock");

    const sel = document.getElementById("unit");
    sel.innerHTML = this.cases
      .map(
        (c) =>
          `<option value="${c.id}">${c.id.replace("UNIT-RCV-", "")} · ${c.label} · ${c.product_name}</option>`
      )
      .join("");

    const rail = document.getElementById("caseRail");
    rail.innerHTML = this.cases
      .map(
        (c) =>
          `<button type="button" class="case-chip" data-id="${c.id}" title="${c.product_name}">${c.id.slice(-2)}</button>`
      )
      .join("");
    rail.querySelectorAll(".case-chip").forEach((btn) => {
      btn.onclick = () => {
        sel.value = btn.dataset.id;
        this.syncRail();
        this.loadShots();
      };
    });
    sel.onchange = () => {
      this.syncRail();
      this.loadShots();
    };
    this.syncRail();
    await this.loadShots();
    this.renderBatchIdle();

    document.getElementById("toggleJson").onclick = () => {
      const el = document.getElementById("json");
      el.hidden = !el.hidden;
      if (!el.hidden && this.lastOut) el.textContent = JSON.stringify(this.lastOut, null, 2);
    };
    document.getElementById("run").onclick = () =>
      this.runOne(sel.value, document.getElementById("org").value);
    document.getElementById("runAll").onclick = () =>
      this.runAll(document.getElementById("org").value, this.cases.map((c) => c.id));

    const lb = document.getElementById("lightbox");
    document.getElementById("lbClose").onclick = () => {
      lb.classList.remove("open");
      lb.hidden = true;
    };
    lb.onclick = (e) => {
      if (e.target === lb) {
        lb.classList.remove("open");
        lb.hidden = true;
      }
    };
  },

  syncRail() {
    const id = document.getElementById("unit").value;
    document.querySelectorAll(".case-chip").forEach((b) => {
      b.classList.toggle("active", b.dataset.id === id);
      const done = this.batchState[b.dataset.id];
      b.className = "case-chip" + (b.dataset.id === id ? " active" : "") + (done ? " done-" + done : "");
    });
  },

  async loadShots() {
    const id = document.getElementById("unit").value;
    const shots = document.getElementById("shots");
    const roles = [
      ["01_pallet", "Pallet"],
      ["02_carton", "Carton"],
      ["03_unit", "Unit"],
    ];
    shots.innerHTML = roles
      .map(
        ([n, label]) =>
          `<figure class="shot" data-src="/photos/${id}/${n}.jpg"><img src="/photos/${id}/${n}.jpg?t=${Date.now()}" alt="${label}" loading="lazy"><figcaption>${label}</figcaption></figure>`
      )
      .join("");
    shots.querySelectorAll(".shot").forEach((fig) => {
      fig.onclick = () => {
        const lb = document.getElementById("lightbox");
        document.getElementById("lbImg").src = fig.dataset.src + "?t=" + Date.now();
        lb.hidden = false;
        requestAnimationFrame(() => lb.classList.add("open"));
      };
    });
    const c = this.cases.find((x) => x.id === id);
    document.getElementById("photoHint").textContent = c
      ? `${c.label} · expect ${c.expected_outcome}`
      : "pallet · carton · unit";
  },

  renderResult(out, resOk) {
    this.lastOut = out;
    const json = document.getElementById("json");
    if (!json.hidden) json.textContent = JSON.stringify(out, null, 2);

    const slot = document.getElementById("verdictSlot");
    const poStrip = document.getElementById("poStrip");
    const checksPanel = document.getElementById("checksPanel");
    const checks = document.getElementById("checks");

    if (!resOk || !out.evidence) {
      slot.innerHTML = `<div class="verdict-hero reject">
        <p class="verdict-kicker">Request failed</p>
        <p class="verdict-title">Error</p>
        <p class="verdict-reason">${out.detail || out.error || "request failed"}</p>
      </div>`;
      poStrip.hidden = true;
      checksPanel.hidden = true;
      return;
    }

    const ev = out.evidence;
    const d = ev.decision || {};
    const payload = ev.payload || {};
    const sub = ev.subject || {};
    const refs = sub.refs || {};
    const oc = outcomeClass(d.outcome);

    slot.innerHTML = `<div class="verdict-hero ${oc}">
      <p class="verdict-kicker">${sub.subject_id || "—"} · ${out.agent_id || "receiving"}</p>
      <p class="verdict-title">${(d.outcome || "?").replace(/_/g, " ")}</p>
      <p class="verdict-reason">${d.reason || ""}</p>
      <div class="verdict-meta">
        <span class="pill ${out.verdict || ""}">${out.verdict || "—"}</span>
        <span class="pill ${d.needs_human ? "hold" : "ok"}">${d.needs_human ? "needs human" : "auto"}</span>
        <span class="pill">${ev.record_id || ""}</span>
        <span class="pill">${payload.receiving_mode || "—"} mode</span>
        <span class="pill">${(out.model && out.model.name) || "model"}</span>
      </div>
    </div>`;

    poStrip.hidden = false;
    poStrip.innerHTML = [
      ["PO", refs.po_number || "—"],
      ["SKU", refs.sku || "—"],
      ["Units", `${payload.qty_received ?? "?"} / ${payload.qty_ordered ?? "?"}`],
      ["Cartons", `${payload.cartons_received ?? "?"} / ${payload.cartons_ordered ?? "?"}`],
    ]
      .map(([k, v]) => `<div class="po-cell"><span>${k}</span><strong>${fmtVal(v)}</strong></div>`)
      .join("");

    const list = ev.checks || [];
    const pass = list.filter((c) => c.verdict === "PASS").length;
    const fail = list.filter((c) => c.verdict === "FAIL").length;
    const unc = list.filter((c) => c.verdict === "UNCERTAIN").length;
    document.getElementById("checkSummary").textContent =
      `${pass} pass · ${fail} fail · ${unc} uncertain`;

    checksPanel.hidden = false;
    checks.innerHTML = list
      .map((c) => {
        const label = CHECK_LABELS[c.check_key] || c.check_key;
        return `<article class="check-card ${c.verdict}">
          <div class="check-top">
            <b>${label}</b>
            <span class="pill ${c.verdict}">${c.verdict}</span>
          </div>
          <div class="check-body">
            <div><span>Expected</span><strong>${fmtVal(c.expected)}</strong></div>
            <div><span>Observed</span><strong>${fmtVal(c.observed)}</strong></div>
          </div>
          <p class="check-detail">${c.detail || ""}</p>
        </article>`;
      })
      .join("");
  },

  renderBatchIdle() {
    const board = document.getElementById("batch");
    board.innerHTML = this.cases
      .map(
        (c) =>
          `<button type="button" class="batch-tile wait" data-id="${c.id}">
            <div class="id">${c.id}</div>
            <div class="out">ready</div>
          </button>`
      )
      .join("");
    board.querySelectorAll(".batch-tile").forEach((t) => {
      t.onclick = () => {
        document.getElementById("unit").value = t.dataset.id;
        this.syncRail();
        this.loadShots();
      };
    });
  },

  paintBatchTile(id, outcome, verdict) {
    this.batchState[id] = outcome;
    const board = document.getElementById("batch");
    let tile = board.querySelector(`[data-id="${id}"]`);
    if (!tile) return;
    tile.className = "batch-tile " + outcomeClass(outcome);
    tile.innerHTML = `<div class="id">${id}</div><div class="out">${(outcome || "?").replace(/_/g, " ")}</div><div class="meta">${verdict || ""}</div>`;
    tile.onclick = () => {
      document.getElementById("unit").value = id;
      this.syncRail();
      this.loadShots();
      if (this.lastOut?.evidence?.subject?.subject_id === id) this.renderResult(this.lastOut, true);
    };
    this.syncRail();
  },

  async runOne(unit, org) {
    const status = document.getElementById("status");
    const btn = document.getElementById("run");
    btn.disabled = true;
    status.className = "status-line busy busy-pulse";
    status.textContent = `Running ${unit}…`;
    try {
      const res = await fetch("/run", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          schema_version: "1.0",
          request_id: "desk-" + Date.now(),
          workflow_id: `WF-${org}-${unit}`,
          stage: "receiving",
          subject: { org_id: org, subject_id: unit, route: "fba" },
          previous_evidence: [],
          context: {},
          inputs: [],
        }),
      });
      const out = await res.json();
      this.renderResult(out, res.ok);
      const outcome = out.evidence?.decision?.outcome || "error";
      this.paintBatchTile(unit, outcome, out.verdict);
      status.className = "status-line";
      status.textContent = res.ok
        ? `${outcome.replace(/_/g, " ")} · ${out.evidence?.record_id || ""}`
        : `Error ${res.status}`;
    } finally {
      btn.disabled = false;
    }
  },

  async runAll(org, ids) {
    const btn = document.getElementById("runAll");
    const status = document.getElementById("status");
    btn.disabled = true;
    status.className = "status-line busy busy-pulse";
    for (const id of ids) {
      status.textContent = `Batch ${id}…`;
      document.getElementById("unit").value = id;
      this.syncRail();
      await this.loadShots();
      const res = await fetch("/run", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          schema_version: "1.0",
          request_id: "batch-" + id + "-" + Date.now(),
          workflow_id: `WF-${org}-${id}`,
          stage: "receiving",
          subject: { org_id: org, subject_id: id, route: "fba" },
          previous_evidence: [],
          context: {},
          inputs: [],
        }),
      });
      const out = await res.json();
      const outcome = out.evidence?.decision?.outcome || out.status || "error";
      this.paintBatchTile(id, outcome, out.verdict);
      this.renderResult(out, res.ok);
    }
    status.className = "status-line";
    status.textContent = "Batch complete · 12 deliveries";
    btn.disabled = false;
  },
};

const ReceivingEval = {
  async init() {
    const score = await (await fetch("/api/eval/score")).json();
    const soft = score.per_check_soft_agreement || {};
    const full = score.per_check_full_agreement || {};
    const preds = (await (await fetch("/api/eval/predictions")).json()).cases || [];

    const softMatch = soft.quantity?.match ?? 0;
    const softN = soft.quantity?.n ?? 0;
    document.getElementById("stats").innerHTML = [
      ["Labeled", score.n_labeled ?? 12],
      ["Full agree", score.n_agreed_all_checks ?? 0],
      ["Model runs", score.model_calls ?? preds.length],
      ["Qty soft", softN ? `${softMatch}/${softN}` : "—"],
    ]
      .map(([k, v]) => `<div class="stat"><span>${k}</span><strong>${v}</strong></div>`)
      .join("");

    const fill = (tbody, obj) => {
      document.getElementById(tbody).innerHTML = Object.entries(obj)
        .map(([check, s]) => {
          const n = s.n || 0;
          const pct = n ? ((100 * (s.match || 0)) / n).toFixed(0) + "%" : "—";
          return `<tr><td class="mono">${CHECK_LABELS[check] || check}</td><td>${n}</td><td>${s.match || 0} (${pct})</td><td>${s.fp || 0}</td><td>${s.fn || 0}</td><td>${s.uncertain_mismatch || 0}</td></tr>`;
        })
        .join("");
    };
    fill("softBody", soft);
    fill("fullBody", full);
    document.getElementById("agreedNote").textContent =
      "Agreed cases: " + ((score.agreed_case_ids || []).join(", ") || "none");

    document.getElementById("casesBody").innerHTML = preds
      .map((p) => {
        const c = p.checks || {};
        const cell = (k) => `<td class="mono ${c[k] || ""}">${c[k] || "—"}</td>`;
        return `<tr><td class="mono"><a href="/?unit=${p.case_id}">${p.case_id}</a></td><td><span class="pill ${p.outcome || ""}">${(p.outcome || p.status || "").replace(/_/g, " ")}</span></td>${cell("identity_match")}${cell("carton_count")}${cell("quantity")}${cell("carton_damage")}${cell("unit_damage")}${cell("quality_flags")}</tr>`;
      })
      .join("");
  },
};

const ReceivingFailures = {
  async init() {
    const dig = await (await fetch("/api/eval/digest")).json();
    const failed = dig.failed || [];
    const el = document.getElementById("failList");
    if (!failed.length) {
      el.innerHTML = '<div class="empty-state"><strong>Clean freeze</strong>No agreed-check mismatches in the current freeze.</div>';
      return;
    }
    el.innerHTML = failed
      .map((f) => {
        const items = (f.mismatches_on_agreed_checks || []).map((m) => `<li>${m}</li>`).join("");
        const hum = (f.human_disagreement || []).length
          ? `<p class="meta">Human disagreement: ${f.human_disagreement.join(", ")}</p>`
          : "";
        return `<article class="fail-card">
          <h3>${f.case_id} · ${f.label || ""}</h3>
          <p class="meta">${f.product_name || ""} · agent <span class="pill ${f.agent_outcome}">${(f.agent_outcome || "").replace(/_/g, " ")}</span>
          · <a href="/?unit=${f.case_id}">Open on desk</a></p>
          <ul>${items}</ul>${hum}
        </article>`;
      })
      .join("");
  },
};

// Deep-link ?unit=UNIT-RCV-01
(function deepLink() {
  const u = new URLSearchParams(location.search).get("unit");
  if (u && document.getElementById("unit")) {
    const wait = setInterval(() => {
      const sel = document.getElementById("unit");
      if (sel && sel.options.length) {
        clearInterval(wait);
        if ([...sel.options].some((o) => o.value === u)) {
          sel.value = u;
          if (window.ReceivingDesk) {
            ReceivingDesk.syncRail();
            ReceivingDesk.loadShots();
          }
        }
      }
    }, 50);
    setTimeout(() => clearInterval(wait), 3000);
  }
})();
