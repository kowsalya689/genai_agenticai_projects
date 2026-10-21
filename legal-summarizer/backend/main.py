"""FastAPI application factory. Serves the JSON API under /api/v1 and the web UI from /frontend at '/'."""
import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.api.routes import router
from backend.config import ROOT, Settings, get_settings
from backend.core.errors import AppError, error_response
from backend.core.logging import setup_logging
from backend.core.middleware import RateLimitMiddleware, RequestContextMiddleware, SecurityHeadersMiddleware

log = logging.getLogger("lexbrief")
FRONTEND_DIR = ROOT / "frontend"


def create_app(settings: Settings | None = None, summarizer=None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings.log_level)

    if summarizer is None:
        from backend.services.summarizer import LegalSummarizer
        summarizer = LegalSummarizer(settings)

    def _load_in_background():
        try:
            summarizer.load()
        except Exception as exc:  # noqa: BLE001
            summarizer.load_error = f"{type(exc).__name__}: {exc}"
            log.exception("Model failed to load")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.preload_model and not summarizer.is_loaded:
            # background thread: the server (and /api/v1/health) is reachable while the model loads
            threading.Thread(target=_load_in_background, daemon=True).start()
        yield

    app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan,
                  docs_url=None if settings.is_production else "/docs",
                  redoc_url=None, openapi_url=None if settings.is_production else "/openapi.json")
    app.state.summarizer = summarizer
    app.state.settings = settings

    # ---- middleware (the LAST one added is the OUTERMOST) ----
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(SecurityHeadersMiddleware, hsts=settings.is_production)
    app.add_middleware(RateLimitMiddleware, per_minute=settings.rate_limit_per_minute)
    app.add_middleware(CORSMiddleware, allow_origins=settings.origins_list, allow_methods=["GET", "POST", "OPTIONS"],
                       allow_headers=["Content-Type", "X-Request-ID"],
                       expose_headers=["X-Request-ID", "X-Process-Time-Ms", "X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"],
                       max_age=600)
    app.add_middleware(RequestContextMiddleware)

    # ---- error handlers: one JSON shape everywhere ----
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError):
        return error_response(request, exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        first = exc.errors()[0] if exc.errors() else {}
        loc = ".".join(str(p) for p in first.get("loc", []) if p != "body")
        msg = first.get("msg", "Invalid request").removeprefix("Value error, ")
        return error_response(request, 422, "validation_error", f"{loc}: {msg}" if loc else msg)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        return error_response(request, exc.status_code, "http_error", str(exc.detail))

    app.include_router(router)
    if FRONTEND_DIR.exists():
        app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    return app


app = create_app()
