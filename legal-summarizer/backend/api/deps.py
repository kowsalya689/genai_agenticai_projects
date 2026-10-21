from fastapi import Request

from backend.config import Settings
from backend.core.errors import AppError


def get_app_settings(request: Request) -> Settings:
    """Settings the app was created with (so tests / overrides apply)."""
    return request.app.state.settings


def get_summarizer(request: Request):
    s = request.app.state.summarizer
    if not s.is_loaded:
        detail = getattr(s, "load_error", None)
        raise AppError(503, "model_unavailable", "The model is not ready yet." + (f" ({detail})" if detail else ""))
    return s
