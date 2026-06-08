"""FastAPI application factory.

Builds the ASGI app: OpenAPI metadata, CORS, request-id middleware, the
consistent error handlers, and the versioned routers. Routes contain no business
logic — they are thin wrappers over :class:`EmergencyService`.

The module also exposes a ready-to-run ``app = create_app()`` so the server can
be started with ``uvicorn kenya_emergency.api.app:app``.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from kenya_emergency.api.error_handlers import register_exception_handlers
from kenya_emergency.api.middleware import RequestIDMiddleware
from kenya_emergency.api.routes import counties, emergency, health, poison
from kenya_emergency.core.config import Settings
from kenya_emergency.version import __version__

_DESCRIPTION = (
    "Civic-tech infrastructure providing verified emergency contacts, national "
    "emergency numbers, and poison control information for all 47 Kenyan "
    "counties.\n\n"
    "Every record carries provenance: a source, a verification method, and the "
    "date it was last verified.\n\n"
    "v1 scope excludes hospital facilities — those are planned for v1.1."
)

_REPO_URL = "https://github.com/Xander-AJ/kenya-emergency-api"

_OPENAPI_TAGS = [
    {"name": "counties", "description": "Counties and their county-level emergency contacts."},
    {"name": "emergency", "description": "National emergency numbers and one-call overviews."},
    {"name": "poison", "description": "Poison control centres."},
    {"name": "meta", "description": "Service health and dataset metadata."},
]


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure the FastAPI application.

    Args:
        settings: Configuration to use. When ``None``, :class:`Settings` is read
            from the environment/defaults.

    Returns:
        A configured :class:`FastAPI` instance. The :class:`EmergencyService` is
        created lazily on the first storage-touching request (see
        :func:`kenya_emergency.api.dependencies.get_service`), so building the
        app has no storage side effects.
    """
    settings = settings if settings is not None else Settings()

    app = FastAPI(
        title="Kenya Emergency API",
        description=_DESCRIPTION,
        version=__version__,
        contact={"name": "Norah Labs", "url": _REPO_URL},
        license_info={"name": "MIT", "url": f"{_REPO_URL}/blob/main/LICENSE"},
        openapi_tags=_OPENAPI_TAGS,
    )

    # Permissive CORS for the public, read-only dataset. Production deployments
    # should override this (e.g. restrict allow_origins) via env-driven config
    # or by re-mounting CORSMiddleware with tighter settings.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIDMiddleware)

    register_exception_handlers(app)

    # Settings live on app.state; the service is built lazily and cached there.
    app.state.settings = settings

    app.include_router(health.router)
    app.include_router(health.metadata_router, prefix="/v1")
    app.include_router(counties.router, prefix="/v1")
    app.include_router(emergency.router, prefix="/v1")
    app.include_router(poison.router, prefix="/v1")

    return app


#: Module-level app for ``uvicorn kenya_emergency.api.app:app``.
app = create_app()
