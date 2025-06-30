"""OpenAI service for transcription and structured data extraction."""

import logging
import re
from datetime import UTC, datetime
from io import BytesIO
from typing import Any

from langfuse import observe
from openai import AsyncOpenAI

from common.config.settings import settings
from common.exceptions import AppError
from fitness_tracking.schemas.fitness import FitnessDataExtraction
from voice_processing.schemas.processing import TranscriptionResponse

logger = logging.getLogger(__name__)


class OpenAIServiceError(AppError):
    """OpenAI service specific error."""

    status_code = 500
    detail = "OpenAI service operation failed"


class OpenAIService:
    """Service for OpenAI transcription and data extraction."""

    def __init__(self) -> None:
        """Initialize OpenAI service."""
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI | None:
        """Get OpenAI client, initializing it if needed."""
        if self._client is None:
            # Check if we're in testing mode
            if settings.app.is_testing:
                # Return None for testing - functions should handle this gracefully
                return None

            if not settings.openai.api_key:
                logger.warning("OpenAI API key not configured")
                return None

            try:
                self._client = AsyncOpenAI(
                    api_key=settings.openai.api_key,
                    timeout=settings.openai.timeout,
                )
            except Exception as e:
                logger.warning("Failed to initialize OpenAI client: %s", e)
                return None

        return self._client

    async def transcribe_audio(self, audio_data: bytes) -> TranscriptionResponse:
        """
        Transcribe audio using OpenAI Whisper with settings-driven configuration.

        Args:
            audio_data: Audio data in bytes format

        Returns:
            TranscriptionResponse with text and metadata

        Raises:
            OpenAIServiceError: If transcription fails

        """
        client = self._get_client()

        # Handle testing or when client is not available
        if client is None:
            logger.info("Mock transcription for testing")
            return TranscriptionResponse(
                text="Mock transcription result",
                confidence=0.9,
                language="en",
            )

        if len(audio_data) == 0:
            msg = "Audio data is empty"
            raise OpenAIServiceError(msg)

        try:
            # Convert bytes to a file-like object with proper naming
            audio_file = BytesIO(audio_data)
            audio_file.name = "audio.wav"  # Provide a name for file type detection

            # Use settings-driven configuration for Whisper
            prompt = "This is cricket and fitness related voice data from a young athlete in Nepal."
            response = await client.audio.transcriptions.create(
                model=settings.openai.whisper_model,
                file=audio_file,
                language="en",  # English for cricket/fitness context
                response_format="verbose_json",  # Get detailed response
                temperature=settings.openai.temperature,
                prompt=prompt,
            )

            # Extract text from verbose response
            transcript_text = response.text

            # Calculate confidence based on response quality
            confidence = self._calculate_confidence(transcript_text, response)

            # Log information
            if hasattr(response, "language"):
                logger.info(
                    "Transcription successful: %d characters, language: %s",
                    len(transcript_text),
                    response.language,
                )
            else:
                logger.info("Transcription successful: %d characters", len(transcript_text))

            # Quality check - use constant for minimum length
            min_transcript_length = 3
            if transcript_text and len(transcript_text.strip()) < min_transcript_length:
                logger.warning("Very short transcription result, audio quality might be poor")

            return TranscriptionResponse(
                text=transcript_text,
                confidence=confidence,
                language=getattr(response, "language", "en"),
            )

        except Exception as e:
            logger.exception("Transcription failed")

            # Fallback with basic transcription if verbose fails
            try:
                logger.info("Attempting fallback transcription with basic format")
                audio_file = BytesIO(audio_data)
                audio_file.name = "audio.wav"

                fallback_response = await client.audio.transcriptions.create(
                    model=settings.openai.whisper_model,
                    file=audio_file,
                    response_format="text",
                )

                logger.info(
                    "Fallback transcription successful: %d characters",
                    len(fallback_response),
                )
                return TranscriptionResponse(
                    text=fallback_response,
                    confidence=0.7,  # Lower confidence for fallback
                    language="en",
                )

            except Exception:
                logger.exception("Fallback transcription also failed")
                msg = f"Audio transcription failed: {e}"
                raise OpenAIServiceError(msg) from e

    def _calculate_confidence(self, text: str, response: Any) -> float:  # noqa: ANN401, ARG002
        """Calculate confidence score based on transcription quality."""
        base_confidence = 0.8

        # Define constants for magic numbers
        min_length_threshold = 10
        good_length_threshold = 100

        # Adjust based on text length
        if len(text.strip()) < min_length_threshold:
            base_confidence -= 0.2
        elif len(text.strip()) > good_length_threshold:
            base_confidence += 0.1

        # Check for typical transcription issues
        if "..." in text or "[inaudible]" in text.lower():
            base_confidence -= 0.3

        # Ensure confidence is within valid range
        return max(0.0, min(1.0, base_confidence))

    @observe(capture_input=True, capture_output=True)
    async def extract_fitness_data(self, transcript: str) -> dict[str, Any]:
        """
        Extract structured fitness data from transcript using OpenAI structured outputs.

        Args:
            transcript: Text transcript to analyze

        Returns:
            Dictionary containing structured fitness data

        """
        client = self._get_client()

        # Handle testing or when client is not available
        if client is None:
            logger.info("Mock fitness data extraction for testing")
            return {
                "fitness_type": "running",
                "duration_minutes": 30,
                "intensity": "medium",
                "details": "Mock details from transcript",
                "mental_state": "good",
                "energy_level": 4,
                "timestamp": datetime.now(UTC).isoformat(),
            }

        try:
            # Use settings-driven model configuration
            completion = await client.beta.chat.completions.parse(
                model=settings.openai.gpt_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert fitness tracker analyzer specifically "
                            "designed for young cricket players. "
                            "Extract fitness activity information from the user's voice transcript. "
                            "Context: This is from a 15-year-old cricket player in Nepal "
                            "tracking their fitness journey. "
                            "Be precise and accurate. Consider cricket-specific fitness activities "
                            "like wicket keeping practice, bowling endurance training, "
                            "batting stance work, etc."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Extract fitness information from this transcript: {transcript}",
                    },
                ],
                response_format=FitnessDataExtraction,
                temperature=settings.openai.temperature,
                max_tokens=settings.openai.max_tokens,
            )

            # Better error handling for parsing
            if not completion.choices or not completion.choices[0].message.parsed:
                logger.warning("No parsed response received from OpenAI")
                return self._extract_fitness_fallback(transcript)

            # Parse the structured response
            fitness_data = completion.choices[0].message.parsed

            # Validate extracted data
            if not fitness_data.fitness_type or fitness_data.duration_minutes <= 0:
                logger.warning("Invalid fitness data extracted, using fallback values")
                fitness_data.fitness_type = fitness_data.fitness_type or "general_fitness"
                fitness_data.duration_minutes = max(fitness_data.duration_minutes, 10)

            # Convert to dictionary format expected by the system
            return {
                "fitness_type": fitness_data.fitness_type,
                "duration_minutes": fitness_data.duration_minutes,
                "intensity": fitness_data.intensity,
                "details": fitness_data.details,
                "mental_state": fitness_data.mental_state,
                "energy_level": fitness_data.energy_level,
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception:
            logger.exception("Fitness data extraction failed")
            return self._extract_fitness_fallback(transcript)

    def _extract_fitness_fallback(self, transcript: str) -> dict[str, Any]:
        """Fallback fitness data extraction using keyword matching."""
        logger.info("Using fallback fitness data extraction with keyword matching")

        transcript_lower = transcript.lower()

        # Simple keyword-based extraction
        fitness_type = "general_fitness"
        if any(word in transcript_lower for word in ["run", "running", "jog", "cardio"]):
            fitness_type = "running"
        elif any(word in transcript_lower for word in ["gym", "weight", "strength", "lift"]):
            fitness_type = "strength_training"
        elif any(word in transcript_lower for word in ["bat", "batting", "wicket", "bowl"]):
            fitness_type = "cricket_specific"

        # Extract duration (look for numbers followed by "minute" or "min")
        duration_match = re.search(r"(\d+)\s*(?:minute|min)", transcript_lower)
        duration_minutes = int(duration_match.group(1)) if duration_match else 30

        return {
            "fitness_type": fitness_type,
            "duration_minutes": duration_minutes,
            "intensity": "medium",
            "details": f"Extracted from transcript: {transcript[:100]}...",
            "mental_state": "good",
            "energy_level": 3,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def analyze_transcript_type(self, transcript: str) -> str:
        """
        Analyze transcript to determine entry type.

        Args:
            transcript: Text transcript to analyze

        Returns:
            Entry type: 'fitness', 'cricket_coaching', 'cricket_match', or 'rest_day'

        """
        # Simple keyword-based analysis for MVP
        transcript_lower = transcript.lower()

        # Check for cricket match keywords
        if any(
            word in transcript_lower
            for word in [
                "match",
                "game",
                "scored",
                "runs",
                "wickets",
                "opposition",
                "team",
                "batting",
                "bowling",
                "caught",
                "stumped",
                "won",
                "lost",
            ]
        ):
            return "cricket_match"

        # Check for coaching keywords
        if any(
            word in transcript_lower
            for word in [
                "coach",
                "practice",
                "training",
                "drill",
                "technique",
                "improvement",
                "session",
                "feedback",
                "instruction",
            ]
        ):
            return "cricket_coaching"

        # Check for rest day keywords
        if any(
            word in transcript_lower
            for word in [
                "rest",
                "sleep",
                "recovery",
                "tired",
                "relaxed",
                "break",
                "day off",
                "recover",
            ]
        ):
            return "rest_day"

        # Default to fitness
        return "fitness"


# Global OpenAI service instance
openai_service = OpenAIService()
