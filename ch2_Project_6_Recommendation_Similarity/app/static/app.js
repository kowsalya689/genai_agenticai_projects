const $ = (id) => document.getElementById(id);
let mode = "text";

async function api(url, opts) {
  const r = await fetch(url, opts);
  const data = await r.json();
  if (!r.ok) throw new Error(data.detail || "Request failed");
  return data;
}

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function card(p, i) {
  const pct = Math.max(0, Math.min(100, Math.round(p.similarity * 100)));
  const price = p.discount_price ? `<span class="price">${esc(p.discount_price)}${p.actual_price ? `<s>${esc(p.actual_price)}</s>` : ""}</span>` : "";
  return `<div class="card">
    ${p.image ? `<img src="${esc(p.image)}" alt="" loading="lazy" onerror="this.style.display='none'">` : ""}
    <div class="body">
      <span class="rank">#${i + 1} · ID ${p.product_id}</span>
      <h3>${esc(p.name)}</h3>
      <span class="tag">${esc(p.main_category)} › ${esc(p.sub_category)}</span>
      ${price}
      <div class="score"><div class="bar"><i style="width:${pct}%"></i></div><b>${p.similarity.toFixed(3)}</b></div>
      ${p.link ? `<a href="${esc(p.link)}" target="_blank" rel="noopener">View product ↗</a>` : ""}
    </div></div>`;
}

async function run() {
  $("msg").textContent = "";
  const top_n = +$("top-n").value || 10;
  const category = $("category").value || null;
  $("go").disabled = true;
  try {
    let data;
    if (mode === "text") {
      const text = $("text-input").value.trim();
      if (!text) throw new Error("Enter some product text.");
      data = await api("/api/recommend/text", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, top_n, category }),
      });
    } else {
      const id = $("id-input").value;
      if (id === "") throw new Error("Enter a product ID.");
      const qs = new URLSearchParams({ top_n }); if (category) qs.set("category", category);
      data = await api(`/api/recommend/${id}?${qs}`);
    }
    const q = data.query;
    $("query-box").hidden = false;
    $("query-box").innerHTML = q.text
      ? `<h2>Query text</h2><p>${esc(q.text)}</p>`
      : `<h2>Query product</h2><p><b>${esc(q.name)}</b><br><span class="tag">${esc(q.main_category)} › ${esc(q.sub_category)}</span></p>`;
    $("results").innerHTML = data.results.map(card).join("") || "<p>No results.</p>";
  } catch (e) { $("msg").textContent = e.message; }
  $("go").disabled = false;
}

document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => {
  mode = b.dataset.mode;
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t === b));
  $("mode-text").hidden = mode !== "text";
  $("mode-id").hidden = mode !== "id";
}));

let timer;
$("name-input").addEventListener("input", (e) => {
  clearTimeout(timer);
  const q = e.target.value.trim();
  if (q.length < 2) { $("name-hits").innerHTML = ""; return; }
  timer = setTimeout(async () => {
    const hits = await api(`/api/products/search?q=${encodeURIComponent(q)}`);
    $("name-hits").innerHTML = hits.map((h) => `<li data-id="${h.product_id}">${esc(h.name)} <span class="tag">(ID ${h.product_id})</span></li>`).join("");
  }, 250);
});
$("name-hits").addEventListener("click", (e) => {
  const li = e.target.closest("li"); if (!li) return;
  $("id-input").value = li.dataset.id; $("name-hits").innerHTML = ""; run();
});
$("go").addEventListener("click", run);
document.addEventListener("keydown", (e) => { if (e.key === "Enter" && e.target.tagName === "INPUT") run(); });

(async () => {
  const [cats, health] = await Promise.all([api("/api/categories"), api("/api/health")]);
  $("category").innerHTML += cats.map((c) => `<option value="${esc(c)}">${esc(c)}</option>`).join("");
  $("stats").textContent = `${health.products.toLocaleString()} products · ${health.vocab_size.toLocaleString()} words · ${health.vector_size}-d FastText vectors · cosine similarity`;
})();
