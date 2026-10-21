"""Pydantic request/response models (these also generate the Swagger docs at /docs)."""
from pydantic import BaseModel, Field, field_validator


class SummarizeRequest(BaseModel):
    text: str = Field(..., description="Plain-text legal document (contract, policy, notice, ...).")
    compression: float | None = Field(None, ge=0.05, le=0.6, description="Target summary length as a fraction of the source (default 0.20).")
    max_summary_tokens: int | None = Field(None, ge=50, le=1000, description="Hard cap on summary length in tokens (default 350).")
    num_beams: int | None = Field(None, ge=1, le=8, description="Beam-search width (default 4).")

    @field_validator("text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError("Document is too short to summarise (minimum 10 characters).")
        return v


class Faithfulness(BaseModel):
    unsupported_numbers: list[str] = []
    unsupported_dates: list[str] = []
    unsupported_terms: list[str] = []
    n_numbers: int = 0
    n_terms: int = 0


class PassInfo(BaseModel):
    level: int
    chunks: int
    summary_tokens: int


class SummarizeResponse(BaseModel):
    summary: str
    source_tokens: int
    summary_tokens: int
    source_words: int
    summary_words: int
    compression_ratio: float
    passes: list[PassInfo]
    warnings: list[str]
    faithfulness: Faithfulness
    model: str
    elapsed_ms: int


class ExtractResponse(BaseModel):
    filename: str
    characters: int
    text: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_error: str | None = None
    device: str | None = None
    version: str


class ModelInfo(BaseModel):
    loaded: bool
    source: str | None = None
    device: str | None = None
    parameters_millions: float | None = None
    encoder_layers: int | None = None
    decoder_layers: int | None = None
    attention_heads: int | None = None
    d_model: int | None = None
    max_positions: int | None = None
    target_compression: float
    final_cap_tokens: int


class Sample(BaseModel):
    id: str
    title: str
    text: str
    key_facts: list[str]
