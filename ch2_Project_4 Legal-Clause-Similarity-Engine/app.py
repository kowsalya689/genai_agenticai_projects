"""
Legal Clause Similarity Engine - Flask backend
Run:  python app.py   ->  http://127.0.0.1:5000

Pipeline: input text -> preprocess -> Word2Vec embedding -> cosine similarity -> Top-K
Endpoints:
    GET/POST /            web UI (templates/index.html)
    POST     /api/similar JSON API  {"text": "...", "top_k": 5}
    GET      /health      health check
"""
import os
import sys
import pickle

import numpy as np
from flask import Flask, render_template, request, jsonify

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

app = Flask(__name__)

# ---------------------------------------------------------------------------
# 1. Use your existing src modules when possible, otherwise fall back safely.
#    If your function names differ, change the names in the lists below.
# ---------------------------------------------------------------------------
def _find(module_name, names):
    try:
        mod = __import__(module_name)
    except Exception:
        return None
    for n in names:
        if hasattr(mod, n):
            return getattr(mod, n)
    return None


_preprocess = _find("preprocess", ["preprocess_text", "preprocess", "clean_text", "tokenize"])
_embed = _find("embed", ["get_embedding", "embed_text", "get_sentence_vector", "sentence_vector", "embed"])


def preprocess(text):
    """Return a list of tokens."""
    if _preprocess:
        out = _preprocess(text)
        if isinstance(out, str):
            return out.split()
        return list(out)
    import re
    return re.findall(r"[a-z0-9]+", text.lower())


# ---------------------------------------------------------------------------
# 2. Load models / data once at startup
# ---------------------------------------------------------------------------
_PICKLE_PROBLEMS = []


def _load_pickle(name):
    """Load a pickle; return None (and remember why) if missing, empty or corrupt."""
    path = os.path.join(MODEL_DIR, name)
    if not os.path.exists(path):
        _PICKLE_PROBLEMS.append(f"{name}: file not found")
        return None
    if os.path.getsize(path) == 0:
        _PICKLE_PROBLEMS.append(f"{name}: file is EMPTY (0 bytes) - re-save it from your notebook/training script")
        return None
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        _PICKLE_PROBLEMS.append(f"{name}: cannot be read ({type(e).__name__}: {e})")
        return None


def _to_clause_list(obj):
    """Accept list / Series / DataFrame / dict and return list[str]."""
    if obj is None:
        return None
    try:
        import pandas as pd
        if isinstance(obj, pd.DataFrame):
            for col in ("clause", "clause_text", "text", "Clause", "Text"):
                if col in obj.columns:
                    return obj[col].astype(str).tolist()
            return obj.iloc[:, 0].astype(str).tolist()
        if isinstance(obj, pd.Series):
            return obj.astype(str).tolist()
    except ImportError:
        pass
    if isinstance(obj, dict):
        for k in ("clauses", "texts", "clause", "text"):
            if k in obj:
                return _to_clause_list(obj[k])
        return None
    if isinstance(obj, (list, tuple)) and obj and isinstance(obj[0], str):
        return list(obj)
    return None


# ---- clause types (used by the "Filter by type" dropdown) -----------------
import re as _re

TYPE_RULES = [
    ("Confidentiality", r"confiden|non-?disclos|proprietary information|trade secret"),
    ("Governing law", r"governed by|governing law|jurisdiction|laws of the"),
    ("Termination", r"terminat|expir"),
    ("Base salary", r"base salary|salary|compensation|wage|bonus|remuneration"),
    ("Payment terms", r"\bpay|invoice|\bfees?\b"),
    ("Indemnification", r"indemnif|hold harmless"),
    ("Compliance", r"complian|applicable laws?|regulation"),
]
TYPE_COLUMNS = ("clause_type", "type", "label", "category", "Clause Type", "Type", "Label", "Category")


def guess_type(text):
    t = text.lower()
    for name, pattern in TYPE_RULES:
        if _re.search(pattern, t):
            return name
    return "Other"


def _to_type_list(obj, clauses):
    """Use a type/label column from the data if present, otherwise guess from keywords."""
    try:
        import pandas as pd
        if isinstance(obj, pd.DataFrame):
            for col in TYPE_COLUMNS:
                if col in obj.columns and len(obj) == len(clauses):
                    return obj[col].astype(str).str.strip().tolist()
    except ImportError:
        pass
    return [guess_type(c) for c in clauses]


w2v = None
CLAUSE_TYPES = []
CLAUSES = []
CLAUSE_VECS = None
LOAD_ERROR = None


def _sentence_vector(tokens):
    """Mean of Word2Vec vectors (uses your embed.py if it exposes a function)."""
    if _embed:
        try:
            v = np.asarray(_embed(" ".join(tokens)), dtype=float)
            if v.ndim == 1 and v.any():
                return v
        except Exception:
            pass
    vecs = [w2v.wv[t] for t in tokens if t in w2v.wv]
    if not vecs:
        return np.zeros(w2v.vector_size)
    return np.mean(vecs, axis=0)


def _normalize(m):
    n = np.linalg.norm(m, axis=-1, keepdims=True)
    n[n == 0] = 1.0
    return m / n


def load_everything():
    global w2v, CLAUSES, CLAUSE_VECS, CLAUSE_TYPES, LOAD_ERROR
    try:
        from gensim.models import Word2Vec
        w2v = Word2Vec.load(os.path.join(MODEL_DIR, "legal_word2vec.model"))

        loaded = {}
        for name in ("clauses.pkl", "legal_clause_data.pkl", "clause.pkl"):
            loaded[name] = _load_pickle(name)
            if not CLAUSES:
                CLAUSES = _to_clause_list(loaded[name])
                source_obj = loaded[name]
        if not CLAUSES:
            raise ValueError("No clause texts could be loaded. " + " | ".join(_PICKLE_PROBLEMS))

        # reuse saved embeddings if one pickle is a matrix of the right size
        saved = None
        for obj in loaded.values():
            if isinstance(obj, np.ndarray) and obj.ndim == 2 and len(obj) == len(CLAUSES):
                saved = obj
                break
        if saved is None:
            cache = os.path.join(MODEL_DIR, "clause_vectors.npy")
            if os.path.exists(cache):
                cached = np.load(cache)
                if len(cached) == len(CLAUSES):
                    saved = cached
                    print("[ok] loaded cached clause vectors")
            if saved is None:
                print(f"[info] first run: embedding {len(CLAUSES)} clauses (saved afterwards, so next start is fast)...")
                rows = []
                for n, c in enumerate(CLAUSES, 1):
                    rows.append(_sentence_vector(preprocess(c)))
                    if n % 2000 == 0:
                        print(f"       {n}/{len(CLAUSES)}")
                saved = np.vstack(rows)
                try:
                    np.save(cache, saved)
                except OSError as e:
                    print("[warn] could not save cache:", e)
        CLAUSE_VECS = _normalize(saved.astype(float))
        CLAUSE_TYPES = _to_type_list(source_obj, CLAUSES)
        print(f"[ok] loaded {len(CLAUSES)} clauses, vector size {CLAUSE_VECS.shape[1]}")
    except Exception as e:  # keep the UI alive and show the reason
        LOAD_ERROR = f"{type(e).__name__}: {e}"
        print("[error]", LOAD_ERROR)


load_everything()


# ---------------------------------------------------------------------------
# 3. Search
# ---------------------------------------------------------------------------
def find_similar(text, top_k=5, clause_type=None):
    tokens = preprocess(text)
    if not tokens:
        raise ValueError("Please enter a legal clause, sentence or short paragraph.")
    q = _sentence_vector(tokens)
    if not q.any():
        raise ValueError("None of the words in your text were found in the model vocabulary.")
    q = q / np.linalg.norm(q)
    scores = CLAUSE_VECS @ q
    order = np.argsort(-scores)
    if clause_type and clause_type != "all":
        order = [i for i in order if CLAUSE_TYPES[i] == clause_type]
    idx = order[:top_k]
    return [
        {"rank": r + 1, "clause": CLAUSES[i], "type": CLAUSE_TYPES[i], "score": round(float(scores[i]), 4),
         "percent": round(max(float(scores[i]), 0) * 100, 1)}
        for r, i in enumerate(idx)
    ]


def _parse_top_k(value, default=5):
    try:
        return max(1, min(int(value), 20))
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# 4. Routes
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    ctx = {"query": "", "top_k": 5, "results": None, "error": LOAD_ERROR, "total": len(CLAUSES),
           "types": sorted(set(CLAUSE_TYPES)), "selected_type": "all"}
    if request.method == "POST":
        ctx["query"] = request.form.get("text", "").strip()
        ctx["top_k"] = _parse_top_k(request.form.get("top_k"))
        ctx["selected_type"] = request.form.get("clause_type", "all")
        if not LOAD_ERROR:
            try:
                ctx["results"] = find_similar(ctx["query"], ctx["top_k"], ctx["selected_type"])
            except ValueError as e:
                ctx["error"] = str(e)
    return render_template("index.html", **ctx)


@app.route("/api/similar", methods=["POST"])
def api_similar():
    if LOAD_ERROR:
        return jsonify({"error": LOAD_ERROR}), 500
    data = request.get_json(silent=True) or {}
    try:
        results = find_similar(str(data.get("text", "")).strip(), _parse_top_k(data.get("top_k")), data.get("clause_type"))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"query": data.get("text"), "results": results})


@app.route("/health")
def health():
    return jsonify({"status": "error" if LOAD_ERROR else "ok", "clauses": len(CLAUSES), "types": sorted(set(CLAUSE_TYPES))})


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)  # reloader would load spaCy/models twice
