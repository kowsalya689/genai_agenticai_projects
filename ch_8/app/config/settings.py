"""Application configuration.

All values can be overridden with environment variables, which makes the app
portable across local development, Docker, and PaaS hosts (Render / Railway)
without code changes. Defaults mirror the training notebook so that the
inference pipeline reproduces training-time preprocessing exactly.

Multi-model support: the app can serve several trained architectures
(SimpleRNN / GRU / LSTM) side by side. Each architecture's artifact follows the
naming pattern ``next_word_{arch}_best.keras`` inside ``saved_models/``. The
tokenizer and config.json are SHARED across architectures because all models
are trained on the same corpus with the same preprocessing.
"""

import os
from pathlib import Path

# Project root: .../next_word_predictor/  (this file is app/config/settings.py)
BASE_DIR = Path(__file__).resolve().parents[2]
SAVED_MODELS_DIR = BASE_DIR / "saved_models"


class Settings:
    # --- App metadata -------------------------------------------------------
    APP_NAME: str = os.getenv("APP_NAME", "Next Word Prediction API")
    VERSION: str = "2.0.0"

    # --- Model / preprocessing config (mirrors the training notebook) -------
    VOCAB_SIZE: int = int(os.getenv("VOCAB_SIZE", "5000"))
    SEQ_CONTEXT: int = int(os.getenv("SEQ_CONTEXT", "15"))
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "200"))
    OOV_TOKEN: str = os.getenv("OOV_TOKEN", "<OOV>")

    # Width of the model's input (context window). This is normally read from
    # the model's own input shape at load time; this value is only a fallback.
    CONTEXT_LENGTH: int = int(os.getenv("CONTEXT_LENGTH", "15"))

    # --- Multi-model registry ----------------------------------------------
    # Known architectures the app can serve. Only those whose artifact file
    # actually exists in saved_models/ are exposed at runtime (see
    # model_loader.available_models()).
    SUPPORTED_ARCHS: tuple = ("lstm", "gru", "rnn")
    DEFAULT_ARCH: str = os.getenv("DEFAULT_ARCH", "lstm")

    @staticmethod
    def model_path_for(arch: str) -> str:
        """Artifact path for a given architecture, env-overridable per arch.

        Env override example: ``MODEL_PATH_GRU=/models/my_gru.keras``.
        """
        env_key = f"MODEL_PATH_{arch.upper()}"
        return os.getenv(
            env_key, str(SAVED_MODELS_DIR / f"next_word_{arch}_best.keras")
        )

    # --- Artifact paths (tokenizer/config shared by all architectures) ------
    # Backward-compat: MODEL_PATH still points at the default (LSTM) artifact.
    MODEL_PATH: str = os.getenv(
        "MODEL_PATH", str(SAVED_MODELS_DIR / "next_word_lstm_best.keras")
    )
    TOKENIZER_PATH: str = os.getenv(
        "TOKENIZER_PATH", str(SAVED_MODELS_DIR / "tokenizer.pkl")
    )
    CONFIG_PATH: str = os.getenv(
        "CONFIG_PATH", str(SAVED_MODELS_DIR / "config.json")
    )
    COMPARISON_PATH: str = os.getenv(
        "COMPARISON_PATH", str(SAVED_MODELS_DIR / "comparison.json")
    )

    # --- Generation defaults / guard rails ----------------------------------
    DEFAULT_TOP_K: int = 5
    DEFAULT_NUM_WORDS: int = 12
    DEFAULT_TEMPERATURE: float = 0.8
    MAX_TOP_K: int = 20
    MAX_NUM_WORDS: int = 50
    MAX_TEMPERATURE: float = 2.0


settings = Settings()
