"use strict";

const $ = (id) => document.getElementById(id);

const seedText = $("seedText");
const topK = $("topK");
const modelArch = $("modelArch");
const numWords = $("numWords");
const temperature = $("temperature");
const tempValue = $("tempValue");
const predictBtn = $("predictBtn");
const generateBtn = $("generateBtn");
const output = $("output");
const errorBox = $("error");
const statusBadge = $("statusBadge");

// Keep the temperature label in sync with the slider.
temperature.addEventListener("input", () => {
  tempValue.textContent = Number(temperature.value).toFixed(2);
});

function showError(message) {
  errorBox.textContent = message;
  errorBox.classList.remove("d-none");
}
function clearError() {
  errorBox.classList.add("d-none");
}
function setLoading(button, isLoading, label) {
  if (isLoading) {
    button.disabled = true;
    button.dataset.label = button.textContent;
    button.innerHTML =
      '<span class="spinner-border spinner-inline me-2" role="status"></span>' + label;
  } else {
    button.disabled = false;
    button.textContent = button.dataset.label || label;
  }
}

async function callApi(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) {
    const detail = Array.isArray(data.detail)
      ? data.detail.map((d) => d.msg).join("; ")
      : data.detail || "Request failed";
    throw new Error(detail);
  }
  return data;
}

function renderPredictions(data) {
  const chips = data.predictions
    .map(
      (p) =>
        `<span class="pred-chip" data-word="${p.word}">` +
        `${p.word}<span class="prob">${(p.probability * 100).toFixed(1)}%</span></span>`
    )
    .join("");
  output.innerHTML =
    `<div class="fw-semibold mb-2">Top ${data.predictions.length} next-word predictions</div>` +
    `<div>${chips}</div>` +
    `<div class="text-secondary small mt-2">Tip: click a word to append it to your input.</div>`;
  output.classList.remove("d-none");

  // Clicking a chip appends the word and re-predicts.
  output.querySelectorAll(".pred-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      seedText.value = (seedText.value.trim() + " " + chip.dataset.word).trim();
      doPredict();
    });
  });
}

function renderGeneration(data) {
  const seed = data.input.trim();
  const full = data.generated_text.trim();
  const newPart = full.startsWith(seed.toLowerCase())
    ? full.slice(seed.length)
    : " " + full;
  output.innerHTML =
    `<div class="fw-semibold mb-2">Generated continuation (temperature ${data.temperature})</div>` +
    `<div class="generated-text"><span class="seed">${seed}</span>` +
    `<span class="new">${newPart}</span></div>`;
  output.classList.remove("d-none");
}

async function doPredict() {
  clearError();
  const text = seedText.value.trim();
  if (!text) return showError("Please enter some text first.");
  setLoading(predictBtn, true, "Predicting…");
  try {
    const data = await callApi("/predict", {
      text,
      top_k: Number(topK.value),
      model: modelArch.value,
    });
    renderPredictions(data);
  } catch (e) {
    showError(e.message);
  } finally {
    setLoading(predictBtn, false, "Predict next word");
  }
}

async function doGenerate() {
  clearError();
  const text = seedText.value.trim();
  if (!text) return showError("Please enter some text first.");
  setLoading(generateBtn, true, "Generating…");
  try {
    const data = await callApi("/generate", {
      model: modelArch.value,
      text,
      num_words: Number(numWords.value),
      temperature: Number(temperature.value),
    });
    renderGeneration(data);
  } catch (e) {
    showError(e.message);
  } finally {
    setLoading(generateBtn, false, "Generate text");
  }
}

async function refreshHealth() {
  try {
    const res = await fetch("/health");
    const data = await res.json();
    if (data.model_loaded) {
      statusBadge.textContent = `model ready · vocab ${data.vocab_size}`;
      statusBadge.className = "badge rounded-pill mt-2 bg-success";
    } else {
      statusBadge.textContent = "model not loaded";
      statusBadge.className = "badge rounded-pill mt-2 bg-warning text-dark";
    }
  } catch {
    statusBadge.textContent = "API unreachable";
    statusBadge.className = "badge rounded-pill mt-2 bg-danger";
  }
}

async function loadModels() {
  try {
    const res = await fetch("/models");
    if (!res.ok) return;
    const data = await res.json();
    const opts = data.models
      .filter((m) => m.loaded)
      .map(
        (m) =>
          `<option value="${m.name}" ${m.name === data.default ? "selected" : ""}>` +
          `${m.name.toUpperCase()}</option>`
      );
    if (opts.length) modelArch.innerHTML = opts.join("");
  } catch (e) {
    /* keep the static LSTM option */
  }
}
loadModels();

predictBtn.addEventListener("click", doPredict);
generateBtn.addEventListener("click", doGenerate);
refreshHealth();
