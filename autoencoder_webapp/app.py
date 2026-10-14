"""
Application entry point.

Creates the Flask app, configures logging, loads the trained Autoencoder
model exactly once, and registers routes.

Run with:
    python app.py
"""

from __future__ import annotations

import logging

from flask import Flask

from config import get_config
from routes.api import bp as api_blueprint, register_error_handlers
from services.model_manager import model_manager


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def create_app() -> Flask:
    config_cls = get_config()

    app = Flask(__name__)
    app.config.from_object(config_cls)

    configure_logging(config_cls.LOG_LEVEL)
    logger = logging.getLogger(__name__)

    # Configure the shared model manager singleton and load the model once.
    model_manager.models_dir = config_cls.MODELS_DIR
    model_manager.supported_extensions = config_cls.SUPPORTED_MODEL_EXTENSIONS
    model_manager.preferred_filename = config_cls.MODEL_FILENAME
    model_manager.load()

    if model_manager.is_loaded:
        logger.info("Autoencoder model ready for inference.")
    else:
        logger.warning(
            "Autoencoder model failed to load: %s. The app will run, but "
            "/api/reconstruct will return 503 until a valid model is placed "
            "in the models/ directory and the server is restarted.",
            model_manager.load_error,
        )

    app.register_blueprint(api_blueprint)
    register_error_handlers(app)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", False))
