"""Runtime configuration for kenya-emergency-api.

Settings are loaded from environment variables (prefixed ``KENYA_EMERGENCY_``)
and an optional ``.env`` file, falling back to defaults that make the package
work out of the box against its bundled SQLite snapshot.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import HttpUrl, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from kenya_emergency.core.exceptions import ConfigurationError

#: Directory containing the installed ``kenya_emergency`` package.
_PACKAGE_DIR = Path(__file__).resolve().parent.parent

#: Default location of the bundled SQLite database. The file is built from the
#: vendored snapshots in ``data/snapshots/`` and may not exist yet.
DEFAULT_DB_PATH = _PACKAGE_DIR / "data" / "kenya_emergency.db"

#: Directory holding the vendored JSON snapshots bundled with the package.
DEFAULT_SNAPSHOT_DIR = _PACKAGE_DIR / "data" / "snapshots"


class Settings(BaseSettings):
    """Application settings resolved from the environment.

    Attributes:
        db_path: Filesystem path to the SQLite database file. Defaults to the
            database bundled with the package, which may not exist until it is
            built from the vendored snapshots.
        snapshot_dir: Directory of JSON snapshots used to build the SQLite
            database on first use. Defaults to the snapshots bundled with the
            package.
        storage_adapter: Which storage backend to use.
        supabase_url: Supabase project URL. Required when
            ``storage_adapter == "supabase"``.
        supabase_key: Supabase API key. Required when
            ``storage_adapter == "supabase"``.
    """

    model_config = SettingsConfigDict(
        env_prefix="KENYA_EMERGENCY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db_path: Path = DEFAULT_DB_PATH
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR
    storage_adapter: Literal["sqlite", "supabase"] = "sqlite"
    supabase_url: HttpUrl | None = None
    supabase_key: str | None = None

    @model_validator(mode="after")
    def _validate_supabase_credentials(self) -> Settings:
        """Ensure Supabase credentials are present when that adapter is selected."""
        if self.storage_adapter == "supabase":
            missing = [
                name
                for name, value in (
                    ("supabase_url", self.supabase_url),
                    ("supabase_key", self.supabase_key),
                )
                if value is None
            ]
            if missing:
                joined = ", ".join(missing)
                raise ConfigurationError(
                    f"storage_adapter='supabase' requires the following setting(s): {joined}"
                )
        return self
