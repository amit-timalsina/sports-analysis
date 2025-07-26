"""WebSocket connection management for voice processing sessions."""

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

from common.config.settings import settings
from common.exceptions import AppError
from logger import get_logger
from voice_processing.schemas.processing import WebSocketMessage

logger = get_logger(__name__)


class UUIDEncoder(json.JSONEncoder):
    """JSON encoder that handles UUID objects."""

    def default(self, obj: Any) -> Any:
        """Convert UUID objects to strings."""
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


class WebSocketError(AppError):
    """WebSocket specific error."""

    status_code = 500
    detail = "WebSocket operation failed"


class ConnectionManager:
    """Manages WebSocket connections for voice processing sessions with settings-driven limits."""

    def __init__(self) -> None:
        """Initialize the connection manager."""
        self.active_connections: dict[UUID, WebSocket] = {}
        self.session_metadata: dict[UUID, dict[str, Any]] = {}
        self.audio_buffers: dict[UUID, bytes] = {}  # Add audio buffering

    async def connect(self, websocket: WebSocket, session_id: UUID) -> None:
        """
        Accept and store a WebSocket connection with connection limits.

        Args:
            websocket: The WebSocket connection to accept
            session_id: Unique identifier for this session

        Raises:
            WebSocketError: If connection limit exceeded

        """
        # Check connection limits from settings
        if len(self.active_connections) >= settings.websocket.max_connections:
            await websocket.close(code=1008, reason="Connection limit exceeded")
            msg = f"Connection limit of {settings.websocket.max_connections} exceeded"
            raise WebSocketError(
                msg,
            )

        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.session_metadata[session_id] = {
            "connected_at": datetime.now(UTC).isoformat() + "Z",
            "message_count": 0,
            "last_activity": datetime.now(UTC).isoformat() + "Z",
        }
        # Initialize audio buffer for this session
        self.audio_buffers[session_id] = b""

        logger.info(
            "WebSocket connected for session: %s (%d total)",
            session_id,
            len(self.active_connections),
        )

    def disconnect(self, session_id: UUID) -> None:
        """
        Disconnect and clean up a WebSocket session.

        Args:
            session_id: Session to disconnect

        """
        if session_id in self.active_connections:
            del self.active_connections[session_id]

        if session_id in self.session_metadata:
            del self.session_metadata[session_id]

        # Clean up audio buffer
        if session_id in self.audio_buffers:
            del self.audio_buffers[session_id]

        logger.info(
            "WebSocket disconnected for session: %s (%d remaining)",
            session_id,
            len(self.active_connections),
        )

    async def send_message(self, message: WebSocketMessage, session_id: UUID) -> None:
        """
        Send a structured message to a specific session.

        Args:
            message: WebSocketMessage to send
            session_id: Target session identifier

        """
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                # Use custom encoder for UUID objects
                message_data = message.model_dump()
                logger.info("Message sent to session %s: %s", session_id, message_data)
                await websocket.send_text(json.dumps(message_data, cls=UUIDEncoder))

                # Update metadata
                if session_id in self.session_metadata:
                    self.session_metadata[session_id]["message_count"] += 1

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected during send for session: {session_id}")
                self.disconnect(session_id)

            except Exception as e:
                logger.exception("Failed to send message to session %s: %s", session_id, e)
                # Connection might be broken, remove it
                self.disconnect(session_id)
        else:
            logger.warning("Attempted to send message to non-existent session: %s", session_id)

    async def send_personal_message(self, message: dict[str, Any], session_id: UUID) -> None:
        """
        Send a raw dictionary message to a specific session (for backward compatibility).

        Args:
            message: Dictionary message to send
            session_id: Target session identifier

        """
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_text(json.dumps(message))

                # Update metadata
                if session_id in self.session_metadata:
                    self.session_metadata[session_id]["message_count"] += 1

                logger.debug(
                    "Raw message sent to session %s: %s",
                    session_id,
                    message.get("type", "unknown"),
                )

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected during send for session: {session_id}")
                self.disconnect(session_id)

            except Exception as e:
                logger.exception("Failed to send raw message to session %s: %s", session_id, e)
                # Connection might be broken, remove it
                self.disconnect(session_id)
        else:
            logger.warning("Attempted to send raw message to non-existent session: %s", session_id)

    async def broadcast_message(self, message: WebSocketMessage) -> None:
        """
        Send a structured message to all connected sessions.

        Args:
            message: WebSocketMessage to broadcast

        """
        if not self.active_connections:
            logger.debug("No active connections to broadcast to")
            return

        disconnected_sessions = []
        for session_id, websocket in self.active_connections.items():
            try:
                # Use custom encoder for UUID objects
                message_data = message.model_dump()
                await websocket.send_text(json.dumps(message_data, cls=UUIDEncoder))

                # Update metadata
                if session_id in self.session_metadata:
                    self.session_metadata[session_id]["message_count"] += 1

            except WebSocketDisconnect:
                logger.info("WebSocket disconnected during broadcast for session: %s", session_id)
                disconnected_sessions.append(session_id)

            except Exception as e:
                logger.exception("Failed to broadcast to session %s: %s", session_id, e)
                disconnected_sessions.append(session_id)

        # Clean up disconnected sessions
        for session_id in disconnected_sessions:
            self.disconnect(session_id)

    def get_active_sessions(self) -> list[UUID]:
        """
        Get list of currently active session IDs.

        Returns:
            List of active session identifiers

        """
        return list(self.active_connections.keys())

    def is_session_active(self, session_id: UUID) -> bool:
        """
        Check if a session is currently active.

        Args:
            session_id: Session identifier to check

        Returns:
            True if session is active, False otherwise

        """
        return session_id in self.active_connections

    def get_connection_count(self) -> int:
        """
        Get the current number of active connections.

        Returns:
            Number of active connections

        """
        return len(self.active_connections)

    def get_connection_info(self, session_id: UUID) -> dict[str, Any] | None:
        """
        Get connection information for a specific session.

        Args:
            session_id: Session identifier

        Returns:
            Connection info dictionary or None if session not found

        """
        if session_id not in self.active_connections:
            return None

        metadata = self.session_metadata.get(session_id, {})
        return {
            "session_id": session_id,
            "connected": True,
            "metadata": metadata,
            "total_connections": len(self.active_connections),
            "max_connections": settings.websocket.max_connections,
        }

    def get_stats(self) -> dict[str, Any]:
        """
        Get overall connection statistics.

        Returns:
            Statistics dictionary

        """
        return {
            "active_connections": len(self.active_connections),
            "max_connections": settings.websocket.max_connections,
            "connection_utilization": len(self.active_connections)
            / settings.websocket.max_connections,
            "active_sessions": self.get_active_sessions(),
            "total_messages_sent": sum(
                metadata.get("message_count", 0) for metadata in self.session_metadata.values()
            ),
        }

    def set_session_metadata(self, session_id: UUID, metadata: dict[str, Any]) -> None:
        """
        Set custom metadata for a session.

        Args:
            session_id: Session identifier
            metadata: Dictionary of metadata to store

        """
        if session_id in self.session_metadata:
            self.session_metadata[session_id].update(metadata)
            self.session_metadata[session_id]["last_activity"] = datetime.now(UTC).isoformat() + "Z"
            logger.debug("Updated metadata for session %s: %s", session_id, metadata)
        else:
            logger.warning("Attempted to set metadata for non-existent session: %s", session_id)

    def get_session_metadata(self, session_id: UUID) -> dict[str, Any] | None:
        """
        Get custom metadata for a session.

        Args:
            session_id: Session identifier

        Returns:
            Session metadata dictionary or None if session not found

        """
        if session_id in self.session_metadata:
            return self.session_metadata[session_id].copy()
        return None

    async def cleanup(self) -> None:
        """Cleanup all connections gracefully."""
        if not self.active_connections:
            return

        logger.info("Cleaning up %d WebSocket connections", len(self.active_connections))

        # Send goodbye message to all connections
        for session_id, websocket in self.active_connections.items():
            try:
                goodbye_message = WebSocketMessage(
                    type="connection_closed",
                    message="Server is shutting down",
                    session_id=session_id,
                )
                message_data = goodbye_message.model_dump()
                await websocket.send_text(json.dumps(message_data, cls=UUIDEncoder))
                await websocket.close(code=1001, reason="Server shutdown")
            except Exception:
                logger.exception("Error during cleanup for session %s", session_id)

        # Clear all connections
        self.active_connections.clear()
        self.session_metadata.clear()
        logger.info("WebSocket cleanup completed")

    def accumulate_audio_chunk(self, session_id: UUID, audio_chunk: bytes) -> None:
        """
        Accumulate audio chunks for a session.

        Args:
            session_id: Session identifier
            audio_chunk: Audio data chunk to accumulate

        """
        if session_id not in self.audio_buffers:
            self.audio_buffers[session_id] = b""

        self.audio_buffers[session_id] += audio_chunk
        logger.debug(
            "Accumulated audio chunk for session %s: +%d bytes (total: %d bytes)",
            session_id,
            len(audio_chunk),
            len(self.audio_buffers[session_id]),
        )

    def get_accumulated_audio(self, session_id: UUID) -> bytes:
        """
        Get all accumulated audio for a session.

        Args:
            session_id: Session identifier

        Returns:
            All accumulated audio data

        """
        return self.audio_buffers.get(session_id, b"")

    def clear_audio_buffer(self, session_id: UUID) -> None:
        """
        Clear the audio buffer for a session.

        Args:
            session_id: Session identifier

        """
        if session_id in self.audio_buffers:
            self.audio_buffers[session_id] = b""
            logger.debug("Cleared audio buffer for session %s", session_id)


# Global connection manager instance
connection_manager = ConnectionManager()
