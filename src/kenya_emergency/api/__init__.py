"""FastAPI surface wrapping the shared service layer."""

from kenya_emergency.api.app import create_app

__all__ = ["create_app"]
