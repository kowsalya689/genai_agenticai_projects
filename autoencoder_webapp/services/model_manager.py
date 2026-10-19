"""
Model manager service.

Responsible for discovering, loading, and holding the trained Autoencoder
model in memory. The model is loaded exactly once (on application startup)
and reused for every inference request via a module-level singleton.

This module NEVER trains or fits the model - it only loads an existing
trained model and calls `.predict()` on it.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class ModelLoadError(Exception):
    """Raised when the model cannot be found or loaded."""


@dataclass
class ModelInfo:
    """Small metadata bundle describing the currently loaded model."""

    filename: str
    path: str
    input_shape: Tuple
    output_shape: Tuple


class ModelManager:
    """
    Loads a trained Keras Autoencoder from disk and serves predictions.

    Usage:
        manager = ModelManager(models_dir, supported_extensions)
        manager.load()
        reconstructed = manager.predict(preprocessed_batch)
    """

    def __init__(
        self,
        models_dir: str,
        supported_extensions: Tuple[str, ...] = (".keras", ".h5"),
        preferred_filename: Optional[str] = None,
    ) -> None:
        self.models_dir = models_dir
        self.supported_extensions = supported_extensions
        self.preferred_filename = preferred_filename

        self._model = None
        self._info: Optional[ModelInfo] = None
        self._load_error: Optional[str] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def info(self) -> Optional[ModelInfo]:
        return self._info

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def load(self) -> None:
        """
        Discover and load the trained model from `models_dir`.

        Any failure is captured internally (and logged in full) rather than
        raised, so the Flask app can start up and report a friendly status
        via /api/health instead of crashing outright. Routes that require
        an active model should check `is_loaded` first.
        """
        try:
            model_path = self._resolve_model_path()
            logger.info("Loading Autoencoder model from: %s", model_path)

            # Imported lazily so the rest of the app can start even if
            # TensorFlow itself is slow to import or briefly unavailable.
            from tensorflow import keras

            model = keras.models.load_model(model_path, compile=False)

            input_shape = model.input_shape
            output_shape = model.output_shape

            self._validate_shape_is_mnist_like(input_shape)

            self._model = model
            self._info = ModelInfo(
                filename=os.path.basename(model_path),
                path=model_path,
                input_shape=input_shape,
                output_shape=output_shape,
            )
            self._load_error = None
            logger.info(
                "Model loaded successfully. input_shape=%s output_shape=%s",
                input_shape,
                output_shape,
            )
        except ModelLoadError as exc:
            self._model = None
            self._info = None
            self._load_error = str(exc)
            logger.error("Model load error: %s", exc)
        except Exception as exc:  # noqa: BLE001 - we want to catch everything here
            self._model = None
            self._info = None
            self._load_error = "The trained model could not be loaded. Please contact the administrator."
            logger.exception("Unexpected error while loading model: %s", exc)

    def predict(self, batch: np.ndarray) -> np.ndarray:
        """
        Run inference on a preprocessed batch and return the raw model
        output. Raises RuntimeError if no model is currently loaded.
        """
        if not self.is_loaded:
            raise RuntimeError("Model is not loaded. Cannot run inference.")
        return self._model.predict(batch, verbose=0)

    def get_expected_input_shape(self) -> Tuple:
        """
        Return the model's expected input shape (excluding batch dimension)
        if known, otherwise an empty tuple.
        """
        if self._info is None:
            return ()
        shape = self._info.input_shape
        if isinstance(shape, list):  # multi-input models (unlikely here)
            shape = shape[0]
        return tuple(shape[1:]) if shape else ()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_model_path(self) -> str:
        if not os.path.isdir(self.models_dir):
            raise ModelLoadError(
                f"The models directory was not found. Expected it at: {self.models_dir}"
            )

        if self.preferred_filename:
            candidate = os.path.join(self.models_dir, self.preferred_filename)
            if os.path.isfile(candidate):
                return candidate
            raise ModelLoadError(
                f"Configured model file '{self.preferred_filename}' was not found "
                f"in {self.models_dir}."
            )

        # Auto-discover: search directory for the first matching supported file.
        candidates = sorted(os.listdir(self.models_dir))
        for filename in candidates:
            if filename.lower().endswith(self.supported_extensions):
                return os.path.join(self.models_dir, filename)

        raise ModelLoadError(
            "No trained model file was found in the models/ directory. "
            f"Supported formats: {', '.join(self.supported_extensions)}. "
            "Please place your trained Autoencoder there."
        )

    @staticmethod
    def _validate_shape_is_mnist_like(input_shape) -> None:
        """
        Sanity-check that the loaded model's input is compatible with
        28x28 (optionally single-channel) grayscale images. This does not
        block loading models with a flattened (None, 784) input, since that
        is also a common, valid Autoencoder input shape.
        """
        if isinstance(input_shape, list):
            input_shape = input_shape[0]

        dims = [d for d in input_shape if d is not None]

        # Accept: (28, 28), (28, 28, 1), or flattened (784,)
        is_2d_or_3d = len(dims) in (2, 3) and 28 in dims
        is_flat = len(dims) == 1 and dims[0] == 784

        if not (is_2d_or_3d or is_flat):
            raise ModelLoadError(
                "The loaded model's input shape "
                f"{input_shape} does not look compatible with 28x28 "
                "grayscale MNIST-style images. Please provide a matching "
                "Autoencoder model."
            )


# ---------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------
# A single shared instance is created here and configured/loaded once from
# app.py at startup, then imported by routes so the model is never reloaded
# per-request.
model_manager = ModelManager(models_dir=os.path.join(os.path.dirname(os.path.dirname(__file__)), "models"))
