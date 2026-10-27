"""
Central settings for the app.

Everything you might want to change lives here, so you don't have to hunt
through the code. You can also override any value with an environment variable.
"""
import os
from pathlib import Path

# Project root folder (the folder that contains this "app" package).
BASE_DIR = Path(__file__).resolve().parent.parent

# Folder that holds the trained model files. After you unzip
# fake_news_model.zip inside the project folder you will have:
#   fake_news_app/fake_news_model/config.json
#   fake_news_app/fake_news_model/model.safetensors
#   fake_news_app/fake_news_model/tokenizer.json
#   fake_news_app/fake_news_model/tokenizer_config.json
#   fake_news_app/fake_news_model/label_map.json
# Override with:  set MODEL_DIR=...   (Windows)  /  export MODEL_DIR=...  (Mac/Linux)
MODEL_DIR = os.environ.get("MODEL_DIR", str(BASE_DIR / "fake_news_model"))

# Maximum number of tokens the model reads from one article.
# MUST match the value used during training in the Colab notebook (256).
MAX_LEN = int(os.environ.get("MAX_LEN", "256"))

# Web server address.
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))
