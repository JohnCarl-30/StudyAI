"""
Supabase Storage service for persisting uploaded PDF files.

Replaces local disk storage (which is ephemeral on Render free tier).
Files are stored in a private Supabase bucket and downloaded to a
temporary local file when PDF processing is needed.
"""
import os
import tempfile
from datetime import datetime
from functools import lru_cache
from typing import Optional

from supabase import create_client, Client
from app.config import settings


class StorageService:

    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be set to use cloud storage."
            )
        self._client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.bucket = settings.SUPABASE_BUCKET

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def upload(self, file_bytes: bytes, storage_path: str) -> str:
        """Upload bytes to Supabase Storage. Returns storage_path."""
        self._client.storage.from_(self.bucket).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": "application/pdf", "upsert": True},
        )
        return storage_path

    def download(self, storage_path: str) -> bytes:
        """Download file bytes from Supabase Storage."""
        return self._client.storage.from_(self.bucket).download(storage_path)

    def delete(self, storage_path: str) -> None:
        """Delete a file from Supabase Storage."""
        try:
            self._client.storage.from_(self.bucket).remove([storage_path])
        except Exception as e:
            print(f"[StorageService] Failed to delete {storage_path}: {e}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def download_to_temp(self, storage_path: str) -> str:
        """
        Download a file to a local temp file. Caller is responsible for
        deleting the temp file when done (use try/finally + os.unlink).

        Returns the temp file path.
        """
        file_bytes = self.download(storage_path)
        suffix = os.path.splitext(storage_path)[-1] or ".pdf"
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        try:
            tmp.write(file_bytes)
            tmp.flush()
            return tmp.name
        finally:
            tmp.close()

    @staticmethod
    def build_storage_path(user_id: int, filename: str) -> str:
        """Build a deterministic, unique storage path for a file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Sanitize filename to avoid path traversal
        safe_name = os.path.basename(filename)
        return f"{user_id}/{timestamp}_{safe_name}"


@lru_cache(maxsize=1)
def get_storage_service() -> StorageService:
    """Return a cached StorageService singleton."""
    return StorageService()
