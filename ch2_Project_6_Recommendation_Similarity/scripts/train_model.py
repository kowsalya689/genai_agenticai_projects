"""Train FastText + build the product-vector matrix.   Run:  python -m scripts.train_model"""
import logging
import time

from app.core.recommender import Recommender

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    t = time.time()
    rec = Recommender.build(force_retrain=True)
    print(f"Done in {time.time() - t:.0f}s  ->  {rec.stats()}")
