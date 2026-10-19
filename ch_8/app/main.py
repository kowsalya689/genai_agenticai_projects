"""Application entrypoint.

Creates the FastAPI app, mounts static files and the HTML frontend, wires up the
prediction and health routers, and loads the model bundle once at startup.

Run locally:
    uvicorn app.main:app --reload
or:
    python app.py
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config.settings import settings
from app.models.model_loader import load_bundle
from app.routes import health_routes, prediction_routes

BASE_DIR = Path(__file__).resolve().parents[1]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm the model cache at startup; degrade gracefully if artifacts absent."""
    try:
        load_bundle()
        print("[startup] Model + tokenizer loaded successfully.")
    except Exception as exc:  # noqa: BLE001
        print(f"[startup] WARNING: could not load artifacts yet: {exc}")
    yield
    print("[shutdown] Bye.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="LSTM-based next-word prediction and text generation API.",
    lifespan=lifespan,
)

# Static assets + Jinja2 templates for the browser UI.
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# API routers.
app.include_router(prediction_routes.router)
app.include_router(health_routes.router)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index(request: Request):
    """Serve the single-page frontend."""
    return templates.TemplateResponse(
        "index.html", {"request": request, "app_name": settings.APP_NAME}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
