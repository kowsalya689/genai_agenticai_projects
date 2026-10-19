"""Health-check route: GET /health.

Reports whether the default model + tokenizer are loaded, which architectures
have artifacts on disk, plus the effective context length and vocabulary size.
Never raises — a failed load is reported as ``model_loaded: false`` so
orchestrators can still scrape the endpoint.
"""

from fastapi import APIRouter

from app.models.model_loader import available_models, get_bundle
from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Service health and model status")
def health() -> HealthResponse:
    try:
        bundle = get_bundle()
        return HealthResponse(
            status="ok",
            model_loaded=True,
            available_models=available_models(),
            context_length=bundle.context_length,
            vocab_size=len(bundle.word_index) + 1,
        )
    except Exception as exc:  # noqa: BLE001 - deliberately broad; health must not throw
        return HealthResponse(
            status=f"degraded: {exc}",
            model_loaded=False,
            available_models=available_models(),
            context_length=0,
            vocab_size=0,
        )
