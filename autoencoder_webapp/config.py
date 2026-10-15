"""
Central configuration for the Autoencoder web application.

All tunable settings live here so the rest of the codebase never hardcodes
paths, limits, or magic numbers.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration shared by every environment."""

    # --- Paths -----------------------------------------------------------
    BASE_DIR = BASE_DIR
    MODELS_DIR = os.path.join(BASE_DIR, "models")

    # --- Model -------------------------------------------------------------
    # Extensions (in priority order) that the model manager will search for
    # inside MODELS_DIR when a specific filename isn't given.
    SUPPORTED_MODEL_EXTENSIONS = (".keras", ".h5")

    # Optional: force a specific model filename (inside MODELS_DIR).
    # Leave as None to auto-discover the first supported model file found.
    MODEL_FILENAME = os.environ.get("MODEL_FILENAME", None)

    # Fallback input size used only if the model's input shape cannot be
    # introspected for some reason.
    DEFAULT_IMAGE_SIZE = (28, 28)

    # --- Uploads -----------------------------------------------------------
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB max upload size
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "jfif"}

    # --- Flask ---------------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    JSON_SORT_KEYS = False

    # --- Logging -----------------------------------------------------------
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)
