"""Exception handlers producing a consistent JSON error shape.

Every error response has the same body::

    {"detail": str, "error_type": str, "request_id": str | null}

and carries the request's correlation id. Client-caused errors (400/404) are
logged at WARNING; server-side problems (500/503) at ERROR.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from kenya_emergency.core.exceptions import (
    ConfigurationError,
    DataNotFoundError,
    StorageError,
)

logger = logging.getLogger(__name__)


def _error_response(
    request: Request, status_code: int, detail: str, error_type: str
) -> JSONResponse:
    """Build the canonical error JSON response, including the request id."""
    request_id: str | None = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "error_type": error_type, "request_id": request_id},
    )


def _log(request: Request, exc: Exception, status_code: int) -> None:
    """Log an error with request id, route, and exception class."""
    request_id = getattr(request.state, "request_id", None)
    level = logging.ERROR if status_code >= 500 else logging.WARNING
    logger.log(
        level,
        "%s on %s %s [request_id=%s]: %s",
        type(exc).__name__,
        request.method,
        request.url.path,
        request_id,
        exc,
    )


async def _handle_not_found(request: Request, exc: Exception) -> JSONResponse:
    """Map :class:`DataNotFoundError` to 404."""
    _log(request, exc, 404)
    return _error_response(request, 404, str(exc), "not_found")


async def _handle_configuration(request: Request, exc: Exception) -> JSONResponse:
    """Map :class:`ConfigurationError` to 500."""
    _log(request, exc, 500)
    return _error_response(request, 500, str(exc), "configuration")


async def _handle_storage(request: Request, exc: Exception) -> JSONResponse:
    """Map :class:`StorageError` to 503 (storage health, not a programming bug)."""
    _log(request, exc, 503)
    return _error_response(request, 503, str(exc), "storage_unavailable")


async def _handle_value_error(request: Request, exc: Exception) -> JSONResponse:
    """Map :class:`ValueError` (bad caller input) to 400."""
    _log(request, exc, 400)
    return _error_response(request, 400, str(exc), "bad_request")


async def _handle_validation(request: Request, exc: Exception) -> JSONResponse:
    """Map FastAPI's request validation errors to a 400 in our shape.

    By default FastAPI returns 422 with its own body; we normalize bad query/path
    input (e.g. an unknown category enum) to the same 400 shape as other
    caller-input errors.
    """
    _log(request, exc, 400)
    detail = "Invalid request parameters"
    if isinstance(exc, RequestValidationError) and exc.errors():
        first = exc.errors()[0]
        msg = str(first.get("msg", detail))
        location = ".".join(str(part) for part in first.get("loc", ()))
        detail = f"{msg} ({location})" if location else msg
    return _error_response(request, 400, detail, "bad_request")


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the application."""
    app.add_exception_handler(DataNotFoundError, _handle_not_found)
    app.add_exception_handler(ConfigurationError, _handle_configuration)
    app.add_exception_handler(StorageError, _handle_storage)
    app.add_exception_handler(ValueError, _handle_value_error)
    app.add_exception_handler(RequestValidationError, _handle_validation)
