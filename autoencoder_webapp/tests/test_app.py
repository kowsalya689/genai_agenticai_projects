"""
Basic tests for the Autoencoder web application.

Run with:
    pytest tests/

Note: these tests exercise the Flask routes, request validation, and image
processing helpers. They do not require a real trained model to be present
for most cases (routes correctly report 503 when no model is loaded), but
having a valid model in models/ will let the full /api/reconstruct happy
path run end-to-end.
"""

import io
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from PIL import Image

from app import create_app
from services.image_processor import (
    allowed_file,
    postprocess_output,
    preprocess_image,
)


@pytest.fixture()
def app():
    flask_app = create_app()
    flask_app.config.update({"TESTING": True})
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


def make_test_image_bytes(size=(64, 64), color="white", fmt="PNG"):
    image = Image.new("RGB", size, color=color)
    buffer = io.BytesIO()
    image.save(buffer, format=fmt)
    buffer.seek(0)
    return buffer


# --------------------------------------------------------------------------
# Route tests
# --------------------------------------------------------------------------

def test_index_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"MNIST Autoencoder" in response.data


def test_health_endpoint_returns_json(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert "success" in data
    assert "model_loaded" in data


def test_reconstruct_without_file_returns_400(client):
    response = client.post("/api/reconstruct", data={})
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False


def test_reconstruct_with_invalid_extension_returns_400(client):
    file_bytes = make_test_image_bytes()
    response = client.post(
        "/api/reconstruct",
        data={"image": (file_bytes, "test.txt")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400


def test_reconstruct_with_valid_image(client, app):
    """
    If a model is loaded, this should succeed end-to-end. If no model is
    present in models/, the API correctly reports 503 rather than crashing.
    """
    from services.model_manager import model_manager

    file_bytes = make_test_image_bytes()
    response = client.post(
        "/api/reconstruct",
        data={"image": (file_bytes, "test.png")},
        content_type="multipart/form-data",
    )

    if model_manager.is_loaded:
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "original_image" in data
        assert "reconstructed_image" in data
    else:
        assert response.status_code == 503


# --------------------------------------------------------------------------
# Image processor unit tests
# --------------------------------------------------------------------------

def test_allowed_file_accepts_supported_extensions():
    assert allowed_file("digit.png")
    assert allowed_file("digit.JPG")
    assert allowed_file("digit.jfif")


def test_allowed_file_rejects_unsupported_extensions():
    assert not allowed_file("digit.txt")
    assert not allowed_file("digit")
    assert not allowed_file("")


def test_preprocess_image_produces_expected_shape():
    image = Image.new("L", (100, 100), color=128)
    batch, preview = preprocess_image(image, target_size=(28, 28), target_ndims=4)
    assert batch.shape == (1, 28, 28, 1)
    assert batch.dtype.name == "float32"
    assert batch.max() <= 1.0
    assert batch.min() >= 0.0
    assert preview.size == (28, 28)


def test_postprocess_output_handles_channel_dimension():
    import numpy as np

    fake_output = np.random.rand(1, 28, 28, 1).astype("float32")
    image = postprocess_output(fake_output, target_size=(28, 28))
    assert image.size == (28, 28)
    assert image.mode == "L"


def test_postprocess_output_handles_flattened_output():
    import numpy as np

    fake_output = np.random.rand(1, 784).astype("float32")
    image = postprocess_output(fake_output, target_size=(28, 28))
    assert image.size == (28, 28)
