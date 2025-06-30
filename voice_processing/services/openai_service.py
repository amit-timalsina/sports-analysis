"""OpenAI service for transcription and structured data extraction."""

import logging
import os
import re
import subprocess
import tempfile
from datetime import UTC, datetime
from io import BytesIO
from typing import Any

from langfuse import observe  # type: ignore[import-untyped]
from langfuse.openai import AsyncOpenAI

from common.config.settings import settings
from common.exceptions import AppError
from fitness_tracking.schemas.cricket import (
    CricketCoachingDataExtraction,
    CricketMatchDataExtraction,
    RestDayDataExtraction,
)
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

    def _convert_webm_to_wav(self, webm_data: bytes) -> bytes:
        """Convert WebM audio to WAV format using ffmpeg."""
        if len(webm_data) == 0:
            raise OpenAIServiceError("Cannot convert empty WebM data")

        logger.info("Starting WebM to WAV conversion: %d bytes input", len(webm_data))

        try:
            # Create temporary files for input and output
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as input_file:
                input_file.write(webm_data)
                input_file.flush()
                input_path = input_file.name

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as output_file:
                output_path = output_file.name

            try:
                # First, probe the input file to validate it's actually audio
                probe_cmd = [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-print_format",
                    "json",
                    "-show_streams",
                    input_path,
                ]

                try:
                    probe_result = subprocess.run(
                        probe_cmd,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    import json

                    probe_data = json.loads(probe_result.stdout)

                    # Check if there's an audio stream
                    has_audio = any(
                        stream.get("codec_type") == "audio"
                        for stream in probe_data.get("streams", [])
                    )
                    if not has_audio:
                        raise OpenAIServiceError("Input file contains no audio streams")

                    # Log audio info for debugging
                    for stream in probe_data.get("streams", []):
                        if stream.get("codec_type") == "audio":
                            logger.info(
                                "Input audio: codec=%s, sample_rate=%s, channels=%s, duration=%s",
                                stream.get("codec_name", "unknown"),
                                stream.get("sample_rate", "unknown"),
                                stream.get("channels", "unknown"),
                                stream.get("duration", "unknown"),
                            )
                            break

                except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
                    logger.warning("Could not probe input file, proceeding with conversion anyway")

                # Use improved ffmpeg command with better error handling
                cmd = [
                    "ffmpeg",
                    "-i",
                    input_path,
                    "-vn",  # No video
                    "-acodec",
                    "pcm_s16le",  # 16-bit PCM
                    "-ar",
                    "16000",  # 16kHz sample rate
                    "-ac",
                    "1",  # Mono channel
                    "-af",
                    "volume=1.5",  # Boost volume slightly in case it's too quiet
                    "-f",
                    "wav",  # WAV format
                    "-y",  # Overwrite output file
                    "-loglevel",
                    "error",  # Reduce ffmpeg output noise
                    output_path,
                ]

                logger.debug("Running ffmpeg command: %s", " ".join(cmd))
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)

                # Check if output file was created and has content
                if not os.path.exists(output_path):
                    raise OpenAIServiceError("ffmpeg failed to create output file")

                output_size = os.path.getsize(output_path)
                if output_size == 0:
                    raise OpenAIServiceError("ffmpeg created empty output file")

                # Read the converted WAV file
                with open(output_path, "rb") as wav_file:
                    wav_data = wav_file.read()

                # Validate WAV data more thoroughly
                if len(wav_data) < 44:  # WAV header is at least 44 bytes
                    raise OpenAIServiceError(f"Generated WAV file too small: {len(wav_data)} bytes")

                # Check for basic WAV header
                if not wav_data.startswith(b"RIFF") or b"WAVE" not in wav_data[:12]:
                    raise OpenAIServiceError(
                        "Generated file does not appear to be a valid WAV file",
                    )

                # Additional validation: check if file has meaningful audio content
                # WAV files should have data beyond just the header
                if len(wav_data) < 1000:  # Less than 1KB suggests very short or empty audio
                    logger.warning(
                        "Generated WAV file is very small (%d bytes), audio might be too short",
                        len(wav_data),
                    )

                logger.info(
                    "Successfully converted WebM to WAV: %d bytes -> %d bytes",
                    len(webm_data),
                    len(wav_data),
                )
                return wav_data

            finally:
                # Clean up temporary files
                for file_path in [input_path, output_path]:
                    try:
                        if os.path.exists(file_path):
                            os.unlink(file_path)
                    except OSError as cleanup_error:
                        logger.warning(
                            "Failed to cleanup temporary file %s: %s",
                            file_path,
                            cleanup_error,
                        )

        except subprocess.CalledProcessError as e:
            error_msg = f"ffmpeg conversion failed (exit code {e.returncode})"
            if e.stderr:
                error_msg += f": {e.stderr.strip()}"
            logger.error("%s", error_msg)
            raise OpenAIServiceError(error_msg) from e
        except FileNotFoundError as e:
            if "ffmpeg" in str(e) or "ffprobe" in str(e):
                error_msg = "ffmpeg/ffprobe is not installed or not found in PATH. Please install ffmpeg to enable audio conversion."
                logger.error("%s", error_msg)
                raise OpenAIServiceError(error_msg) from e
            raise OpenAIServiceError(f"File operation failed: {e}") from e
        except Exception as e:
            logger.error("Audio conversion error: %s", e)
            raise OpenAIServiceError(f"Audio conversion error: {e}") from e

    @observe(capture_input=False, capture_output=True)
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

        # Check if this looks like WebM data from a browser MediaRecorder
        is_webm_from_browser = audio_data.startswith(b"\x1a\x45\xdf\xa3")

        try:
            # For WebM data from browsers, prioritize conversion to WAV
            # since browser WebM often uses Opus codec which OpenAI may not support well
            if is_webm_from_browser:
                logger.info(
                    "Detected WebM from browser, converting to WAV for better compatibility",
                )
                wav_data = self._convert_webm_to_wav(audio_data)

                # Validate WAV data
                if len(wav_data) == 0:
                    logger.error("WAV conversion resulted in empty data")
                    raise OpenAIServiceError("Audio conversion failed: empty output")

                # Create file-like object with WAV data
                audio_file = BytesIO(wav_data)
                audio_file.name = "audio.wav"

                # Use settings-driven configuration for Whisper
                prompt = (
                    "This is cricket and fitness related voice data from a young athlete in Nepal."
                )
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
                confidence = self._calculate_confidence(transcript_text, response)

                logger.info(
                    "WAV transcription successful: %d characters, language: %s",
                    len(transcript_text),
                    getattr(response, "language", "unknown"),
                )

                return TranscriptionResponse(
                    text=transcript_text,
                    confidence=confidence,
                    language=getattr(response, "language", "en"),
                )

            # For non-WebM audio, try direct transcription first
            logger.info("Attempting transcription with original format")
            audio_file = BytesIO(audio_data)
            audio_file.name = "audio.webm"  # Default to webm for unknown formats

            prompt = "This is cricket and fitness related voice data from a young athlete in Nepal."
            response = await client.audio.transcriptions.create(
                model=settings.openai.whisper_model,
                file=audio_file,
                language="en",  # English for cricket/fitness context
                response_format="verbose_json",  # Get detailed response
                temperature=settings.openai.temperature,
                prompt=prompt,
            )

            transcript_text = response.text
            confidence = self._calculate_confidence(transcript_text, response)

            logger.info(
                "Direct transcription successful: %d characters, language: %s",
                len(transcript_text),
                getattr(response, "language", "unknown"),
            )

            return TranscriptionResponse(
                text=transcript_text,
                confidence=confidence,
                language=getattr(response, "language", "en"),
            )

        except Exception as e:
            logger.warning("Primary transcription method failed: %s", e)

            # Fallback: Try WAV conversion if not already tried
            if not is_webm_from_browser:
                try:
                    logger.info("Attempting fallback: Converting to WAV format")
                    wav_data = self._convert_webm_to_wav(audio_data)

                    # Validate WAV data
                    if len(wav_data) == 0:
                        logger.error("WAV conversion resulted in empty data")
                        raise OpenAIServiceError("Audio conversion failed: empty output")

                    # Create file-like object with WAV data
                    audio_file = BytesIO(wav_data)
                    audio_file.name = "audio.wav"

                    response = await client.audio.transcriptions.create(
                        model=settings.openai.whisper_model,
                        file=audio_file,
                        language="en",  # English for cricket/fitness context
                        response_format="verbose_json",  # Get detailed response
                        temperature=settings.openai.temperature,
                        prompt="This is cricket and fitness related voice data from a young athlete in Nepal.",
                    )

                    transcript_text = response.text
                    confidence = self._calculate_confidence(transcript_text, response)

                    logger.info(
                        "Fallback WAV transcription successful: %d characters",
                        len(transcript_text),
                    )

                    return TranscriptionResponse(
                        text=transcript_text,
                        confidence=confidence,
                        language=getattr(response, "language", "en"),
                    )

                except Exception:
                    logger.exception("WAV conversion transcription also failed")

            # Final fallback: Try with basic text format
            try:
                logger.info("Final fallback: Attempting basic text format transcription")
                audio_file = BytesIO(audio_data)
                audio_file.name = "audio.webm"

                fallback_response = await client.audio.transcriptions.create(
                    model=settings.openai.whisper_model,
                    file=audio_file,
                    response_format="text",
                    language="en",
                )

                logger.info(
                    "Basic format transcription successful: %d characters",
                    len(fallback_response),
                )
                return TranscriptionResponse(
                    text=fallback_response,
                    confidence=0.6,  # Lower confidence for basic fallback
                    language="en",
                )

            except Exception:
                logger.exception("All transcription methods failed")
                msg = f"Audio transcription failed after trying all formats. Original error: {e}"
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
            # Use settings-driven model configuration with structured outputs
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
                            "Be precise and accurate. The schema will enforce valid values automatically."
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

            # Parse the structured response - schema validation is automatic
            fitness_data = completion.choices[0].message.parsed

            # Convert to dictionary format expected by the system
            return {
                "fitness_type": fitness_data.fitness_type,
                "duration_minutes": fitness_data.duration_minutes,
                "intensity": fitness_data.intensity,
                "details": fitness_data.details,
                "mental_state": fitness_data.mental_state,
                "energy_level": fitness_data.energy_level,
                "distance_km": fitness_data.distance_km,
                "calories_burned": fitness_data.calories_burned,
                "location": fitness_data.location,
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

    async def extract_cricket_coaching_data(self, transcript: str) -> dict[str, Any]:
        """Extract structured cricket coaching data from transcript."""
        client = self._get_client()

        if client is None:
            logger.info("Mock cricket coaching data extraction for testing")
            return {
                "session_type": "batting_drills",
                "duration_minutes": 60,
                "what_went_well": "Mock batting technique improvements",
                "areas_for_improvement": "Mock footwork needs work",
                "skills_practiced": "front foot drives, pull shots",
                "self_assessment_score": 7,
                "confidence_level": 7,
                "focus_level": 8,
                "mental_state": "good",
            }

        try:
            completion = await client.beta.chat.completions.parse(
                model=settings.openai.gpt_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert cricket coaching analyst for a 15-year-old "
                            "cricket player in Nepal. Extract cricket coaching session information "
                            "from the user's voice transcript. Focus on batting drills, "
                            "wicket keeping practice, technical skills, and performance feedback."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Extract cricket coaching session information: {transcript}",
                    },
                ],
                response_format=CricketCoachingDataExtraction,
                temperature=settings.openai.temperature,
                max_tokens=settings.openai.max_tokens,
            )

            if not completion.choices or not completion.choices[0].message.parsed:
                return self._extract_cricket_coaching_fallback(transcript)

            coaching_data = completion.choices[0].message.parsed
            return {
                "session_type": coaching_data.session_type,
                "duration_minutes": coaching_data.duration_minutes,
                "what_went_well": coaching_data.what_went_well,
                "areas_for_improvement": coaching_data.areas_for_improvement,
                "skills_practiced": coaching_data.skills_practiced,
                "self_assessment_score": coaching_data.self_assessment_score,
                "confidence_level": coaching_data.confidence_level,
                "focus_level": coaching_data.focus_level,
                "mental_state": coaching_data.mental_state,
                "coach_feedback": coaching_data.coach_feedback,
                "difficulty_level": coaching_data.difficulty_level,
                "learning_satisfaction": coaching_data.learning_satisfaction,
            }

        except Exception:
            logger.exception("Cricket coaching data extraction failed")
            return self._extract_cricket_coaching_fallback(transcript)

    def _extract_cricket_coaching_fallback(self, transcript: str) -> dict[str, Any]:
        """Fallback cricket coaching data extraction."""
        transcript_lower = transcript.lower()

        session_type = "batting_drills"
        if "keeping" in transcript_lower:
            session_type = "wicket_keeping"
        elif "net" in transcript_lower:
            session_type = "netting"

        duration_match = re.search(r"(\d+)\s*(?:minute|min|hour)", transcript_lower)
        duration = int(duration_match.group(1)) if duration_match else 60

        return {
            "session_type": session_type,
            "duration_minutes": duration,
            "what_went_well": f"Extracted from transcript: {transcript[:100]}...",
            "areas_for_improvement": "Need to analyze further",
            "skills_practiced": "General cricket skills",
            "self_assessment_score": 7,
            "confidence_level": 7,
            "focus_level": 7,
            "mental_state": "good",
        }

    async def extract_cricket_match_data(self, transcript: str) -> dict[str, Any]:
        """Extract structured cricket match data from transcript."""
        client = self._get_client()

        if client is None:
            return {
                "match_type": "school",
                "opposition_strength": 6,
                "pre_match_nerves": 5,
                "post_match_satisfaction": 7,
                "mental_state": "good",
                "runs_scored": 25,
                "balls_faced": 30,
                "boundaries_4s": 3,
                "boundaries_6s": 0,
            }

        try:
            completion = await client.beta.chat.completions.parse(
                model=settings.openai.gpt_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert cricket match analyst for a 15-year-old "
                            "cricket player in Nepal. Extract match performance data "
                            "including batting stats, wicket keeping performance, and mental state."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Extract cricket match performance data: {transcript}",
                    },
                ],
                response_format=CricketMatchDataExtraction,
                temperature=settings.openai.temperature,
                max_tokens=settings.openai.max_tokens,
            )

            if not completion.choices or not completion.choices[0].message.parsed:
                return self._extract_cricket_match_fallback(transcript)

            match_data = completion.choices[0].message.parsed
            return {
                "match_type": match_data.match_type,
                "opposition_strength": match_data.opposition_strength,
                "pre_match_nerves": match_data.pre_match_nerves,
                "post_match_satisfaction": match_data.post_match_satisfaction,
                "mental_state": match_data.mental_state,
                "runs_scored": match_data.runs_scored,
                "balls_faced": match_data.balls_faced,
                "boundaries_4s": match_data.boundaries_4s,
                "boundaries_6s": match_data.boundaries_6s,
                "how_out": match_data.how_out,
                "key_shots_played": match_data.key_shots_played,
                "catches_taken": match_data.catches_taken,
                "catches_dropped": match_data.catches_dropped,
                "stumpings": match_data.stumpings,
            }

        except Exception:
            logger.exception("Cricket match data extraction failed")
            return self._extract_cricket_match_fallback(transcript)

    def _extract_cricket_match_fallback(self, transcript: str) -> dict[str, Any]:
        """Fallback cricket match data extraction."""
        transcript_lower = transcript.lower()

        match_type = "school"
        if "tournament" in transcript_lower:
            match_type = "tournament"
        elif "practice" in transcript_lower:
            match_type = "practice"

        runs_match = re.search(r"(\d+)\s*(?:run|runs)", transcript_lower)
        runs = int(runs_match.group(1)) if runs_match else None

        return {
            "match_type": match_type,
            "opposition_strength": 6,
            "pre_match_nerves": 5,
            "post_match_satisfaction": 7,
            "mental_state": "good",
            "runs_scored": runs,
            "balls_faced": None,
            "boundaries_4s": None,
            "boundaries_6s": None,
        }

    async def extract_rest_day_data(self, transcript: str) -> dict[str, Any]:
        """Extract structured rest day data from transcript."""
        client = self._get_client()

        if client is None:
            return {
                "rest_type": "complete_rest",
                "physical_state": "feeling good and recovered",
                "fatigue_level": 3,
                "energy_level": 7,
                "motivation_level": 8,
                "mood_description": "relaxed and positive",
                "mental_state": "good",
            }

        try:
            completion = await client.beta.chat.completions.parse(
                model=settings.openai.gpt_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert recovery and wellness analyst for a 15-year-old "
                            "cricket player in Nepal. Extract rest day information including "
                            "physical state, mental state, and recovery activities."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Extract rest day information: {transcript}",
                    },
                ],
                response_format=RestDayDataExtraction,
                temperature=settings.openai.temperature,
                max_tokens=settings.openai.max_tokens,
            )

            if not completion.choices or not completion.choices[0].message.parsed:
                return self._extract_rest_day_fallback(transcript)

            rest_data = completion.choices[0].message.parsed
            return {
                "rest_type": rest_data.rest_type,
                "physical_state": rest_data.physical_state,
                "fatigue_level": rest_data.fatigue_level,
                "energy_level": rest_data.energy_level,
                "motivation_level": rest_data.motivation_level,
                "mood_description": rest_data.mood_description,
                "mental_state": rest_data.mental_state,
                "soreness_level": rest_data.soreness_level,
                "training_reflections": rest_data.training_reflections,
                "goals_concerns": rest_data.goals_concerns,
                "recovery_activities": rest_data.recovery_activities,
            }

        except Exception:
            logger.exception("Rest day data extraction failed")
            return self._extract_rest_day_fallback(transcript)

    def _extract_rest_day_fallback(self, transcript: str) -> dict[str, Any]:
        """Fallback rest day data extraction."""
        transcript_lower = transcript.lower()

        rest_type = "complete_rest"
        if "active" in transcript_lower:
            rest_type = "active_recovery"
        elif "injury" in transcript_lower:
            rest_type = "injury_recovery"

        return {
            "rest_type": rest_type,
            "physical_state": f"Extracted from transcript: {transcript[:100]}...",
            "fatigue_level": 5,
            "energy_level": 6,
            "motivation_level": 7,
            "mood_description": "relaxed",
            "mental_state": "good",
        }


# Global OpenAI service instance
openai_service = OpenAIService()
