"""Pydantic request/response schemas.

These drive automatic request validation and the OpenAPI (Swagger) docs served
at ``/docs``. Bounds mirror the guard rails in :mod:`app.config.settings`.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

# Note: the ``model`` request field selects the architecture (lstm/gru/rnn).
# Pydantic reserves the ``model_`` namespace, so schemas carrying that field
# disable protected namespaces.


class PredictRequest(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "example": {"text": "the stock market", "top_k": 5, "model": "lstm"}
        },
    )

    text: str = Field(..., min_length=1, description="Seed word, phrase, or partial sentence.")
    top_k: int = Field(5, ge=1, le=20, description="Number of candidate next words to return.")
    model: Optional[str] = Field(
        None, description="Architecture to use: lstm (default), gru, or rnn."
    )


class Prediction(BaseModel):
    word: str
    probability: float


class PredictResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    input: str
    model: str
    predictions: List[Prediction]


class GenerateRequest(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "example": {
                "text": "the government has decided to",
                "num_words": 14,
                "temperature": 0.7,
                "model": "lstm",
            }
        },
    )

    text: str = Field(..., min_length=1, description="Seed text to continue.")
    num_words: int = Field(12, ge=1, le=50, description="Number of words to generate.")
    temperature: float = Field(
        0.8, ge=0.0, le=2.0,
        description="Sampling temperature. 0 = greedy/deterministic; higher = more random.",
    )
    model: Optional[str] = Field(
        None, description="Architecture to use: lstm (default), gru, or rnn."
    )


class GenerateResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    input: str
    model: str
    generated_text: str
    num_words: int
    temperature: float


class ModelInfo(BaseModel):
    name: str
    loaded: bool
    default: bool


class ModelsResponse(BaseModel):
    models: List[ModelInfo]
    default: str


class HealthResponse(BaseModel):
    # Disable protected-namespace warning for the ``model_*`` field name.
    model_config = ConfigDict(protected_namespaces=())

    status: str
    model_loaded: bool
    available_models: List[str] = []
    context_length: int
    vocab_size: int
