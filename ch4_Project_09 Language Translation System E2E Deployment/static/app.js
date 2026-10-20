"use strict";

// --- Element references -----------------------------------------------------
const els = {
  sourceLang: document.getElementById("source-lang"),
  targetLang: document.getElementById("target-lang"),
  input: document.getElementById("input"),
  output: document.getElementById("output"),
  translateBtn: document.getElementById("translate-btn"),
  swapBtn: document.getElementById("swap-btn"),
  clearBtn: document.getElementById("clear-btn"),
  copyBtn: document.getElementById("copy-btn"),
  charCount: document.getElementById("char-count"),
  detected: document.getElementById("detected"),
  latency: document.getElementById("latency"),
  status: document.getElementById("status"),
};

let LANGS = [];

// --- Populate language dropdowns from the backend ---------------------------
async function loadLanguages() {
  const res = await fetch("/api/languages");
  LANGS = await res.json();

  for (const { iso, name } of LANGS) {
    els.sourceLang.appendChild(new Option(name, iso));
    els.targetLang.appendChild(new Option(name, iso));
  }
  // Sensible defaults: detect -> Hindi.
  els.sourceLang.value = "auto";
  els.targetLang.value = LANGS.some((l) => l.iso === "hi") ? "hi" : LANGS[0].iso;
}

// --- Helpers ----------------------------------------------------------------
function isoName(iso) {
  const l = LANGS.find((x) => x.iso === iso);
  return l ? l.name : iso;
}

function updateCharCount() {
  els.charCount.textContent = `${els.input.value.length} / 2000`;
}

function setLoading(on) {
  els.translateBtn.disabled = on;
  els.translateBtn.innerHTML = on
    ? '<span class="spinner"></span>Translating...'
    : "Translate";
}

// --- Core: call the backend -------------------------------------------------
async function translate() {
  const text = els.input.value.trim();
  els.output.classList.remove("error");
  els.detected.textContent = "";
  els.latency.textContent = "";
  els.status.textContent = "";

  if (!text) {
    els.output.textContent = "";
    els.status.textContent = "Enter some text first.";
    return;
  }

  setLoading(true);
  els.output.textContent = "";
  try {
    const res = await fetch("/api/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        target: els.targetLang.value,
        source: els.sourceLang.value,
      }),
    });
    const data = await res.json();

    if (!res.ok) {
      els.output.textContent = data.error || "Something went wrong.";
      els.output.classList.add("error");
      return;
    }

    els.output.textContent = data.translation;
    if (els.sourceLang.value === "auto") {
      els.detected.textContent = `Detected: ${data.src_name} (${Math.round(
        data.confidence * 100
      )}%)`;
    }
    els.latency.textContent = `${data.latency_ms} ms`;
  } catch (err) {
    els.output.textContent = "Could not reach the server. Is it running?";
    els.output.classList.add("error");
  } finally {
    setLoading(false);
  }
}

// --- Swap source/target -----------------------------------------------------
function swap() {
  // If source is "auto", fall back to the detected/first real language.
  let src = els.sourceLang.value;
  if (src === "auto") src = LANGS[0].iso;
  const tgt = els.targetLang.value;

  els.sourceLang.value = tgt;
  els.targetLang.value = src;

  // Swap the text too, if there is a translation.
  const out = els.output.textContent.trim();
  if (out) {
    els.input.value = out;
    els.output.textContent = "";
    updateCharCount();
  }
}

// --- Wire up events ---------------------------------------------------------
els.translateBtn.addEventListener("click", translate);
els.swapBtn.addEventListener("click", swap);
els.input.addEventListener("input", updateCharCount);
els.clearBtn.addEventListener("click", () => {
  els.input.value = "";
  els.output.textContent = "";
  updateCharCount();
  els.detected.textContent = "";
  els.latency.textContent = "";
  els.status.textContent = "";
});
els.copyBtn.addEventListener("click", async () => {
  const text = els.output.textContent.trim();
  if (!text) return;
  await navigator.clipboard.writeText(text);
  els.status.textContent = "Copied!";
  setTimeout(() => (els.status.textContent = ""), 1500);
});
// Ctrl/Cmd + Enter to translate.
els.input.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") translate();
});

loadLanguages();
updateCharCount();
