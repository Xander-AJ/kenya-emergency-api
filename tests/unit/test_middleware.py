"""Unit test for the request-id middleware."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from kenya_emergency.api.middleware import REQUEST_ID_HEADER, RequestIDMiddleware


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/echo")
    def echo(request: Request) -> dict[str, str]:
        return {"request_id": request.state.request_id}

    return app


def test_request_id_generated_when_absent() -> None:
    """A response gets an X-Request-ID even when the request omits it."""
    client = TestClient(_app())

    response = client.get("/echo")

    generated = response.headers[REQUEST_ID_HEADER]
    assert generated
    # The id the handler saw matches the one returned to the caller.
    assert response.json()["request_id"] == generated


def test_request_id_echoed_when_present() -> None:
    """An inbound X-Request-ID is preserved on the response and in handler state."""
    client = TestClient(_app())

    response = client.get("/echo", headers={REQUEST_ID_HEADER: "abc123"})

    assert response.headers[REQUEST_ID_HEADER] == "abc123"
    assert response.json()["request_id"] == "abc123"
