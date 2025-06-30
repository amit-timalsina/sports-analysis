"""Audio storage service for managing voice recordings."""

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiofiles

from common.config.settings import settings
from common.exceptions import AppError

logger = logging.getLogger(__name__)


class AudioStorageError(AppError):
    """Audio storage specific error."""

    status_code = 500
    detail = "Audio storage operation failed"


class AudioStorageService:
    """Service for managing audio file storage and metadata."""

    def __init__(self) -> None:
        """Initialize audio storage service."""
        self.base_path = Path(settings.audio.storage_path)
        self.ensure_storage_directories()

    def ensure_storage_directories(self) -> None:
        """Ensure all required storage directories exist."""
        directories = [
            self.base_path,
            self.base_path / "raw",
            self.base_path / "processed",
            self.base_path / "metadata",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Audio storage directories initialized: %s",
            self.base_path.absolute(),
        )

    def _generate_filename(
        self,
        session_id: str,
        audio_format: str = "webm",
        prefix: str = "audio",
    ) -> str:
        """Generate unique filename for audio file."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{session_id}_{timestamp}.{audio_format}"

    async def save_raw_audio(
        self,
        session_id: str,
        audio_data: bytes,
        audio_format: str = "webm",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Save raw audio data to storage."""
        if len(audio_data) == 0:
            error_msg = "Cannot save empty audio data"
            raise AudioStorageError(error_msg)

        if len(audio_data) > settings.audio.max_file_size_mb * 1024 * 1024:
            msg = "Audio file exceeds maximum size limit"
            raise AudioStorageError(msg)

        try:
            # Generate filename and paths
            filename = self._generate_filename(session_id, audio_format, "raw")
            file_path = self.base_path / "raw" / filename
            metadata_path = self.base_path / "metadata" / f"{filename}.json"

            logger.info("Saving raw audio: %s (%s bytes)", filename, len(audio_data))

            # Use aiofiles for async file operations
            async with aiofiles.open(file_path, "wb") as audio_file:
                await audio_file.write(audio_data)

            # Calculate file hash for verification
            file_hash = hashlib.sha256(audio_data).hexdigest()

            # Prepare metadata
            file_metadata = {
                "session_id": session_id,
                "filename": filename,
                "file_path": str(file_path),
                "file_size": len(audio_data),
                "file_hash": file_hash,
                "audio_format": audio_format,
                "created_at": datetime.now(UTC).isoformat(),
                "custom_metadata": metadata or {},
            }

            # Save metadata
            async with aiofiles.open(metadata_path, "w") as meta_file:
                await meta_file.write(json.dumps(file_metadata, indent=2))

            logger.info("Raw audio saved successfully: %s", filename)

            return {
                "filename": filename,
                "file_path": str(file_path),
                "file_size": len(audio_data),
                "file_hash": file_hash,
                "metadata_path": str(metadata_path),
            }

        except Exception as e:
            logger.exception("Failed to save raw audio")
            error_msg = f"Audio storage failed: {e}"
            raise AudioStorageError(error_msg) from e

    async def save_processed_audio(
        self,
        session_id: str,
        processed_data: bytes,
        audio_format: str = "wav",
        processing_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Save processed audio data to storage."""
        if len(processed_data) == 0:
            error_msg = "Cannot save empty processed audio data"
            raise AudioStorageError(error_msg)

        try:
            # Generate filename and paths
            filename = self._generate_filename(session_id, audio_format, "processed")
            file_path = self.base_path / "processed" / filename
            metadata_path = self.base_path / "metadata" / f"{filename}.json"

            # Use aiofiles for async file operations
            async with aiofiles.open(file_path, "wb") as audio_file:
                await audio_file.write(processed_data)

            # Prepare metadata
            file_metadata = {
                "session_id": session_id,
                "filename": filename,
                "file_path": str(file_path),
                "file_size": len(processed_data),
                "audio_format": audio_format,
                "created_at": datetime.now(UTC).isoformat(),
                "processing_metadata": processing_metadata or {},
            }

            # Save metadata
            async with aiofiles.open(metadata_path, "w") as meta_file:
                await meta_file.write(json.dumps(file_metadata, indent=2))

            logger.info("Processed audio saved successfully: %s", filename)

            return {
                "filename": filename,
                "file_path": str(file_path),
                "file_size": len(processed_data),
                "metadata_path": str(metadata_path),
            }

        except Exception as e:
            logger.exception("Failed to save processed audio")
            error_msg = f"Processed audio storage failed: {e}"
            raise AudioStorageError(error_msg) from e

    def get_session_audio_files(self, session_id: str) -> dict[str, Any]:
        """Get all audio files for a specific session."""
        try:
            raw_files = []
            processed_files = []

            # Check raw audio files
            raw_dir = self.base_path / "raw"
            if raw_dir.exists():
                raw_files.extend(
                    [
                        {
                            "filename": file.name,
                            "file_path": str(file),
                            "file_size": file.stat().st_size,
                            "created_at": datetime.fromtimestamp(
                                file.stat().st_mtime,
                                tz=UTC,
                            ).isoformat(),
                        }
                        for file in raw_dir.glob(f"*{session_id}*")
                    ],
                )

            # Check processed audio files
            processed_dir = self.base_path / "processed"
            if processed_dir.exists():
                processed_files.extend(
                    [
                        {
                            "filename": file.name,
                            "file_path": str(file),
                            "file_size": file.stat().st_size,
                            "created_at": datetime.fromtimestamp(
                                file.stat().st_mtime,
                                tz=UTC,
                            ).isoformat(),
                        }
                        for file in processed_dir.glob(f"*{session_id}*")
                    ],
                )

            return {
                "session_id": session_id,
                "raw_files": raw_files,
                "processed_files": processed_files,
                "total_files": len(raw_files) + len(processed_files),
            }

        except Exception as e:
            logger.exception("Failed to get session audio files")
            return {"session_id": session_id, "error": str(e)}

    def get_storage_stats(self) -> dict[str, Any]:
        """Get storage statistics."""
        try:
            stats: dict[str, Any] = {
                "base_path": str(self.base_path.absolute()),
                "directories": {},
                "total_files": 0,
                "total_size_bytes": 0,
            }

            # Analyze each directory
            for subdir in ["raw", "processed", "metadata"]:
                dir_path = self.base_path / subdir
                if dir_path.exists():
                    files = list(dir_path.glob("*"))
                    total_size = sum(file.stat().st_size for file in files if file.is_file())

                    stats["directories"][subdir] = {
                        "file_count": len(files),
                        "total_size_bytes": total_size,
                        "total_size_mb": round(total_size / (1024 * 1024), 2),
                    }

                    stats["total_files"] += len(files)
                    stats["total_size_bytes"] += total_size

            stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)

        except Exception as e:
            logger.exception("Failed to get storage stats")
            return {"error": str(e)}
        else:
            return stats

    async def cleanup_old_files(self, max_age_days: int = 7) -> dict[str, Any]:
        """Clean up old audio files."""
        try:
            cutoff_time = datetime.now(UTC).timestamp() - (max_age_days * 24 * 3600)
            cleanup_stats = {"deleted_files": 0, "freed_bytes": 0, "errors": []}

            for subdir in ["raw", "processed", "metadata"]:
                dir_path = self.base_path / subdir
                if not dir_path.exists():
                    continue

                for file_path in dir_path.glob("*"):
                    if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                        try:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            cleanup_stats["deleted_files"] += 1
                            cleanup_stats["freed_bytes"] += file_size
                        except Exception as e:
                            cleanup_stats["errors"].append(f"{file_path.name}: {e}")

            logger.info(
                "Cleanup completed: %d files deleted, %.2f MB freed",
                cleanup_stats["deleted_files"],
                cleanup_stats["freed_bytes"] / (1024 * 1024),
            )

        except Exception as e:
            logger.exception("Failed to cleanup old files")
            error_msg = f"Cleanup failed: {e}"
            raise AudioStorageError(error_msg) from e
        else:
            return cleanup_stats

    async def get_audio_metadata(self, filename: str) -> dict[str, Any] | None:
        """Get metadata for a specific audio file."""
        try:
            metadata_path = self.base_path / "metadata" / f"{filename}.json"

            if not metadata_path.exists():
                return None

            async with aiofiles.open(metadata_path) as meta_file:
                content = await meta_file.read()
                return json.loads(content)

        except Exception as e:
            logger.exception("Failed to get audio metadata")
            error_msg = f"Metadata retrieval failed: {e}"
            raise AudioStorageError(error_msg) from e


# Global audio storage service instance
audio_storage = AudioStorageService()
