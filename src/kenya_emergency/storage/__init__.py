"""Storage adapters. The default is SQLite; Supabase ships as an extra."""

from kenya_emergency.storage.base import StorageAdapter, StorageMetadata
from kenya_emergency.storage.builder import build_database
from kenya_emergency.storage.sqlite_adapter import SQLiteAdapter
from kenya_emergency.storage.supabase_adapter import SupabaseAdapter

__all__ = [
    "SQLiteAdapter",
    "StorageAdapter",
    "StorageMetadata",
    "SupabaseAdapter",
    "build_database",
]
