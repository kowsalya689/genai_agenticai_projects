
import numpy as np


def clause_to_vector(tokens, model):
    """Convert tokens into an average Word2Vec vector."""
    vectors = [
        model.wv[word]
        for word in tokens
        if word in model.wv
    ]

    if not vectors:
        return np.zeros(model.vector_size, dtype=np.float32)

    return np.mean(vectors, axis=0).astype(np.float32)
