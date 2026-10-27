"""
Request and response shapes for the API.

FastAPI uses these to check incoming data and to document the API automatically
(visit /docs when the server is running).
"""
from typing import Dict

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """What the client sends: one piece of text."""
    text: str = Field(..., min_length=1, description="A news headline or article body")

    model_config = {
        "json_schema_extra": {
            "example": {"text": "The central bank raised interest rates after its policy meeting."}
        }
    }


class PredictResponse(BaseModel):
    """What the API sends back."""
    label: str = Field(..., description='Either "REAL" or "FAKE"')
    confidence: float = Field(..., description="How sure the model is (0 to 1)")
    probabilities: Dict[str, float] = Field(..., description="Probability for each class")
