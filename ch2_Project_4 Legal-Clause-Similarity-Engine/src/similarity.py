
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from src.embed import clause_to_vector
from src.preprocess import preprocess_text


def find_similar_clauses(query, clauses, model, top_k=5):
    """Return the top matching clauses for a user query."""

    query_tokens = preprocess_text(query)
    query_vector = clause_to_vector(query_tokens, model).reshape(1, -1)

    if np.linalg.norm(query_vector) == 0:
        return []

    results = []

    for index, row in clauses.iterrows():
        # The dataset should contain a precomputed vector column
        if "sentence_vector" in clauses.columns:
            clause_vector = np.asarray(
                row["sentence_vector"], dtype=np.float32
            )
        else:
            text_column = next(
                (col for col in ["clause_text", "text", "clause"]
                 if col in clauses.columns),
                None
            )

            if text_column is None:
                raise ValueError(
                    "Dataset needs a clause text column such as clause_text."
                )

            tokens = preprocess_text(row[text_column])
            clause_vector = clause_to_vector(tokens, model)

        if clause_vector.shape[0] != query_vector.shape[1]:
            continue

        score = float(
            cosine_similarity(
                query_vector,
                clause_vector.reshape(1, -1)
            )[0][0]
        )

        results.append({
            "clause_id": str(row.get("clause_id", index)),
            "clause_text": str(
                row.get(
                    "clause_text",
                    row.get("text", row.get("clause", ""))
                )
            ),
            "similarity_score": round(score, 4)
        })

    results.sort(
        key=lambda item: item["similarity_score"],
        reverse=True
    )

    return results[:top_k]
