"""
The FastAPI web application.

Endpoints:
  GET  /          -> the web page (paste text, get a result)
  POST /predict   -> send {"text": "..."} and get the label + confidence back
  GET  /health    -> quick check that the server is alive
  GET  /docs       -> automatic interactive API documentation
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR
from app.detector import get_detector
from app.schemas import PredictRequest, PredictResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the model once when the server starts (so the first request is fast).
    print("Loading model, please wait...")
    get_detector()
    print("Model loaded. Server is ready.")
    yield


app = FastAPI(
    title="Fake News Detection System",
    description="Classifies a news headline or article as REAL or FAKE using DistilBERT.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["system"])
def health():
    """Simple liveness check."""
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse, tags=["prediction"])
def predict(request: PredictRequest):
    """Classify one headline or article."""
    detector = get_detector()
    try:
        return detector.predict(request.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- serve the simple web page ---------------------------------------------
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(BASE_DIR / "static" / "index.html")
