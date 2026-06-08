"""Request-ID middleware.

Tags every request/response with a correlation id so logs and error bodies can
be tied back to a single call.
"""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

#: Header carrying the request correlation id, both inbound and outbound.
REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a request id to each request and echo it on the response.

    Honors an inbound ``X-Request-ID`` header when present (so a caller or
    upstream proxy can supply its own id); otherwise mints a fresh ``uuid4`` hex.
    The id is exposed to handlers as ``request.state.request_id`` and returned in
    the ``X-Request-ID`` response header.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Set ``request.state.request_id`` and mirror it onto the response."""
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
