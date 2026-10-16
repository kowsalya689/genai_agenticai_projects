"""Quantitative check: Precision@K of sub-category / main-category match on random products.
Run:  python -m scripts.evaluate"""
import numpy as np

from app.core.recommender import Recommender

K, SAMPLES = 10, 500

if __name__ == "__main__":
    rec = Recommender.build()
    rng = np.random.default_rng(0)
    ids = rng.choice(len(rec.df), SAMPLES, replace=False)
    sub_hits, main_hits = [], []
    for pid in ids:
        res = rec.recommend_by_id(int(pid), K)
        q = res["query"]
        sub_hits.append(np.mean([r["sub_category"] == q["sub_category"] for r in res["results"]]))
        main_hits.append(np.mean([r["main_category"] == q["main_category"] for r in res["results"]]))
    print(f"Precision@{K}  main_category: {np.mean(main_hits):.3f}   sub_category: {np.mean(sub_hits):.3f}")
