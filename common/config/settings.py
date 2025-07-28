"""Application settings using the user's existing AppBaseSettings pattern."""

import json
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import SettingsConfigDict

from common.schemas import AppBaseSettings


class OpenAISettings(AppBaseSettings):
    """OpenAI API configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="OPENAI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: str = Field(default="", description="OpenAI API key")
    whisper_model: str = Field(default="whisper-1", description="Whisper model for transcription")
    gpt_model: str = Field(
        default="gpt-4.1",
        description="GPT model for structured extraction",
    )
    max_tokens: int = Field(default=500, description="Maximum tokens for responses")
    temperature: float = Field(default=0.1, description="Temperature for consistent responses")
    timeout: int = Field(default=30, description="Request timeout in seconds")


class AudioSettings(AppBaseSettings):
    """Audio processing configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="AUDIO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    storage_path: str = Field(default="audio_storage", description="Audio storage directory")
    max_file_size_mb: int = Field(default=10, description="Maximum audio file size in MB")
    supported_formats: list[str] = Field(
        default=["wav", "mp3", "webm", "m4a"],
        description="Supported audio formats",
    )
    default_sample_rate: int = Field(
        default=16000,
        description="Default sample rate for processing",
    )
    min_sample_rate: int = Field(default=8000, description="Minimum sample rate")
    max_sample_rate: int = Field(default=48000, description="Maximum sample rate")
    max_duration_seconds: int = Field(default=300, description="Maximum audio duration in seconds")


class WebSocketSettings(AppBaseSettings):
    """WebSocket configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="WS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    max_connections: int = Field(
        default=100,
        description="Maximum concurrent WebSocket connections",
    )
    ping_interval: int = Field(default=20, description="Ping interval in seconds")
    ping_timeout: int = Field(default=20, description="Ping timeout in seconds")
    close_timeout: int = Field(default=10, description="Connection close timeout in seconds")
    max_message_size: int = Field(default=10 * 1024 * 1024, description="Max message size in bytes")


class ValidationSettings(AppBaseSettings):
    """Data validation configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="VALIDATION_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Fitness validation limits
    max_fitness_duration_minutes: int = Field(
        default=600,
        description="Max fitness duration (10 hours)",
    )
    min_fitness_duration_minutes: int = Field(default=1, description="Min fitness duration")
    max_distance_km: float = Field(default=100.0, description="Max distance in km")
    min_distance_km: float = Field(default=0.1, description="Min distance in km")

    # Cricket validation limits
    max_coaching_duration_minutes: int = Field(
        default=480,
        description="Max coaching duration (8 hours)",
    )
    min_coaching_duration_minutes: int = Field(default=15, description="Min coaching duration")
    max_focus_areas: int = Field(default=10, description="Max focus areas per session")

    # Match validation limits
    max_runs: int = Field(default=1000, description="Maximum runs in a match")
    max_balls: int = Field(default=600, description="Maximum balls faced")
    max_wickets: int = Field(default=10, description="Maximum wickets")

    # Rest day validation limits
    min_sleep_hours: int = Field(default=4, description="Minimum sleep hours")
    max_sleep_hours: int = Field(default=16, description="Maximum sleep hours")

    # Text validation limits
    max_text_length: int = Field(default=2000, description="Maximum text field length")
    min_text_length: int = Field(default=1, description="Minimum text field length")


class ApplicationSettings(AppBaseSettings):
    """Main application configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application metadata
    title: str = Field(default="Cricket Fitness Tracker API", description="Application title")
    description: str = Field(
        default="Voice-powered cricket fitness tracking system for young athletes",
        description="Application description",
    )
    version: str = Field(default="1.0.0", description="Application version")

    # Server settings - use localhost for development, 0.0.0.0 for production
    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=8010, description="Server port")
    reload: bool = Field(default=False, description="Enable hot reload")

    # CORS settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8020", "http://localhost:8010"],
        description="Allowed CORS origins",
    )

    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="cricket_fitness_tracker.log", description="Log file name")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Parse CORS origins from JSON string if needed."""
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else [str(parsed)]
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        if isinstance(v, list):
            return v
        return [str(v)]


class Settings(AppBaseSettings):
    """Main settings container."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Sub-settings
    app: ApplicationSettings = Field(default_factory=lambda: ApplicationSettings())
    openai: OpenAISettings = Field(default_factory=lambda: OpenAISettings())
    audio: AudioSettings = Field(default_factory=lambda: AudioSettings())
    websocket: WebSocketSettings = Field(default_factory=lambda: WebSocketSettings())
    validation: ValidationSettings = Field(default_factory=lambda: ValidationSettings())


# Global settings instance
settings = Settings()
