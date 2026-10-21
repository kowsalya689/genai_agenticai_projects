"""HTTP header handling: request id + timing, security headers, per-IP rate limiting."""
import logging
import re
import time
import uuid
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from backend.core.errors import error_response

log = logging.getLogger("lexbrief.http")
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Adds X-Request-ID and X-Process-Time-Ms, logs each request, turns unexpected errors into JSON 500s."""

    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get("x-request-id", "")
        request.state.request_id = incoming if _SAFE_ID.match(incoming) else uuid.uuid4().hex
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:  # noqa: BLE001
            log.exception("unhandled error on %s %s", request.method, request.url.path)
            response = error_response(request, 500, "internal_error", "Something went wrong on the server.")
        ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Process-Time-Ms"] = f"{ms:.1f}"
        log.info("%s %s -> %s (%.0f ms) rid=%s", request.method, request.url.path, response.status_code, ms, request.state.request_id)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Standard hardening headers. A strict CSP is applied everywhere except the Swagger docs pages."""

    CSP = (
        "default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; "
        "base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
    )

    def __init__(self, app, hsts: bool = False):
        super().__init__(app)
        self.hsts = hsts

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        h = response.headers
        h.setdefault("X-Content-Type-Options", "nosniff")
        h.setdefault("X-Frame-Options", "DENY")
        h.setdefault("Referrer-Policy", "no-referrer")
        h.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if not request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
            h.setdefault("Content-Security-Policy", self.CSP)
        if request.url.path.startswith("/api"):
            h["Cache-Control"] = "no-store"          # summaries of legal documents must never be cached
        if self.hsts:
            h.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window limiter (in memory, per client IP) for the expensive endpoints."""

    PROTECTED = ("/api/v1/summarize", "/api/v1/extract")

    def __init__(self, app, per_minute: int = 30):
        super().__init__(app)
        self.limit = per_minute
        self.hits: dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if self.limit <= 0 or request.method != "POST" or not request.url.path.startswith(self.PROTECTED):
            return await call_next(request)
        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        q = self.hits[ip]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= self.limit:
            retry = max(1, int(60 - (now - q[0])))
            return error_response(request, 429, "rate_limited", f"Too many requests. Try again in {retry}s.",
                                  headers={"Retry-After": str(retry), "X-RateLimit-Limit": str(self.limit), "X-RateLimit-Remaining": "0"})
        q.append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(self.limit - len(q))
        return response
