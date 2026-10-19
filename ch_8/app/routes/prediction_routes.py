"""Prediction API routes: POST /predict, POST /generate, GET /models."""

from typing import Optional

from fastapi import APIRouter, HTTPException

from app.config.settings import settings
from app.models.model_loader import available_models, get_bundle
from app.models.schemas import (
    GenerateRequest,
    GenerateResponse,
    ModelInfo,
    ModelsResponse,
    Prediction,
    PredictRequest,
    PredictResponse,
)
from app.services.predictor import PredictorService

router = APIRouter(tags=["prediction"])


def get_predictor(arch: Optional[str] = None) -> PredictorService:
    """Build a predictor around the cached bundle for ``arch``.

    Kept as a plain function (called per-request with the requested
    architecture) and still overridable in tests via
    ``app.dependency_overrides``.
    """
    try:
        return PredictorService(get_bundle(arch))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _resolve_predictor(arch: Optional[str]) -> PredictorService:
    """Honour test overrides on ``get_predictor``, else load the real bundle."""
    from app.main import app  # local import to avoid a circular import at module load

    override = app.dependency_overrides.get(get_predictor)
    if override is not None:
        return override()
    return get_predictor(arch)


@router.get("/models", response_model=ModelsResponse, summary="List available model architectures")
def list_models() -> ModelsResponse:
    on_disk = available_models()
    return ModelsResponse(
        models=[
            ModelInfo(
                name=arch,
                loaded=arch in on_disk,
                default=(arch == settings.DEFAULT_ARCH),
            )
            for arch in settings.SUPPORTED_ARCHS
        ],
        default=settings.DEFAULT_ARCH,
    )


@router.post("/predict", response_model=PredictResponse, summary="Predict the next word")
def predict(req: PredictRequest) -> PredictResponse:
    if not req.text.strip():
        raise HTTPException(status_code=422, detail="Input text must not be empty or whitespace.")
    predictor = _resolve_predictor(req.model)
    preds = predictor.predict_next_word(req.text, top_k=req.top_k)
    return PredictResponse(
        input=req.text,
        model=(req.model or settings.DEFAULT_ARCH),
        predictions=[Prediction(word=w, probability=p) for w, p in preds],
    )


@router.post("/generate", response_model=GenerateResponse, summary="Generate a multi-word continuation")
def generate(req: GenerateRequest) -> GenerateResponse:
    if not req.text.strip():
        raise HTTPException(status_code=422, detail="Input text must not be empty or whitespace.")
    predictor = _resolve_predictor(req.model)
    generated = predictor.generate_text(
        req.text, num_words=req.num_words, temperature=req.temperature
    )
    return GenerateResponse(
        input=req.text,
        model=(req.model or settings.DEFAULT_ARCH),
        generated_text=generated,
        num_words=req.num_words,
        temperature=req.temperature,
    )
