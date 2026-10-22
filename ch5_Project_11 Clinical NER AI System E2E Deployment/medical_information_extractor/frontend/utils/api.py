"""
utils/api.py
------------
Thin, defensive client for the existing FastAPI backend.

This module is the ONLY place in the frontend that talks to the backend.
It never mutates or mocks data — it simply forwards the uploaded PDF to the
existing `POST /extract` endpoint and returns the JSON exactly as the backend
produced it.

Endpoints used (unchanged from backend):
    GET  /          -> health check ({"message": "..."} )
    POST /extract   -> multipart file upload, returns {summary, entities, tables}
"""

from __future__ import annotations

import os
import requests


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# The backend URL can be overridden with the FASTAPI_URL environment variable
# or from the sidebar at runtime. Default assumes the FastAPI app is running
# locally on port 8000 (uvicorn app:app --reload).
DEFAULT_BASE_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

# Hard limit enforced client-side to give a friendly message before uploading.
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Network timeouts (seconds): (connect, read). NLP extraction can be slow,
# so the read timeout is generous.
HEALTH_TIMEOUT = (3, 5)
EXTRACT_TIMEOUT = (5, 120)


# ---------------------------------------------------------------------------
# Typed errors — let the UI show a friendly, specific message per failure mode.
# ---------------------------------------------------------------------------
class BackendError(Exception):
    """Base class for all backend-related failures."""


class BackendConnectionError(BackendError):
    """Backend unreachable — server down, wrong URL, or no network."""


class BackendTimeoutError(BackendError):
    """Backend accepted the request but took too long to respond."""


class FileTooLargeError(BackendError):
    """Uploaded file exceeds the configured size limit."""


class APIResponseError(BackendError):
    """Backend responded with a non-200 status or an unparseable body."""


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------
def check_backend_status(base_url: str = DEFAULT_BASE_URL) -> tuple[bool, str]:
    """
    Ping the backend health endpoint.

    Returns:
        (is_online, human_readable_message)
    """
    url = base_url.rstrip("/") + "/"
    try:
        response = requests.get(url, timeout=HEALTH_TIMEOUT)
        if response.status_code == 200:
            return True, "Connected"
        return False, f"Unexpected status {response.status_code}"
    except requests.exceptions.ConnectTimeout:
        return False, "Connection timed out"
    except requests.exceptions.ConnectionError:
        return False, "Unreachable"
    except requests.exceptions.RequestException as exc:  # pragma: no cover
        return False, f"Error: {exc}"


def extract_information(
    file_bytes: bytes,
    filename: str,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    """
    Send a PDF to the backend's /extract endpoint and return the parsed JSON.

    Args:
        file_bytes: raw bytes of the uploaded PDF.
        filename:   original filename (backend saves under this name).
        base_url:   backend base URL.

    Returns:
        The backend's JSON response as a dict: {summary, entities, tables}.

    Raises:
        FileTooLargeError, BackendConnectionError, BackendTimeoutError,
        APIResponseError.
    """
    # ---- Client-side guard rails -------------------------------------------
    if not file_bytes:
        raise APIResponseError("The uploaded file appears to be empty.")

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        size_mb = len(file_bytes) / (1024 * 1024)
        raise FileTooLargeError(
            f"File is {size_mb:.1f} MB, which exceeds the {MAX_FILE_SIZE_MB} MB limit."
        )

    url = base_url.rstrip("/") + "/extract"
    files = {"file": (filename, file_bytes, "application/pdf")}

    # ---- Network call ------------------------------------------------------
    try:
        response = requests.post(url, files=files, timeout=EXTRACT_TIMEOUT)
    except requests.exceptions.ConnectTimeout as exc:
        raise BackendConnectionError(
            "Could not reach the backend (connection timed out)."
        ) from exc
    except requests.exceptions.ReadTimeout as exc:
        raise BackendTimeoutError(
            "The backend took too long to respond. The document may be very large."
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise BackendConnectionError(
            "The backend is not reachable. Is the FastAPI server running?"
        ) from exc
    except requests.exceptions.RequestException as exc:  # pragma: no cover
        raise BackendError(f"Unexpected network error: {exc}") from exc

    # ---- Status handling ---------------------------------------------------
    if response.status_code != 200:
        detail = _safe_error_detail(response)
        raise APIResponseError(
            f"Backend returned status {response.status_code}. {detail}"
        )

    # ---- Parse body --------------------------------------------------------
    try:
        return response.json()
    except ValueError as exc:
        raise APIResponseError(
            "The backend response could not be parsed as JSON."
        ) from exc


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------
def _safe_error_detail(response: requests.Response) -> str:
    """Best-effort extraction of an error message from a failed response."""
    try:
        payload = response.json()
        if isinstance(payload, dict) and "detail" in payload:
            return str(payload["detail"])
    except ValueError:
        pass
    text = (response.text or "").strip()
    return text[:200] if text else "No further detail provided."
