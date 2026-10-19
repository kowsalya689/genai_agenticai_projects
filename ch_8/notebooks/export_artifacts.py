"""Export trained artifacts for serving.

PREFERRED PATH: run ``notebooks/train_models.py`` — it trains all three
architectures (SimpleRNN / GRU / LSTM) and writes every artifact the web app
needs directly into ``saved_models/``:

    next_word_rnn_best.keras
    next_word_gru_best.keras
    next_word_lstm_best.keras
    tokenizer.pkl        (shared)
    config.json          (shared)
    comparison.json / comparison.csv / training_curves.png

MANUAL PATH: if you trained a single model in your own notebook, paste the
block below into a cell after training (variables ``model``, ``tokenizer``,
``context_length`` must exist), then drop the files into saved_models/.
"""

# --- Paste the block below into a notebook cell after training --------------
"""
import os, json, pickle

os.makedirs("saved_models", exist_ok=True)

# 1) Model — name it after its architecture (lstm / gru / rnn):
model.save("saved_models/next_word_lstm_best.keras")

# 2) Tokenizer — pickle the fitted Keras Tokenizer (shared by all archs):
with open("saved_models/tokenizer.pkl", "wb") as f:
    pickle.dump(tokenizer, f)

# 3) Config — persist the context length + key hyperparameters so the API
#    reproduces training-time preprocessing exactly:
config = {
    "context_length": int(context_length),   # X.shape[1] from the notebook
    "vocab_size": int(VOCAB_SIZE_EFF),
    "embedding_dim": int(EMBEDDING_DIM),
    "seq_context": int(SEQ_CONTEXT),
    "oov_token": "<OOV>",
}
with open("saved_models/config.json", "w") as f:
    json.dump(config, f, indent=2)

print("Saved artifacts to saved_models/")

# In Colab, download them:
# from google.colab import files
# for fn in ["next_word_lstm_best.keras", "tokenizer.pkl", "config.json"]:
#     files.download(f"saved_models/{fn}")
"""
