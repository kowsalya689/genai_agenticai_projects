import { api, ApiError } from "./api.js";
import { buildSegments } from "./highlight.js";

const $ = (id) => document.getElementById(id);
const el = {
  status: $("status"), statusText: $("statusText"),
  samples: $("samples"), file: $("fileInput"), ratio: $("ratio"), ratioOut: $("ratioOut"),
  btn: $("summarizeBtn"), source: $("source"), sourceMeta: $("sourceMeta"), sourceSheet: $("sourceSheet"), clear: $("clearBtn"),
  summaryMeta: $("summaryMeta"), actions: $("actions"), copy: $("copyBtn"), download: $("downloadBtn"),
  empty: $("emptyState"), loading: $("loadingState"), loadingText: $("loadingText"), error: $("errorState"), result: $("resultState"),
  summaryText: $("summaryText"), ledger: $("ledgerList"), stats: $("stats"), toast: $("toast"),
};
const state = { modelReady: false, busy: false, lastSummary: "", abort: null };
const nf = new Intl.NumberFormat();

// ---------------------------------------------------------------- helpers
function toast(msg) {
  el.toast.textContent = msg; el.toast.hidden = false;
  clearTimeout(toast.t); toast.t = setTimeout(() => (el.toast.hidden = true), 2200);
}
function show(which) {
  for (const k of ["empty", "loading", "error", "result"]) el[k].hidden = k !== which;
  el.actions.hidden = which !== "result";
}
function words(s) { const t = s.trim(); return t ? t.split(/\s+/).length : 0; }
function updateSourceMeta() {
  const n = words(el.source.value);
  el.sourceMeta.textContent = n ? `${nf.format(n)} words` : "Paste text, load a sample or drop a file here";
  el.clear.hidden = !n;
  syncButton();
}
function syncButton() {
  el.btn.disabled = !state.modelReady || state.busy || el.source.value.trim().length < 10;
  el.btn.textContent = state.busy ? "Summarising" : "Summarise";
  el.btn.title = state.modelReady ? "" : "The model is still loading";
}
function ratioLabel() {
  const pct = +el.ratio.value;
  el.ratioOut.textContent = `${pct}% of the source`;
}

// ---------------------------------------------------------------- health polling
async function pollHealth() {
  try {
    const h = await api.health();
    if (h.status === "ok") {
      state.modelReady = true;
      el.status.dataset.state = "ready";
      el.statusText.textContent = `Model ready on ${h.device || "cpu"}`;
      syncButton();
      return;                                   // stop polling
    }
    if (h.status === "error") {
      el.status.dataset.state = "error";
      el.statusText.textContent = "Model failed to load, see the server log";
      return;
    }
    el.status.dataset.state = "loading";
    el.statusText.textContent = "Loading the model, this takes a minute on first start";
  } catch {
    el.status.dataset.state = "error";
    el.statusText.textContent = "Cannot reach the server";
  }
  setTimeout(pollHealth, 2000);
}

// ---------------------------------------------------------------- samples + files
async function loadSamples() {
  try {
    const samples = await api.samples();
    for (const s of samples) {
      const b = document.createElement("button");
      b.type = "button"; b.className = "chip"; b.textContent = s.title; b.setAttribute("aria-pressed", "false");
      b.addEventListener("click", () => {
        el.samples.querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", String(c === b)));
        el.source.value = s.text; updateSourceMeta(); show("empty");
      });
      el.samples.append(b);
    }
  } catch { /* samples are optional */ }
}

async function handleFile(file) {
  if (!file) return;
  el.sourceMeta.textContent = `Reading ${file.name}`;
  try {
    const r = await api.extract(file);
    el.source.value = r.text;
    el.samples.querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", "false"));
    updateSourceMeta(); show("empty");
    toast(`Loaded ${file.name}`);
  } catch (err) {
    updateSourceMeta(); showError(err);
  } finally { el.file.value = ""; }
}

// ---------------------------------------------------------------- render
function showError(err) {
  const e = err instanceof ApiError ? err : new ApiError(String(err?.message || err));
  el.error.replaceChildren();
  const strong = document.createElement("strong"); strong.textContent = e.message;
  el.error.append(strong);
  if (e.requestId) { const s = document.createElement("small"); s.textContent = `Reference ${e.requestId}`; el.error.append(s); }
  show("error");
}

function renderSummary(r) {
  state.lastSummary = r.summary;
  // build DOM nodes (never innerHTML) so document text can't inject markup
  el.summaryText.replaceChildren(...buildSegments(r.summary, r.faithfulness).map((seg) => {
    if (seg.kind === "plain") return document.createTextNode(seg.text);
    const m = document.createElement("mark"); m.className = seg.kind; m.textContent = seg.text;
    if (seg.kind === "flag") m.title = "Not found in the source document";
    return m;
  }));

  const f = r.faithfulness;
  const rows = [];
  const flagged = [...f.unsupported_numbers, ...f.unsupported_dates];
  rows.push({ bad: flagged.length > 0,
    text: f.n_numbers === 0 && flagged.length === 0 ? "The summary contains no numbers or dates."
      : flagged.length ? "Not found in the source:" : `All ${f.n_numbers} numbers and dates appear in the source.`,
    items: flagged });
  rows.push({ bad: f.unsupported_terms.length > 0,
    text: f.unsupported_terms.length ? "Names or terms not found in the source:" : f.n_terms ? `All ${f.n_terms} names and defined terms appear in the source.` : "No names or defined terms to check.",
    items: f.unsupported_terms });
  el.ledger.replaceChildren(...rows.map((row) => {
    const li = document.createElement("li"); if (row.bad) li.className = "bad";
    const tick = document.createElement("span"); tick.className = "tick"; tick.textContent = row.bad ? "!" : "\u2713"; tick.setAttribute("aria-hidden", "true");
    const t = document.createElement("span"); t.textContent = row.text;
    li.append(tick, t);
    if (row.items.length) { const i = document.createElement("span"); i.className = "items"; i.textContent = row.items.join(", "); li.append(i); }
    return li;
  }));

  const pct = (r.compression_ratio * 100).toFixed(1);
  const stats = [
    ["Source", `${nf.format(r.source_tokens)} tokens`],
    ["Summary", `${nf.format(r.summary_tokens)} tokens`],
    ["Length", `${pct}% of source`],
    ["Passes", `${r.passes.length}${r.passes[0]?.chunks > 1 ? ` (${r.passes[0].chunks} chunks)` : ""}`],
    ["Time", `${(r.elapsed_ms / 1000).toFixed(1)} s`],
  ];
  el.stats.replaceChildren(...stats.map(([k, v]) => {
    const d = document.createElement("div"), dt = document.createElement("dt"), dd = document.createElement("dd");
    dt.textContent = k; dd.textContent = v; d.append(dt, dd); return d;
  }));
  el.summaryMeta.textContent = `${nf.format(r.summary_words)} words`;
  show("result");
}

// ---------------------------------------------------------------- summarise
async function summarise() {
  if (el.btn.disabled) return;
  state.busy = true; syncButton(); show("loading"); el.summaryMeta.textContent = "";
  const t0 = Date.now();
  const tick = setInterval(() => {
    const s = Math.round((Date.now() - t0) / 1000);
    el.loadingText.textContent = `Summarising, ${s}s elapsed. Long documents are split into chunks and take longer on a CPU.`;
  }, 1000);
  el.loadingText.textContent = "Summarising";
  try {
    const r = await api.summarize({ text: el.source.value, compression: +el.ratio.value / 100 });
    renderSummary(r);
  } catch (err) {
    showError(err);
  } finally {
    clearInterval(tick); state.busy = false; syncButton();
  }
}

// ---------------------------------------------------------------- wiring
el.ratio.addEventListener("input", ratioLabel);
el.source.addEventListener("input", updateSourceMeta);
el.source.addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") summarise(); });
el.btn.addEventListener("click", summarise);
el.clear.addEventListener("click", () => {
  el.source.value = ""; el.samples.querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", "false"));
  updateSourceMeta(); show("empty"); el.summaryMeta.textContent = ""; el.source.focus();
});
el.file.addEventListener("change", () => handleFile(el.file.files[0]));
el.copy.addEventListener("click", async () => {
  try { await navigator.clipboard.writeText(state.lastSummary); toast("Summary copied"); } catch { toast("Copy failed, select the text and copy manually"); }
});
el.download.addEventListener("click", () => {
  const url = URL.createObjectURL(new Blob([state.lastSummary], { type: "text/plain;charset=utf-8" }));
  const a = Object.assign(document.createElement("a"), { href: url, download: "summary.txt" });
  document.body.append(a); a.click(); a.remove(); URL.revokeObjectURL(url);
});
for (const ev of ["dragenter", "dragover"]) el.sourceSheet.addEventListener(ev, (e) => { e.preventDefault(); el.sourceSheet.classList.add("dragging"); });
for (const ev of ["dragleave", "drop"]) el.sourceSheet.addEventListener(ev, (e) => { e.preventDefault(); el.sourceSheet.classList.remove("dragging"); });
el.sourceSheet.addEventListener("drop", (e) => handleFile(e.dataTransfer?.files?.[0]));

ratioLabel(); updateSourceMeta(); loadSamples(); pollHealth();
