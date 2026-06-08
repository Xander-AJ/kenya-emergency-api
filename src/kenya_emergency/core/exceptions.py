"""Exception hierarchy for kenya-emergency-api.

All errors raised by this package derive from :class:`KenyaEmergencyError`, so
callers can catch the whole family with a single ``except`` clause.
"""

from __future__ import annotations


class KenyaEmergencyError(Exception):
    """Base class for every error raised by kenya-emergency-api."""


class DataNotFoundError(KenyaEmergencyError):
    """Raised when a requested record does not exist in the backing store."""


class StorageError(KenyaEmergencyError):
    """Raised when the storage backend fails to read or write data."""


class ConfigurationError(KenyaEmergencyError):
    """Raised when the runtime configuration is invalid or incomplete."""
