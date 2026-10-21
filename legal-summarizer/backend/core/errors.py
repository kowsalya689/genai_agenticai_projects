"""One error shape for the whole API: {"error": {"code", "message", "request_id"}}."""
from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code, self.code, self.message = status_code, code, message


def error_response(request: Request, status_code: int, code: str, message: str, headers: dict | None = None):
    rid = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "request_id": rid}},
        headers=headers,
    )
