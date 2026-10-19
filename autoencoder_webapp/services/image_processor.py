"""
Image preprocessing / postprocessing module.

Handles turning an uploaded file into a model-ready NumPy batch, and turning
a raw model output back into a displayable PNG image.
"""

from __future__ import annotations

import io
import logging
from typing import Tuple

import numpy as np
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "jfif"}


class ImageValidationError(Exception):
    """Raised when an uploaded file fails validation or cannot be decoded."""


def allowed_file(filename: str) -> bool:
    """Check the uploaded filename has a supported extension."""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def load_image_from_bytes(file_bytes: bytes) -> Image.Image:
    """
    Safely open an uploaded image using Pillow.

    Raises ImageValidationError if the bytes do not represent a valid,
    decodable image.
    """
    try:
        image = Image.open(io.BytesIO(file_bytes))
        image.verify()  # verify() checks integrity but leaves the file unusable afterward
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageValidationError("The uploaded file is not a valid image.") from exc

    # Re-open because verify() consumes the file pointer / renders it unusable.
    try:
        image = Image.open(io.BytesIO(file_bytes))
        image.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageValidationError("The uploaded image could not be decoded.") from exc

    return image


def preprocess_image(
    image: Image.Image,
    target_size: Tuple[int, int] = (28, 28),
    target_ndims: int = 4,
) -> Tuple[np.ndarray, Image.Image]:
    """
    Convert a PIL image into a model-ready NumPy batch.

    Steps: grayscale -> resize -> float32 -> normalize [0, 1] -> reshape to
    match the target dimensionality the model expects.

    Returns:
        (batch, grayscale_preview_image)
        - batch: NumPy array ready to feed to model.predict()
        - grayscale_preview_image: the resized 28x28 grayscale PIL image,
          useful for showing the user exactly what was fed to the model.
    """
    # Convert to grayscale ("L" mode = 8-bit single channel).
    grayscale = image.convert("L")

    # Resize to the model's expected spatial size.
    resized = grayscale.resize(target_size, Image.LANCZOS)

    # To NumPy, float32, normalized to [0, 1].
    array = np.asarray(resized, dtype=np.float32) / 255.0

    # Reshape to match the model's expected input rank.
    if target_ndims == 4:
        # (1, H, W, 1)
        batch = array.reshape(1, target_size[0], target_size[1], 1)
    elif target_ndims == 3:
        # (1, H, W)
        batch = array.reshape(1, target_size[0], target_size[1])
    elif target_ndims == 2:
        # (1, H*W) flattened
        batch = array.reshape(1, target_size[0] * target_size[1])
    else:
        # Fallback: default to channel-last 4D
        batch = array.reshape(1, target_size[0], target_size[1], 1)

    return batch, resized


def postprocess_output(output: np.ndarray, target_size: Tuple[int, int] = (28, 28)) -> Image.Image:
    """
    Convert the raw Autoencoder output back into a displayable grayscale
    PIL Image.

    Steps: remove batch dim -> remove channel dim if present -> reshape if
    flattened -> clip [0, 1] -> scale to [0, 255] -> uint8 -> PIL Image.
    """
    array = np.asarray(output, dtype=np.float32)

    # Remove batch dimension (first axis).
    if array.ndim >= 1 and array.shape[0] == 1:
        array = array[0]

    # If flattened (H*W,), reshape to (H, W).
    if array.ndim == 1:
        expected = target_size[0] * target_size[1]
        if array.shape[0] == expected:
            array = array.reshape(target_size[0], target_size[1])
        else:
            raise ValueError(f"Unexpected flattened output size: {array.shape[0]}")

    # Remove trailing channel dimension, e.g. (H, W, 1) -> (H, W).
    if array.ndim == 3 and array.shape[-1] == 1:
        array = array[:, :, 0]

    if array.ndim != 2:
        raise ValueError(f"Unexpected reconstructed output shape: {array.shape}")

    # Clip to valid normalized range, then scale to 0-255.
    array = np.clip(array, 0.0, 1.0)
    array = (array * 255.0).astype(np.uint8)

    return Image.fromarray(array, mode="L")


def image_to_png_bytes(image: Image.Image) -> bytes:
    """Encode a PIL image as PNG bytes."""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
