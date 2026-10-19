"""
Semantic Search Studio — FastAPI web app
========================================
Backend : FastAPI + Uvicorn
Engines : TF-IDF, Word2Vec, FastText, Hybrid (TF-IDF + FastText)
Frontend: single-page UI served by this same file (no extra files needed)

SETUP (once):
    pip install fastapi uvicorn pandas numpy scikit-learn gensim

RUN:
    1. Put your CSV next to this file (or edit CSV_PATH below).
       Required columns: document_id, category, title, content, keywords
    2. python app.py
    3. Open http://127.0.0.1:8000

The first start trains the models (a few minutes for 50k docs) and caches them
in ./cache. Later starts load instantly. Delete ./cache to retrain.
"""

import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from gensim.models import FastText, Word2Vec
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
import joblib
import scipy.sparse as sp

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "knowledge_base_improved 1.csv"   # <-- change if needed
CACHE_DIR = BASE_DIR / "cache"
VECTOR_SIZE = 100
EPOCHS = 15
HOST, PORT = "127.0.0.1", 8000

STOP_WORDS = set(ENGLISH_STOP_WORDS)
CACHE_DIR.mkdir(exist_ok=True)


# ----------------------------------------------------------------------------
# TEXT PROCESSING (same logic as the notebook)
# ----------------------------------------------------------------------------
def preprocess_text(text) -> list:
    if not isinstance(text, str):
        text = ""
    text = text.lower()
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [t for t in text.split() if t not in STOP_WORDS]


def mean_vector(tokens, model) -> np.ndarray:
    vecs = [model.wv[t] for t in tokens if t in model.wv]
    if not vecs:
        return np.zeros(model.vector_size, dtype=np.float32)
    return np.mean(vecs, axis=0).astype(np.float32)


def l2_normalize(mat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


# ----------------------------------------------------------------------------
# SEARCH ENGINE
# ----------------------------------------------------------------------------
class SearchEngine:
    def __init__(self):
        self.df = None
        self.tokens = None
        self.categories = []
        self.tfidf = None
        self.tfidf_matrix = None
        self.w2v = None
        self.w2v_docs = None
        self.ft = None
        self.ft_docs = None
        self.ready = False

    def load(self):
        t0 = time.time()
        if not CSV_PATH.exists():
            sys.exit(f"\n[ERROR] CSV not found: {CSV_PATH}\n"
                     f"Place your dataset there or edit CSV_PATH in app.py.\n")

        df = pd.read_csv(CSV_PATH)
        for col in ["document_id", "category", "title", "content", "keywords"]:
            if col not in df.columns:
                sys.exit(f"[ERROR] Missing column '{col}' in CSV.")
        df = df.fillna("")
        df["text"] = (df["title"].astype(str) + " " + df["content"].astype(str)
                      + " " + df["keywords"].astype(str))
        self.df = df.reset_index(drop=True)
        self.categories = sorted(df["category"].astype(str).unique().tolist())

        print(f"[1/4] Preprocessing {len(df):,} documents ...")
        self.tokens = [preprocess_text(t) for t in self.df["text"]]

        # --- TF-IDF ---
        tf_vec, tf_mat = CACHE_DIR / "tfidf_vectorizer.joblib", CACHE_DIR / "tfidf_matrix.npz"
        if tf_vec.exists() and tf_mat.exists():
            print("[2/4] Loading cached TF-IDF ...")
            self.tfidf = joblib.load(tf_vec)
            self.tfidf_matrix = sp.load_npz(tf_mat)
        else:
            print("[2/4] Building TF-IDF ...")
            self.tfidf = TfidfVectorizer(lowercase=False, tokenizer=str.split,
                                         token_pattern=None, norm="l2")
            self.tfidf_matrix = self.tfidf.fit_transform(" ".join(t) for t in self.tokens)
            joblib.dump(self.tfidf, tf_vec)
            sp.save_npz(tf_mat, self.tfidf_matrix)

        workers = max(1, (os.cpu_count() or 2) - 1)

        # --- Word2Vec ---
        w_model, w_docs = CACHE_DIR / "word2vec.model", CACHE_DIR / "w2v_docs.npy"
        if w_model.exists() and w_docs.exists():
            print("[3/4] Loading cached Word2Vec ...")
            self.w2v = Word2Vec.load(str(w_model))
            self.w2v_docs = np.load(w_docs)
        else:
            print("[3/4] Training Word2Vec ...")
            self.w2v = Word2Vec(sentences=self.tokens, vector_size=VECTOR_SIZE, window=5,
                                min_count=1, workers=workers, sg=1, epochs=EPOCHS, seed=42)
            self.w2v_docs = l2_normalize(np.array([mean_vector(t, self.w2v) for t in self.tokens]))
            self.w2v.save(str(w_model))
            np.save(w_docs, self.w2v_docs)

        # --- FastText ---
        f_model, f_docs = CACHE_DIR / "fasttext.model", CACHE_DIR / "ft_docs.npy"
        if f_model.exists() and f_docs.exists():
            print("[4/4] Loading cached FastText ...")
            self.ft = FastText.load(str(f_model))
            self.ft_docs = np.load(f_docs)
        else:
            print("[4/4] Training FastText (this is the slowest step) ...")
            self.ft = FastText(vector_size=VECTOR_SIZE, window=5, min_count=1,
                               workers=workers, sg=1, min_n=3, max_n=6, seed=42)
            self.ft.build_vocab(corpus_iterable=self.tokens)
            self.ft.train(corpus_iterable=self.tokens, total_examples=len(self.tokens),
                          epochs=EPOCHS)
            self.ft_docs = l2_normalize(np.array([mean_vector(t, self.ft) for t in self.tokens]))
            self.ft.save(str(f_model))
            np.save(f_docs, self.ft_docs)

        self.ready = True
        print(f"Ready in {time.time() - t0:.1f}s  ->  http://{HOST}:{PORT}")

    # ---- scoring per engine ----
    def _tfidf_scores(self, q_tokens):
        qv = self.tfidf.transform([" ".join(q_tokens)])
        return (self.tfidf_matrix @ qv.T).toarray().ravel()

    def _embed_scores(self, q_tokens, model, docs):
        qv = mean_vector(q_tokens, model)
        n = np.linalg.norm(qv)
        if n == 0:
            return np.zeros(len(docs), dtype=np.float32)
        return docs @ (qv / n)

    def search(self, query, engine="hybrid", top_k=8, category=None):
        q_tokens = preprocess_text(query)
        if not q_tokens:
            return [], q_tokens

        if engine == "tfidf":
            scores = self._tfidf_scores(q_tokens)
        elif engine == "word2vec":
            scores = self._embed_scores(q_tokens, self.w2v, self.w2v_docs)
        elif engine == "fasttext":
            scores = self._embed_scores(q_tokens, self.ft, self.ft_docs)
        else:  # hybrid: lexical precision + subword robustness to typos
            scores = (0.5 * self._tfidf_scores(q_tokens)
                      + 0.5 * self._embed_scores(q_tokens, self.ft, self.ft_docs))

        if category and category != "all":
            mask = (self.df["category"].astype(str) == category).to_numpy()
            scores = np.where(mask, scores, -1.0)

        k = min(top_k, len(scores))
        idx = np.argpartition(-scores, k - 1)[:k]
        idx = idx[np.argsort(-scores[idx])]

        results = []
        for i in idx:
            if scores[i] <= 0:
                continue
            row = self.df.iloc[i]
            results.append({
                "document_id": str(row["document_id"]),
                "title": str(row["title"]),
                "category": str(row["category"]),
                "snippet": str(row["content"])[:220].rstrip() + "...",
                "keywords": [k.strip() for k in str(row["keywords"]).split(",") if k.strip()][:6],
                "score": round(float(scores[i]), 4),
            })
        return results, q_tokens


engine = SearchEngine()

# ----------------------------------------------------------------------------
# API
# ----------------------------------------------------------------------------
app = FastAPI(title="Semantic Search Studio", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def _startup():
    engine.load()


@app.get("/api/meta")
def meta():
    return {
        "documents": len(engine.df),
        "categories": engine.categories,
        "engines": ["hybrid", "fasttext", "word2vec", "tfidf"],
        "vocabulary": len(engine.ft.wv),
    }


@app.get("/api/search")
def api_search(
    q: str = Query(..., min_length=1, max_length=300),
    engine_name: str = Query("hybrid", alias="engine"),
    top_k: int = Query(8, ge=1, le=50),
    category: str = Query("all"),
):
    if engine_name not in {"hybrid", "fasttext", "word2vec", "tfidf"}:
        raise HTTPException(400, "Unknown engine")
    t0 = time.perf_counter()
    results, tokens = engine.search(q, engine_name, top_k, category)
    return {
        "query": q,
        "engine": engine_name,
        "tokens": tokens,
        "count": len(results),
        "took_ms": round((time.perf_counter() - t0) * 1000, 1),
        "results": results,
    }


@app.get("/api/doc/{doc_id}")
def api_doc(doc_id: str):
    hit = engine.df[engine.df["document_id"].astype(str) == doc_id]
    if hit.empty:
        raise HTTPException(404, "Document not found")
    r = hit.iloc[0]
    return {
        "document_id": str(r["document_id"]),
        "title": str(r["title"]),
        "category": str(r["category"]),
        "content": str(r["content"]),
        "keywords": [k.strip() for k in str(r["keywords"]).split(",") if k.strip()],
    }


@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_PAGE


# ----------------------------------------------------------------------------
# FRONTEND (HTML + CSS + JS)
# ----------------------------------------------------------------------------
HTML_PAGE = r"""<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Semantic Search Studio</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#0b0d17; --bg2:#11142a; --card:rgba(255,255,255,.04); --border:rgba(255,255,255,.09);
  --text:#e9ecff; --muted:#9aa1c7; --accent:#7c5cff; --accent2:#22d3ee; --good:#34d399;
  --shadow:0 10px 40px rgba(0,0,0,.35);
}
[data-theme="light"]{
  --bg:#f5f6ff; --bg2:#ffffff; --card:rgba(255,255,255,.85); --border:rgba(20,20,60,.10);
  --text:#161a3a; --muted:#6a7096; --shadow:0 10px 40px rgba(60,60,140,.12);
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Inter,system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;
  background-image:radial-gradient(900px 500px at 10% -10%,rgba(124,92,255,.25),transparent 60%),
                   radial-gradient(800px 500px at 100% 0%,rgba(34,211,238,.18),transparent 60%);
  background-attachment:fixed;transition:background .3s,color .3s}
.wrap{max-width:980px;margin:0 auto;padding:28px 20px 80px}
header{display:flex;justify-content:space-between;align-items:center;margin-bottom:46px}
.brand{display:flex;align-items:center;gap:12px;font-weight:700;font-size:18px}
.logo{width:38px;height:38px;border-radius:11px;display:grid;place-items:center;font-size:20px;
  background:linear-gradient(135deg,var(--accent),var(--accent2));box-shadow:0 6px 20px rgba(124,92,255,.45)}
.tbtn{background:var(--card);border:1px solid var(--border);color:var(--text);width:40px;height:40px;
  border-radius:12px;cursor:pointer;font-size:17px;transition:.2s}
.tbtn:hover{transform:translateY(-2px)}
.hero{text-align:center;margin-bottom:30px}
.hero h1{font-size:clamp(30px,5vw,50px);font-weight:800;letter-spacing:-1.2px;line-height:1.1}
.grad{background:linear-gradient(90deg,var(--accent),var(--accent2));-webkit-background-clip:text;
  background-clip:text;color:transparent}
.hero p{color:var(--muted);margin-top:14px;font-size:16px}
.search{position:relative;background:var(--card);border:1px solid var(--border);border-radius:20px;
  box-shadow:var(--shadow);backdrop-filter:blur(14px);display:flex;align-items:center;padding:6px 8px 6px 20px;
  transition:.25s}
.search:focus-within{border-color:var(--accent);box-shadow:0 0 0 4px rgba(124,92,255,.18),var(--shadow)}
.search svg{flex:none;opacity:.6}
.search input{flex:1;background:none;border:none;outline:none;color:var(--text);font:500 17px Inter;padding:16px 14px}
.search input::placeholder{color:var(--muted)}
.go{border:none;cursor:pointer;color:#fff;font:600 15px Inter;padding:14px 26px;border-radius:14px;
  background:linear-gradient(135deg,var(--accent),#5b8cff);transition:.2s}
.go:hover{filter:brightness(1.1);transform:translateY(-1px)}
.controls{display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;margin:18px 2px 8px}
.pills{display:flex;gap:8px;flex-wrap:wrap}
.pill{background:var(--card);border:1px solid var(--border);color:var(--muted);padding:8px 15px;border-radius:999px;
  font:600 13px Inter;cursor:pointer;transition:.2s}
.pill:hover{color:var(--text)}
.pill.active{color:#fff;border-color:transparent;background:linear-gradient(135deg,var(--accent),var(--accent2))}
select{background:var(--card);border:1px solid var(--border);color:var(--text);padding:9px 12px;border-radius:12px;
  font:500 13px Inter;outline:none;cursor:pointer}
select option{color:#111}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin:14px 2px 0;justify-content:center}
.chip{font-size:13px;color:var(--muted);border:1px dashed var(--border);padding:6px 12px;border-radius:999px;cursor:pointer;transition:.2s}
.chip:hover{color:var(--text);border-color:var(--accent)}
.status{display:flex;justify-content:space-between;color:var(--muted);font-size:13px;margin:26px 4px 12px;min-height:20px}
.tok{color:var(--accent2)}
.results{display:grid;gap:14px}
.card{background:var(--card);border:1px solid var(--border);border-radius:18px;padding:20px 22px;cursor:pointer;
  backdrop-filter:blur(10px);transition:.22s;animation:rise .4s both}
.card:hover{transform:translateY(-3px);border-color:var(--accent);box-shadow:var(--shadow)}
@keyframes rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
.row{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}
.rank{font-weight:800;color:var(--accent);font-size:13px;margin-bottom:6px}
.card h3{font-size:18px;font-weight:700;letter-spacing:-.3px}
.cat{flex:none;font-size:12px;font-weight:600;padding:5px 11px;border-radius:999px;
  background:rgba(124,92,255,.15);color:var(--accent)}
.snip{color:var(--muted);font-size:14px;line-height:1.6;margin:10px 0 14px}
.kw{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px}
.kw span{font-size:12px;color:var(--muted);background:rgba(127,127,160,.12);padding:4px 9px;border-radius:8px}
.bar{height:6px;border-radius:99px;background:rgba(127,127,160,.18);overflow:hidden}
.bar i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--accent),var(--accent2));
  transition:width .7s cubic-bezier(.2,.8,.2,1)}
.score{font-size:12px;color:var(--good);font-weight:700;margin-top:7px;text-align:right}
.empty{text-align:center;padding:60px 20px;color:var(--muted)}
.empty .big{font-size:44px;margin-bottom:10px}
.skel{height:150px;border-radius:18px;background:linear-gradient(90deg,var(--card),rgba(127,127,160,.12),var(--card));
  background-size:200% 100%;animation:sh 1.2s infinite}
@keyframes sh{to{background-position:-200% 0}}
.modal{position:fixed;inset:0;background:rgba(5,6,15,.65);backdrop-filter:blur(6px);display:none;
  align-items:center;justify-content:center;padding:20px;z-index:50}
.modal.open{display:flex}
.sheet{background:var(--bg2);border:1px solid var(--border);border-radius:22px;max-width:680px;width:100%;
  max-height:85vh;overflow:auto;padding:30px;box-shadow:var(--shadow);animation:rise .25s both}
.sheet h2{font-size:24px;letter-spacing:-.4px;margin:10px 0 14px}
.sheet p{color:var(--muted);line-height:1.75;font-size:15px}
.x{float:right;background:none;border:none;color:var(--muted);font-size:24px;cursor:pointer}
footer{text-align:center;color:var(--muted);font-size:12px;margin-top:50px}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand"><div class="logo">🔎</div>Semantic Search Studio</div>
    <button class="tbtn" id="theme" title="Toggle theme">🌙</button>
  </header>

  <section class="hero">
    <h1>Find answers by <span class="grad">meaning</span>,<br>not just keywords</h1>
    <p id="sub">Search across your knowledge base with TF-IDF, Word2Vec and FastText.</p>
  </section>

  <div class="search">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
    <input id="q" placeholder="Try: forgot my passwrd, refund status, update billing date..." autofocus autocomplete="off">
    <button class="go" id="go">Search</button>
  </div>

  <div class="controls">
    <div class="pills" id="engines">
      <button class="pill active" data-e="hybrid">✨ Hybrid</button>
      <button class="pill" data-e="fasttext">FastText</button>
      <button class="pill" data-e="word2vec">Word2Vec</button>
      <button class="pill" data-e="tfidf">TF-IDF</button>
    </div>
    <div style="display:flex;gap:10px">
      <select id="cat"><option value="all">All categories</option></select>
      <select id="k"><option>5</option><option selected>8</option><option>12</option><option>20</option></select>
    </div>
  </div>

  <div class="chips" id="chips">
    <span class="chip">forgot my passwrd</span>
    <span class="chip">change billing date</span>
    <span class="chip">cancel subscription</span>
    <span class="chip">website search not workng</span>
  </div>

  <div class="status"><span id="left"></span><span id="right"></span></div>
  <div class="results" id="res">
    <div class="empty"><div class="big">💡</div>Type a question above to start searching.</div>
  </div>
  <footer>FastAPI · gensim · scikit-learn</footer>
</div>

<div class="modal" id="modal"><div class="sheet" id="sheet"></div></div>

<script>
const $=s=>document.querySelector(s);
let engine="hybrid", timer=null;

// theme
const root=document.documentElement;
const saved=localStorage.getItem("theme"); if(saved){root.dataset.theme=saved}
const syncIcon=()=>$("#theme").textContent=root.dataset.theme==="dark"?"🌙":"☀️";
syncIcon();
$("#theme").onclick=()=>{root.dataset.theme=root.dataset.theme==="dark"?"light":"dark";
  localStorage.setItem("theme",root.dataset.theme);syncIcon()};

// meta
fetch("/api/meta").then(r=>r.json()).then(m=>{
  $("#sub").textContent=`Searching ${m.documents.toLocaleString()} documents across ${m.categories.length} categories.`;
  m.categories.forEach(c=>{const o=document.createElement("option");o.value=c;o.textContent=c;$("#cat").appendChild(o)});
});

// engine pills
$("#engines").onclick=e=>{
  const b=e.target.closest(".pill"); if(!b) return;
  document.querySelectorAll(".pill").forEach(p=>p.classList.remove("active"));
  b.classList.add("active"); engine=b.dataset.e; search();
};
document.querySelectorAll(".chip").forEach(c=>c.onclick=()=>{$("#q").value=c.textContent;search()});
$("#cat").onchange=search; $("#k").onchange=search; $("#go").onclick=search;
$("#q").addEventListener("input",()=>{clearTimeout(timer);timer=setTimeout(search,350)});
$("#q").addEventListener("keydown",e=>{if(e.key==="Enter"){clearTimeout(timer);search()}});

const esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

async function search(){
  const q=$("#q").value.trim();
  if(!q){$("#res").innerHTML='<div class="empty"><div class="big">💡</div>Type a question above to start searching.</div>';
    $("#left").textContent="";$("#right").textContent="";return}
  $("#res").innerHTML='<div class="skel"></div><div class="skel"></div><div class="skel"></div>';
  try{
    const url=`/api/search?q=${encodeURIComponent(q)}&engine=${engine}&top_k=${$("#k").value}&category=${encodeURIComponent($("#cat").value)}`;
    const d=await (await fetch(url)).json();
    render(d);
  }catch(e){
    $("#res").innerHTML='<div class="empty"><div class="big">⚠️</div>Could not reach the server.</div>';
  }
}

function render(d){
  $("#left").innerHTML=d.count?`<b>${d.count}</b> results · understood as <span class="tok">${esc(d.tokens.join(" · "))}</span>`:"";
  $("#right").textContent=`${d.took_ms} ms · ${d.engine}`;
  if(!d.count){
    $("#res").innerHTML=`<div class="empty"><div class="big">🤷</div>No matches found.<br>
      <small>Words not in the knowledge base score zero in Word2Vec/TF-IDF. Try the Hybrid or FastText engine.</small></div>`;
    return;
  }
  const max=Math.max(...d.results.map(r=>r.score),0.0001);
  $("#res").innerHTML=d.results.map((r,i)=>`
    <div class="card" style="animation-delay:${i*40}ms" data-id="${esc(r.document_id)}">
      <div class="row"><div><div class="rank">#${i+1} · ${esc(r.document_id)}</div><h3>${esc(r.title)}</h3></div>
        <span class="cat">${esc(r.category)}</span></div>
      <p class="snip">${esc(r.snippet)}</p>
      <div class="kw">${r.keywords.map(k=>`<span>${esc(k)}</span>`).join("")}</div>
      <div class="bar"><i style="width:0" data-w="${Math.round(r.score/max*100)}"></i></div>
      <div class="score">similarity ${(r.score*100).toFixed(1)}%</div>
    </div>`).join("");
  requestAnimationFrame(()=>document.querySelectorAll(".bar i").forEach(b=>b.style.width=b.dataset.w+"%"));
}

// detail modal
$("#res").onclick=async e=>{
  const c=e.target.closest(".card"); if(!c) return;
  const d=await (await fetch("/api/doc/"+c.dataset.id)).json();
  $("#sheet").innerHTML=`<button class="x" onclick="closeM()">×</button>
    <span class="cat">${esc(d.category)}</span><h2>${esc(d.title)}</h2>
    <p>${esc(d.content)}</p>
    <div class="kw" style="margin-top:18px">${d.keywords.map(k=>`<span>${esc(k)}</span>`).join("")}</div>`;
  $("#modal").classList.add("open");
};
const closeM=()=>$("#modal").classList.remove("open");
$("#modal").onclick=e=>{if(e.target.id==="modal")closeM()};
document.addEventListener("keydown",e=>{if(e.key==="Escape")closeM()});
</script>
</body>
</html>
"""

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
