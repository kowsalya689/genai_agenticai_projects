# saved_models/

Place your **trained artifacts** here (they are not committed to git):

| File | How it is produced |
|------|--------------------|
| `next_word_lstm_best.keras` | Saved by `ModelCheckpoint` during notebook training. |
| `tokenizer.pkl` | `pickle.dump(tokenizer, ...)` — see `notebooks/export_artifacts.py`. |
| `config.json` *(optional)* | Written by `notebooks/export_artifacts.py`; stores `context_length`. |

If `config.json` is absent, the app infers the context length from the model's
input shape. Override any path with the `MODEL_PATH` / `TOKENIZER_PATH` /
`CONFIG_PATH` environment variables.
