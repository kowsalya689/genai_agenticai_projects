"""
API routes for the Autoencoder web application.

Endpoints:
    GET  /                    -> render the main SPA-style page
    GET  /api/health          -> server + model status
    POST /api/reconstruct     -> run an uploaded image through the Autoencoder
"""

from __future__ import annotations

import base64
import logging

from flask import Blueprint, current_app, jsonify, render_template, request

from services.image_processor import (
    ImageValidationError,
    allowed_file,
    image_to_png_bytes,
    load_image_from_bytes,
    postprocess_output,
    preprocess_image,
)
from services.model_manager import model_manager

logger = logging.getLogger(__name__)

bp = Blueprint("api", __name__)


# --------------------------------------------------------------------------
# Page routes
# --------------------------------------------------------------------------

@bp.route("/", methods=["GET"])
def index():
    """Render the main application page."""
    return render_template("index.html", model_loaded=model_manager.is_loaded)


# --------------------------------------------------------------------------
# API routes
# --------------------------------------------------------------------------

@bp.route("/api/health", methods=["GET"])
def health():
    """Report server liveness and current model status."""
    payload = {
        "success": True,
        "status": "ok",
        "model_loaded": model_manager.is_loaded,
    }

    if model_manager.is_loaded and model_manager.info is not None:
        payload["model"] = {
            "filename": model_manager.info.filename,
            "input_shape": _shape_to_list(model_manager.info.input_shape),
            "output_shape": _shape_to_list(model_manager.info.output_shape),
        }
    else:
        payload["model_error"] = model_manager.load_error or "Model not loaded."

    return jsonify(payload), 200


@bp.route("/api/reconstruct", methods=["POST"])
def reconstruct():
    """
    Accept an uploaded image, preprocess it, run it through the Autoencoder,
    and return both the original preview and the reconstructed image as
    base64-encoded PNGs.
    """
    if "image" not in request.files:
        return _error_response("No image file was provided.", 400)

    file = request.files["image"]

    if file.filename == "":
        return _error_response("No file was selected.", 400)

    if not allowed_file(file.filename):
        return _error_response(
            "Unsupported file type. Please upload a PNG, JPG, JPEG, WEBP, or JFIF image.",
            400,
        )

    file_bytes = file.read()
    if not file_bytes:
        return _error_response("The uploaded file is empty.", 400)

    if not model_manager.is_loaded:
        return _error_response(
            "The Autoencoder model is not currently available. Please try again later.",
            503,
        )

    try:
        original_image = load_image_from_bytes(file_bytes)
    except ImageValidationError as exc:
        return _error_response(str(exc), 400)

    try:
        target_size = _resolve_target_size()
        target_ndims = _resolve_target_ndims()

        batch, preview_28x28 = preprocess_image(
            original_image, target_size=target_size, target_ndims=target_ndims
        )

        raw_output = model_manager.predict(batch)
        reconstructed_image = postprocess_output(raw_output, target_size=target_size)
    except ValueError as exc:
        logger.error("Preprocessing/postprocessing error: %s", exc)
        return _error_response(
            "The image could not be processed by the model. Please try a different image.",
            422,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error during reconstruction: %s", exc)
        return _error_response(
            "Something went wrong while reconstructing the image. Please try again.",
            500,
        )

    original_thumb = original_image.convert("L").resize(target_size)

    response = {
        "success": True,
        "original_image": _to_base64_png(original_thumb),
        "reconstructed_image": _to_base64_png(reconstructed_image),
        "dimensions": {"width": target_size[0], "height": target_size[1]},
    }
    return jsonify(response), 200


# --------------------------------------------------------------------------
# Error handlers (registered on the blueprint's parent app in app.py)
# --------------------------------------------------------------------------

def register_error_handlers(app):
    """Attach JSON error handlers for common HTTP errors."""

    @app.errorhandler(413)
    def handle_payload_too_large(_e):
        return _error_response("The uploaded file is too large.", 413)

    @app.errorhandler(404)
    def handle_not_found(_e):
        if request.path.startswith("/api/"):
            return _error_response("The requested endpoint was not found.", 404)
        return render_template("index.html", model_loaded=model_manager.is_loaded), 404

    @app.errorhandler(500)
    def handle_internal_error(e):
        logger.exception("Unhandled server error: %s", e)
        return _error_response("An unexpected server error occurred.", 500)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _error_response(message: str, status_code: int):
    return jsonify({"success": False, "error": message}), status_code


def _to_base64_png(image) -> str:
    png_bytes = image_to_png_bytes(image)
    encoded = base64.b64encode(png_bytes).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def _shape_to_list(shape):
    if isinstance(shape, list):
        return [list(s) for s in shape]
    return list(shape)


def _resolve_target_size():
    expected = model_manager.get_expected_input_shape()
    dims = [d for d in expected if d is not None]
    if len(dims) >= 2 and 28 in dims:
        return (28, 28)
    if len(dims) == 1 and dims[0] == 784:
        return (28, 28)
    return current_app.config.get("DEFAULT_IMAGE_SIZE", (28, 28))


def _resolve_target_ndims():
    expected = model_manager.get_expected_input_shape()
    # expected excludes batch dim already, so add 1 for the batch axis
    # to determine the full rank the model expects.
    return len(expected) + 1 if expected else 4
