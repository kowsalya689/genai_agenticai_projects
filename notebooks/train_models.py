"""Train and compare SimpleRNN vs GRU vs LSTM next-word models.

Run in Colab / Jupyter / locally (GPU strongly recommended):

    python notebooks/train_models.py --data Articles.csv --out saved_models

Trains three architectures with IDENTICAL preprocessing, embedding size,
hidden size, and training schedule so the comparison is fair, then writes:

    saved_models/next_word_rnn_best.keras
    saved_models/next_word_gru_best.keras
    saved_models/next_word_lstm_best.keras
    saved_models/tokenizer.pkl          (shared by all three)
    saved_models/config.json            (shared preprocessing config)
    saved_models/comparison.json        (metrics table for the API / video)
    saved_models/comparison.csv
    saved_models/training_curves.png

The comparison table (accuracy, top-5 accuracy, perplexity, params, epoch
time) is printed at the end — this is the headline slide for the explanation
video.

Disclosure (per assessment brief NX-NLP-2026-014): uses TensorFlow/Keras,
NumPy, Pandas, Matplotlib. Corpus: Kaggle "Articles.csv" news dataset
(business/sports news articles).
"""

import argparse
import json
import pickle
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# Hyperparameters (identical across architectures for a fair comparison)
# ----------------------------------------------------------------------------
VOCAB_SIZE = 5000          # keep the 5k most frequent words; rest -> <OOV>
SEQ_CONTEXT = 15           # sliding-window context length (input tokens)
EMBEDDING_DIM = 200        # trainable embedding size (brief 4.2: no one-hot)
HIDDEN_UNITS = 256         # recurrent hidden state size
DROPOUT = 0.2
BATCH_SIZE = 256
EPOCHS = 30                # EarlyStopping usually halts well before this
PATIENCE = 3
MAX_ARTICLES = None        # set e.g. 800 for a fast smoke run
OOV_TOKEN = "<OOV>"
SEED = 42


def clean_text(text: str) -> str:
    """Mirror app/utils/text_cleaner.py: lowercase, strip bylines, keep words."""
    text = str(text).lower()
    text = re.sub(r"^[a-z ]+:\s*", "", text)          # strip "KARACHI: " bylines
    text = re.sub(r"[^a-z\s']", " ", text)            # keep letters + apostrophes
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_dataset(csv_path: str):
    """Load Articles.csv -> tokenizer + (X, y) sliding-window sequences."""
    from tensorflow.keras.preprocessing.text import Tokenizer
    from tensorflow.keras.preprocessing.sequence import pad_sequences

    df = pd.read_csv(csv_path, encoding="latin-1")
    articles = df["Article"].dropna().astype(str)
    if MAX_ARTICLES:
        articles = articles.iloc[:MAX_ARTICLES]
    corpus = [clean_text(a) for a in articles]
    print(f"[data] {len(corpus)} articles loaded")

    tokenizer = Tokenizer(num_words=VOCAB_SIZE, oov_token=OOV_TOKEN)
    tokenizer.fit_on_texts(corpus)
    vocab_size_eff = min(VOCAB_SIZE, len(tokenizer.word_index) + 1)
    print(f"[data] effective vocab size: {vocab_size_eff}")

    # Sliding window: every SEQ_CONTEXT tokens predict the next one.
    sequences = []
    for seq in tokenizer.texts_to_sequences(corpus):
        for i in range(SEQ_CONTEXT, len(seq)):
            sequences.append(seq[i - SEQ_CONTEXT: i + 1])
    sequences = np.array(sequences, dtype=np.int64)
    print(f"[data] {len(sequences):,} training sequences of length {SEQ_CONTEXT}+1")

    X, y = sequences[:, :-1], sequences[:, -1]
    return tokenizer, vocab_size_eff, X, y


def build_model(arch: str, vocab_size: int):
    """Same topology for all three; only the recurrent cell differs."""
    from tensorflow.keras import layers, models

    cell = {
        "rnn": layers.SimpleRNN,
        "gru": layers.GRU,
        "lstm": layers.LSTM,
    }[arch]

    model = models.Sequential(
        [
            layers.Embedding(vocab_size, EMBEDDING_DIM, input_length=SEQ_CONTEXT),
            cell(HIDDEN_UNITS, return_sequences=False),
            layers.Dropout(DROPOUT),
            layers.Dense(vocab_size, activation="softmax"),
        ],
        name=f"next_word_{arch}",
    )
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=[
            "accuracy",
            # top-5 accuracy: was the true next word in our top-5 candidates?
        ],
    )
    return model


def train_all(csv_path: str, out_dir: str):
    import tensorflow as tf
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

    tf.random.set_seed(SEED)
    np.random.seed(SEED)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    tokenizer, vocab_size_eff, X, y = build_dataset(csv_path)

    # 90/10 split (shuffled once, same split for every architecture)
    rng = np.random.default_rng(SEED)
    idx = rng.permutation(len(X))
    split = int(0.9 * len(X))
    tr, va = idx[:split], idx[split:]
    X_tr, y_tr, X_va, y_va = X[tr], y[tr], X[va], y[va]

    # Shared artifacts (identical preprocessing across all models)
    with open(out / "tokenizer.pkl", "wb") as f:
        pickle.dump(tokenizer, f)
    with open(out / "config.json", "w") as f:
        json.dump(
            {
                "context_length": SEQ_CONTEXT,
                "vocab_size": vocab_size_eff,
                "embedding_dim": EMBEDDING_DIM,
                "hidden_units": HIDDEN_UNITS,
                "seq_context": SEQ_CONTEXT,
                "oov_token": OOV_TOKEN,
            },
            f,
            indent=2,
        )

    results = {}
    histories = {}
    for arch in ("rnn", "gru", "lstm"):
        print(f"\n{'=' * 60}\n[train] {arch.upper()}\n{'=' * 60}")
        model = build_model(arch, vocab_size_eff)
        model.summary()
        ckpt_path = str(out / f"next_word_{arch}_best.keras")

        t0 = time.time()
        hist = model.fit(
            X_tr,
            y_tr,
            validation_data=(X_va, y_va),
            batch_size=BATCH_SIZE,
            epochs=EPOCHS,
            callbacks=[
                EarlyStopping(monitor="val_loss", patience=PATIENCE,
                              restore_best_weights=True),
                ModelCheckpoint(ckpt_path, monitor="val_loss",
                                save_best_only=True),
            ],
            verbose=1,
        )
        elapsed = time.time() - t0
        histories[arch] = hist.history

        # Evaluate best weights on validation split
        val_loss, val_acc = model.evaluate(X_va, y_va, batch_size=BATCH_SIZE,
                                           verbose=0)[:2]

        # Top-5 accuracy computed explicitly (architecture-agnostic)
        probs = model.predict(X_va, batch_size=BATCH_SIZE, verbose=0)
        top5 = np.argsort(probs, axis=1)[:, -5:]
        top5_acc = float(np.mean([y_va[i] in top5[i] for i in range(len(y_va))]))

        results[arch] = {
            "val_loss": round(float(val_loss), 4),
            "val_accuracy": round(float(val_acc), 4),
            "val_top5_accuracy": round(top5_acc, 4),
            "perplexity": round(float(np.exp(val_loss)), 2),
            "parameters": int(model.count_params()),
            "epochs_trained": len(hist.history["loss"]),
            "seconds_per_epoch": round(elapsed / len(hist.history["loss"]), 1),
        }
        print(f"[train] {arch}: {results[arch]}")

    # ---- Comparison table ---------------------------------------------------
    table = pd.DataFrame(results).T
    table.index.name = "model"
    table.to_csv(out / "comparison.csv")
    with open(out / "comparison.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 72)
    print("MODEL COMPARISON (validation set)")
    print("=" * 72)
    print(table.to_string())
    print("\nExpected pattern: LSTM/GRU clearly beat SimpleRNN on accuracy and")
    print("perplexity (gating mitigates vanishing gradients on 15-token")
    print("contexts); GRU trains fastest per epoch with ~25% fewer recurrent")
    print("params; LSTM typically edges out GRU on final perplexity.")

    # ---- Training curves ----------------------------------------------------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
        for arch, h in histories.items():
            axes[0].plot(h["val_loss"], label=f"{arch.upper()} val")
            axes[1].plot(h["val_accuracy"], label=f"{arch.upper()} val")
        axes[0].set_title("Validation loss"); axes[0].set_xlabel("epoch"); axes[0].legend()
        axes[1].set_title("Validation accuracy"); axes[1].set_xlabel("epoch"); axes[1].legend()
        fig.tight_layout()
        fig.savefig(out / "training_curves.png", dpi=150)
        print(f"\n[plot] saved {out / 'training_curves.png'}")
    except Exception as exc:  # matplotlib optional
        print(f"[plot] skipped: {exc}")

    print(f"\n[done] all artifacts in {out}/ — copy the folder into the web "
          f"app's saved_models/ directory.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default="Articles.csv", help="Path to Articles.csv")
    ap.add_argument("--out", default="saved_models", help="Output directory")
    args = ap.parse_args()
    train_all(args.data, args.out)
