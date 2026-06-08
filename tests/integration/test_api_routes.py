"""Integration tests for the FastAPI routes, error shape, and middleware."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from kenya_emergency.api.app import create_app
from kenya_emergency.api.middleware import REQUEST_ID_HEADER
from kenya_emergency.core.config import Settings
from kenya_emergency.core.exceptions import (
    ConfigurationError,
    DataNotFoundError,
    StorageError,
)


def _settings(tmp_path: Path, snapshot_dir: Path) -> Settings:
    return Settings(db_path=tmp_path / "api.db", snapshot_dir=snapshot_dir)


@pytest.fixture
def client(tmp_path: Path, snapshot_dir: Path) -> TestClient:
    """A TestClient over an app backed by the fixture snapshots (lazily built)."""
    return TestClient(create_app(settings=_settings(tmp_path, snapshot_dir)))


def _assert_error_shape(body: Mapping[str, Any], error_type: str) -> None:
    assert set(body) == {"detail", "error_type", "request_id"}
    assert body["error_type"] == error_type
    assert isinstance(body["detail"], str)
    assert isinstance(body["request_id"], str) and body["request_id"]


# --- counties ---------------------------------------------------------------


def test_list_counties(client: TestClient) -> None:
    response = client.get("/v1/counties")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {c["code"] for c in body} == {"001", "047"}


def test_get_county(client: TestClient) -> None:
    response = client.get("/v1/counties/047")
    assert response.status_code == 200
    assert response.json()["name"] == "Nairobi"


def test_get_county_by_name(client: TestClient) -> None:
    response = client.get("/v1/counties/by-name/nairobi")
    assert response.status_code == 200
    assert response.json()["code"] == "047"


def test_get_county_unknown_returns_404(client: TestClient) -> None:
    response = client.get("/v1/counties/046")  # valid shape, no record
    assert response.status_code == 404
    _assert_error_shape(response.json(), "not_found")


def test_get_county_malformed_returns_400(client: TestClient) -> None:
    response = client.get("/v1/counties/abc")
    assert response.status_code == 400
    _assert_error_shape(response.json(), "bad_request")


def test_county_contacts_filter(client: TestClient) -> None:
    all_contacts = client.get("/v1/counties/047/contacts")
    assert all_contacts.status_code == 200
    assert len(all_contacts.json()) == 2

    fire = client.get("/v1/counties/047/contacts", params={"category": "fire"})
    assert fire.status_code == 200
    body = fire.json()
    assert len(body) == 1
    assert body[0]["category"] == "fire"


def test_county_contacts_unknown_category_returns_400(client: TestClient) -> None:
    response = client.get(
        "/v1/counties/047/contacts", params={"category": "fire brigade"}
    )
    assert response.status_code == 400
    _assert_error_shape(response.json(), "bad_request")


# --- emergency --------------------------------------------------------------


def test_national_numbers_and_filter(client: TestClient) -> None:
    assert len(client.get("/v1/emergency/national").json()) == 2
    police = client.get("/v1/emergency/national", params={"category": "police"})
    assert police.status_code == 200
    assert len(police.json()) == 1


def test_police_emergency_present(client: TestClient) -> None:
    response = client.get("/v1/emergency/national/police")
    assert response.status_code == 200
    assert response.json()["short_code"] == "999"


def test_ambulance_emergency_absent_returns_404(client: TestClient) -> None:
    response = client.get("/v1/emergency/national/ambulance")
    assert response.status_code == 404
    _assert_error_shape(response.json(), "not_found")


def test_overview_by_name(client: TestClient) -> None:
    response = client.get("/v1/emergency/overview/Nairobi")
    assert response.status_code == 200
    body = response.json()
    assert body["county"]["code"] == "047"
    assert set(body["contacts_by_category"]) == {"police", "fire"}
    assert len(body["national_numbers"]) == 2


def test_overview_by_code(client: TestClient) -> None:
    response = client.get("/v1/emergency/overview/047")
    assert response.status_code == 200
    assert response.json()["county"]["code"] == "047"


def test_overview_unknown_returns_404(client: TestClient) -> None:
    response = client.get("/v1/emergency/overview/Atlantis")
    assert response.status_code == 404
    _assert_error_shape(response.json(), "not_found")


# --- poison -----------------------------------------------------------------


def test_poison_control_scope_filter(client: TestClient) -> None:
    assert len(client.get("/v1/poison/control").json()) == 1
    national = client.get("/v1/poison/control", params={"scope": "national"})
    assert len(national.json()) == 1
    regional = client.get("/v1/poison/control", params={"scope": "regional"})
    assert regional.json() == []


# --- meta -------------------------------------------------------------------


def test_metadata(client: TestClient) -> None:
    response = client.get("/v1/metadata")
    assert response.status_code == 200
    body = response.json()
    assert body["record_counts"]["counties"] == 2
    assert "built_at" in body


def test_health_does_not_require_storage(tmp_path: Path) -> None:
    """/health stays green even when storage is misconfigured (never queried)."""
    broken = Settings(
        db_path=tmp_path / "nope.db", snapshot_dir=tmp_path / "missing-dir"
    )
    client = TestClient(create_app(settings=broken))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# --- cross-cutting ----------------------------------------------------------


def test_request_id_generated_and_echoed(client: TestClient) -> None:
    generated = client.get("/health")
    assert generated.headers[REQUEST_ID_HEADER]

    echoed = client.get("/health", headers={REQUEST_ID_HEADER: "trace-42"})
    assert echoed.headers[REQUEST_ID_HEADER] == "trace-42"


def test_cors_header_present(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "https://example.com"})
    assert response.headers["access-control-allow-origin"] == "*"


def test_openapi_schema(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["openapi"].startswith("3.")
    assert schema["info"]["title"] == "Kenya Emergency API"
    tag_names = {tag["name"] for tag in schema["tags"]}
    assert {"counties", "emergency", "poison", "meta"} <= tag_names


def test_storage_unavailable_returns_503(tmp_path: Path) -> None:
    """A data request with no snapshots surfaces as 503 in the consistent shape."""
    broken = Settings(
        db_path=tmp_path / "nope.db", snapshot_dir=tmp_path / "missing-dir"
    )
    client = TestClient(create_app(settings=broken))

    response = client.get("/v1/counties")

    assert response.status_code == 503
    _assert_error_shape(response.json(), "storage_unavailable")


def test_all_exception_handlers_share_shape(
    tmp_path: Path, snapshot_dir: Path
) -> None:
    """Each of the four exception types yields the same JSON error body shape."""
    app: FastAPI = create_app(settings=_settings(tmp_path, snapshot_dir))

    @app.get("/_raise/not_found")
    def _not_found() -> None:
        raise DataNotFoundError("missing")

    @app.get("/_raise/configuration")
    def _configuration() -> None:
        raise ConfigurationError("bad config")

    @app.get("/_raise/storage")
    def _storage() -> None:
        raise StorageError("storage down")

    @app.get("/_raise/value")
    def _value() -> None:
        raise ValueError("bad input")

    client = TestClient(app)

    cases = [
        ("/_raise/not_found", 404, "not_found"),
        ("/_raise/configuration", 500, "configuration"),
        ("/_raise/storage", 503, "storage_unavailable"),
        ("/_raise/value", 400, "bad_request"),
    ]
    for path, status_code, error_type in cases:
        response = client.get(path)
        assert response.status_code == status_code
        _assert_error_shape(response.json(), error_type)
