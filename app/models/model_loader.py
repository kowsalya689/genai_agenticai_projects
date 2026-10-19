"""Model + tokenizer loading (multi-architecture).

Loads trained ``.keras`` models (LSTM / GRU / SimpleRNN), the pickled
tokenizer, and (optionally) a ``config.json`` describing the training-time
context length. The tokenizer and config are SHARED across architectures
because every model is trained on the same corpus with identical
preprocessing.

Each architecture's bundle is loaded **once** and cached in a process-wide
registry so repeated requests never reload from disk. Models are never
retrained here. TensorFlow is imported lazily so importing this module (and
the FastAPI app) does not require TensorFlow until a model is actually loaded.
"""

import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config.settings import settings
from app.models.tokenizer_loader import load_tokenizer


class ModelBundle:
    """Container for all runtime artifacts needed for inference."""

    def __init__(self, model: Any, tokenizer: Any, context_length: int,
                 config: Dict[str, Any], arch: str = "lstm"):
        self.model = model
        self.tokenizer = tokenizer
        self.word_index = tokenizer.word_index
        self.index_word = tokenizer.index_word
        self.context_length = context_length
        self.config = config
        self.arch = arch


_bundles: Dict[str, ModelBundle] = {}
_shared: Dict[str, Any] = {}  # cached tokenizer + config, loaded once
_lock = threading.Lock()


def _infer_context_length(model: Any, fallback: int) -> int:
    """Read the context window width from the model's input shape.

    Returns ``fallback`` if the shape cannot be determined.
    """
    try:
        shape = model.input_shape
        if isinstance(shape, list):  # multi-input models return a list
            shape = shape[0]
        if shape and shape[-1]:
            return int(shape[-1])
    except Exception:  # pragma: no cover - defensive
        pass
    return fallback


def available_models() -> List[str]:
    """Architectures whose trained artifact file exists on disk.

    Order follows ``settings.SUPPORTED_ARCHS`` (lstm first).
    """
    return [
        arch for arch in settings.SUPPORTED_ARCHS
        if Path(settings.model_path_for(arch)).exists()
    ]


def _load_shared() -> Dict[str, Any]:
    """Load (once) the tokenizer + config shared by all architectures."""
    if _shared:
        return _shared

    tokenizer_path = settings.TOKENIZER_PATH
    if not Path(tokenizer_path).exists():
        raise FileNotFoundError(
            f"Tokenizer file not found at {tokenizer_path}. Export it from "
            f"the training script with pickle.dump(tokenizer, ...) as "
            f"'tokenizer.pkl'."
        )
    _shared["tokenizer"] = load_tokenizer(tokenizer_path)

    config: Dict[str, Any] = {}
    if Path(settings.CONFIG_PATH).exists():
        with open(settings.CONFIG_PATH) as f:
            config = json.load(f)
    _shared["config"] = config
    return _shared


def load_bundle(arch: Optional[str] = None, force: bool = False) -> ModelBundle:
    """Load (and cache) the model bundle for ``arch``.

    Args:
        arch: One of ``settings.SUPPORTED_ARCHS``. Defaults to
            ``settings.DEFAULT_ARCH`` (lstm).
        force: Reload from disk even if a bundle is already cached.

    Returns:
        The cached :class:`ModelBundle` for that architecture.
    """
    arch = (arch or settings.DEFAULT_ARCH).lower()
    if arch not in settings.SUPPORTED_ARCHS:
        raise ValueError(
            f"Unknown model architecture '{arch}'. "
            f"Supported: {', '.join(settings.SUPPORTED_ARCHS)}."
        )

    if arch in _bundles and not force:
        return _bundles[arch]

    with _lock:
        if arch in _bundles and not force:
            return _bundles[arch]

        # Lazy import: TensorFlow is only needed when actually loading a model.
        import tensorflow as tf  # noqa: WPS433 (intentional local import)

        model_path = settings.model_path_for(arch)
        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"Model file not found at {model_path}. Train it with "
                f"notebooks/train_models.py and place "
                f"'next_word_{arch}_best.keras' in saved_models/ (see README)."
            )

        shared = _load_shared()
        try:
            model = tf.keras.models.load_model(model_path)
        except Exception as exc:  # noqa: BLE001
            # The most common failure here is a Keras version mismatch: the
            # .keras artifact was saved with a NEWER Keras than the one
            # installed at serving time, so deserialization fails. Surface a
            # clear, actionable message instead of a raw TypeError.
            import keras  # local import; TF has already been imported above

            raise RuntimeError(
                f"Failed to load model '{arch}' from {model_path}. This is "
                f"almost always a Keras version mismatch. Installed Keras is "
                f"{keras.__version__}; the artifacts in saved_models/ were "
                f"exported with Keras 3.13.2. Reinstall dependencies with the "
                f"pinned versions: `pip install -r requirements.txt` "
                f"(tensorflow==2.16.1 + keras==3.13.2). Original error: {exc}"
            ) from exc
        config = shared["config"]

        context_length = int(
            config.get("context_length")
            or _infer_context_length(model, settings.CONTEXT_LENGTH)
        )

        _bundles[arch] = ModelBundle(
            model, shared["tokenizer"], context_length, config, arch=arch
        )
        return _bundles[arch]


def get_bundle(arch: Optional[str] = None) -> ModelBundle:
    """Return the cached bundle for ``arch``, loading it on first use."""
    return load_bundle(arch)
