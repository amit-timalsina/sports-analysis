"""Conversation service for managing multi-turn voice interactions."""

import logging
from datetime import datetime
from typing import Any

from langfuse import observe
from langfuse.openai import AsyncOpenAI

from common.config.settings import settings
from common.exceptions import AppError
from voice_processing.schemas.conversation import (
    ActivityType,
    ConversationAnalysis,
    ConversationContext,
    ConversationResult,
    ConversationState,
    DataCompleteness,
    FollowUpQuestion,
)

logger = logging.getLogger(__name__)


class ConversationServiceError(AppError):
    """Conversation service specific error."""

    status_code = 500
    detail = "Conversation service operation failed"


class ConversationService:
    """Service for managing multi-turn voice conversations with OpenAI."""

    def __init__(self) -> None:
        """Initialize conversation service."""
        self._client: AsyncOpenAI | None = None
        self.active_conversations: dict[str, ConversationContext] = {}
        self.max_turns = 8  # Maximum conversation turns before forcing completion

        # Define required and optional fields for each activity type
        self.required_fields = {
            ActivityType.FITNESS: [
                "fitness_type",
                "duration_minutes",
                "intensity",
                "mental_state",
                "energy_level",
            ],
            ActivityType.CRICKET_COACHING: [
                "session_type",
                "duration_minutes",
                "what_went_well",
                "areas_for_improvement",
                "self_assessment_score",
                "confidence_level",
                "focus_level",
                "learning_satisfaction",
                "mental_state",
            ],
            ActivityType.CRICKET_MATCH: [
                "match_type",
                "opposition_strength",
                "pre_match_nerves",
                "post_match_satisfaction",
                "mental_state",
            ],
            ActivityType.REST_DAY: [
                "rest_type",
                "physical_state",
                "fatigue_level",
                "energy_level",
                "motivation_level",
                "mood_description",
                "mental_state",
            ],
        }

        self.optional_fields = {
            ActivityType.FITNESS: [
                "details",
                "distance_km",
                "location",
                "notes",
            ],
            ActivityType.CRICKET_COACHING: [
                "coach_feedback",
                "skills_practiced",
                "difficulty_level",
                "notes",
            ],
            ActivityType.CRICKET_MATCH: [
                "runs_scored",
                "balls_faced",
                "boundaries_4s",
                "boundaries_6s",
                "how_out",
                "key_shots_played",
                "catches_taken",
                "catches_dropped",
                "stumpings",
                "notes",
            ],
            ActivityType.REST_DAY: [
                "soreness_level",
                "training_reflections",
                "goals_concerns",
                "recovery_activities",
                "notes",
            ],
        }

    def _get_client(self) -> AsyncOpenAI | None:
        """Get OpenAI client, initializing if needed."""
        if self._client is None:
            if settings.app.is_testing or not settings.openai.api_key:
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

    def start_conversation(
        self,
        session_id: str,
        user_id: str,
        activity_type: ActivityType,
    ) -> ConversationContext:
        """Start a new conversation session."""
        context = ConversationContext(
            session_id=session_id,
            user_id=user_id,
            activity_type=activity_type,
            state=ConversationState.STARTED,
        )

        self.active_conversations[session_id] = context
        logger.info("Started conversation for session %s, activity: %s", session_id, activity_type)

        return context

    def get_conversation(self, session_id: str) -> ConversationContext | None:
        """Get existing conversation context."""
        return self.active_conversations.get(session_id)

    async def process_user_input(
        self,
        session_id: str,
        user_input: str,
        transcript_confidence: float = 0.9,
    ) -> ConversationAnalysis:
        """
        Process user input and return conversation analysis.

        Args:
            session_id: Unique session identifier
            user_input: User's voice input (transcript)
            transcript_confidence: Confidence score from speech-to-text

        Returns:
            ConversationAnalysis with next steps for the conversation

        """
        context = self.get_conversation(session_id)
        if not context:
            raise ConversationServiceError(f"No active conversation for session {session_id}")

        logger.info(
            "Processing input for session %s (turn %d): %s",
            session_id,
            context.turn_count + 1,
            user_input[:100],
        )

        # Increment turn count and add transcript to history
        context.turn_count += 1

        # **NEW**: Track all transcripts with turn information
        if not hasattr(context, "transcript_history"):
            context.transcript_history = []

        context.transcript_history.append(
            {
                "turn": context.turn_count,
                "transcript": user_input,
                "confidence": transcript_confidence,
            },
        )

        # Extract new data from user input
        extracted_data = await self._extract_data_from_input(
            user_input=user_input,
            activity_type=context.activity_type,
            existing_data=context.collected_data,
        )

        # Update collected data with new extractions
        context.collected_data.update(extracted_data)

        # Analyze data completeness
        data_completeness = self._analyze_data_completeness(
            context.collected_data,
            context.activity_type,
            transcript_confidence,
        )

        # Determine if we should ask follow-up questions
        should_continue = not data_completeness.is_complete and context.turn_count < self.max_turns

        # Generate follow-up question if needed
        next_question = None
        if should_continue and data_completeness.missing_fields:
            next_question = await self._generate_follow_up_question(
                context.collected_data,
                context.activity_type,
                data_completeness.missing_fields,
            )

        # Create analysis result
        analysis = ConversationAnalysis(
            data_completeness=data_completeness,
            next_question=next_question,
            should_continue=should_continue,
            can_generate_final_output=data_completeness.is_complete
            or context.turn_count >= self.max_turns,
            analysis_confidence=data_completeness.confidence_score,
            reasoning=f"Turn {context.turn_count}: {'Complete' if data_completeness.is_complete else f'Missing {len(data_completeness.missing_fields)} fields'}",
        )

        logger.info(
            "Analysis for session %s: continue=%s, complete=%s, missing_fields=%s",
            session_id,
            analysis.should_continue,
            analysis.can_generate_final_output,
            data_completeness.missing_fields,
        )

        return analysis

    @observe(capture_input=True, capture_output=True)
    async def _extract_data_from_input(
        self,
        user_input: str,
        activity_type: ActivityType,
        existing_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Extract structured data from user input using OpenAI."""
        client = self._get_client()

        if client is None:
            # Mock response for testing
            return {
                "mock_field": "mock_value",
                "extracted_from": user_input[:50],
            }

        try:
            # For fitness data, use structured outputs with schema validation
            if activity_type == ActivityType.FITNESS:
                # Import the schema here to avoid circular imports
                from fitness_tracking.schemas.fitness import FitnessDataExtraction

                system_prompt = """You are an expert fitness tracker analyzer for young cricket players.

CRITICAL: You MUST extract fitness data and return it in the EXACT format specified by the schema.

For fitness_type, you MUST use EXACTLY one of these values:
- "running" (for jog, jogging, run, sprint, etc.)
- "strength_training" (for gym, weights, lifting, etc.) 
- "cricket_specific" (for cricket training, cricket fitness)
- "cardio" (for cardiovascular, aerobic, cycling, swimming)
- "flexibility" (for stretching, yoga, pilates)
- "general_fitness" (for general workout, exercise, fitness)

For intensity, you MUST use EXACTLY one of: "low", "medium", "high"

Map similar terms to the allowed values. Extract only information explicitly mentioned."""

                completion = await client.beta.chat.completions.parse(
                    model=settings.openai.gpt_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Extract fitness data from: {user_input}"},
                    ],
                    response_format=FitnessDataExtraction,
                    temperature=0.1,  # Low temperature for consistent extraction
                    max_tokens=500,
                )

                # Enhanced error handling for parsing
                if not completion.choices:
                    logger.warning("No choices in OpenAI response for fitness extraction")
                    return self._fallback_extraction(user_input, activity_type)

                choice = completion.choices[0]
                if not choice.message.parsed:
                    logger.warning("No parsed response received from OpenAI for fitness")
                    if choice.message.refusal:
                        logger.warning(
                            "OpenAI refused to parse fitness data: %s",
                            choice.message.refusal,
                        )
                    return self._fallback_extraction(user_input, activity_type)

                # Parse the structured response - schema validation is automatic via Pydantic
                fitness_data = choice.message.parsed

                # Convert to dictionary and filter for only fields mentioned in input
                extracted_data = {}
                if fitness_data.fitness_type:
                    extracted_data["fitness_type"] = fitness_data.fitness_type
                if fitness_data.duration_minutes:
                    extracted_data["duration_minutes"] = fitness_data.duration_minutes
                if fitness_data.intensity:
                    extracted_data["intensity"] = fitness_data.intensity
                if fitness_data.details:
                    extracted_data["details"] = fitness_data.details
                if fitness_data.mental_state:
                    extracted_data["mental_state"] = fitness_data.mental_state
                if fitness_data.energy_level:
                    extracted_data["energy_level"] = fitness_data.energy_level
                if fitness_data.distance_km:
                    extracted_data["distance_km"] = fitness_data.distance_km
                if fitness_data.location:
                    extracted_data["location"] = fitness_data.location

                logger.info("Extracted structured fitness data: %s", list(extracted_data.keys()))
                return extracted_data

            # For cricket match activities, use structured outputs
            if activity_type == ActivityType.CRICKET_MATCH:
                from fitness_tracking.schemas.cricket import CricketMatchDataExtraction

                system_prompt = """You are an expert cricket match analyzer for young cricket players.

CRITICAL: You MUST extract cricket match data and return it in the EXACT format specified by the schema.

IMPORTANT MAPPINGS - Use descriptive terms, repository will normalize:
- For opposition_strength: Use terms like "very weak", "weak", "easy", "average", "strong", "tough", "very strong"
- For pre_match_nerves: Use terms like "very nervous", "nervous", "confident", "very confident", "excited"  
- For post_match_satisfaction: Use terms like "disappointed", "not satisfied", "satisfied", "very satisfied"
- For match_type: Use "tournament" for ODI/T20/competitive matches, "practice" for friendly matches

Extract only information explicitly mentioned. Use null for missing data."""

                logger.info(f"🏏 Extracting cricket match data from: '{user_input}'")
                logger.info(f"🏏 Using system prompt: {system_prompt[:200]}...")

                completion = await client.beta.chat.completions.parse(
                    model=settings.openai.gpt_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": f"Extract cricket match data from: {user_input}",
                        },
                    ],
                    response_format=CricketMatchDataExtraction,
                    temperature=0.1,
                    max_tokens=500,
                )

                logger.info(
                    f"🏏 OpenAI completion response received, choices: {len(completion.choices)}",
                )

                if not completion.choices:
                    logger.warning("No choices in OpenAI response for cricket match extraction")
                    return self._fallback_extraction(user_input, activity_type)

                choice = completion.choices[0]
                logger.info(f"🏏 Choice message parsed: {choice.message.parsed is not None}")
                logger.info(f"🏏 Choice message refusal: {choice.message.refusal}")

                if not choice.message.parsed:
                    logger.warning("No parsed response received from OpenAI for cricket match")
                    if choice.message.refusal:
                        logger.warning(
                            "OpenAI refused to parse cricket match data: %s",
                            choice.message.refusal,
                        )
                    return self._fallback_extraction(user_input, activity_type)

                cricket_data = choice.message.parsed
                logger.info(f"🏏 Raw cricket_data object: {cricket_data}")
                logger.info(
                    f"🏏 cricket_data.match_type: {getattr(cricket_data, 'match_type', 'NOT_SET')}",
                )
                logger.info(
                    f"🏏 cricket_data.runs_scored: {getattr(cricket_data, 'runs_scored', 'NOT_SET')}",
                )
                logger.info(
                    f"🏏 cricket_data.balls_faced: {getattr(cricket_data, 'balls_faced', 'NOT_SET')}",
                )

                extracted_data = {}

                # Add all non-null fields
                if cricket_data.match_type:
                    extracted_data["match_type"] = cricket_data.match_type
                    logger.info(f"🏏 Added match_type: {cricket_data.match_type}")
                if cricket_data.opposition_strength:
                    extracted_data["opposition_strength"] = cricket_data.opposition_strength
                    logger.info(f"🏏 Added opposition_strength: {cricket_data.opposition_strength}")
                if cricket_data.runs_scored is not None:
                    extracted_data["runs_scored"] = cricket_data.runs_scored
                    logger.info(f"🏏 Added runs_scored: {cricket_data.runs_scored}")
                if cricket_data.balls_faced is not None:
                    extracted_data["balls_faced"] = cricket_data.balls_faced
                    logger.info(f"🏏 Added balls_faced: {cricket_data.balls_faced}")
                if cricket_data.boundaries_4s is not None:
                    extracted_data["boundaries_4s"] = cricket_data.boundaries_4s
                    logger.info(f"🏏 Added boundaries_4s: {cricket_data.boundaries_4s}")
                if cricket_data.boundaries_6s is not None:
                    extracted_data["boundaries_6s"] = cricket_data.boundaries_6s
                    logger.info(f"🏏 Added boundaries_6s: {cricket_data.boundaries_6s}")
                if cricket_data.how_out:
                    extracted_data["how_out"] = cricket_data.how_out
                if cricket_data.key_shots_played:
                    extracted_data["key_shots_played"] = cricket_data.key_shots_played
                if cricket_data.catches_taken is not None:
                    extracted_data["catches_taken"] = cricket_data.catches_taken
                if cricket_data.catches_dropped is not None:
                    extracted_data["catches_dropped"] = cricket_data.catches_dropped
                if cricket_data.stumpings is not None:
                    extracted_data["stumpings"] = cricket_data.stumpings
                if cricket_data.pre_match_nerves:
                    extracted_data["pre_match_nerves"] = cricket_data.pre_match_nerves
                if cricket_data.post_match_satisfaction:
                    extracted_data["post_match_satisfaction"] = cricket_data.post_match_satisfaction
                if cricket_data.mental_state:
                    extracted_data["mental_state"] = cricket_data.mental_state
                if cricket_data.notes:
                    extracted_data["notes"] = cricket_data.notes

                logger.info(f"🏏 Final extracted_data: {extracted_data}")
                logger.info(
                    "Extracted structured cricket match data: %s",
                    list(extracted_data.keys()),
                )

                # Filter out 'null' string values - these represent missing data
                filtered_data = {
                    k: v for k, v in extracted_data.items() if v != "null" and v is not None
                }
                logger.info(f"🏏 Filtered data (removing 'null' values): {filtered_data}")

                return filtered_data

            # For cricket coaching activities, use structured outputs
            if activity_type == ActivityType.CRICKET_COACHING:
                from fitness_tracking.schemas.cricket import CricketCoachingDataExtraction

                system_prompt = """You are an expert cricket coaching session analyzer for young cricket players.

CRITICAL: You MUST extract cricket coaching data and return it in the EXACT format specified by the schema.

IMPORTANT MAPPINGS - Use descriptive terms, repository will normalize:
- For confidence_level: Use terms like "very low", "low", "confident", "very confident"
- For focus_level: Use terms like "distracted", "okay", "focused", "very focused"
- For self_rating: Use terms like "poor", "below average", "good", "excellent"

Extract only information explicitly mentioned. Use null for missing data."""

                completion = await client.beta.chat.completions.parse(
                    model=settings.openai.gpt_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": f"Extract cricket coaching data from: {user_input}",
                        },
                    ],
                    response_format=CricketCoachingDataExtraction,
                    temperature=0.1,
                    max_tokens=500,
                )

                if not completion.choices:
                    logger.warning("No choices in OpenAI response for cricket coaching extraction")
                    return self._fallback_extraction(user_input, activity_type)

                choice = completion.choices[0]
                if not choice.message.parsed:
                    logger.warning("No parsed response received from OpenAI for cricket coaching")
                    if choice.message.refusal:
                        logger.warning(
                            "OpenAI refused to parse cricket coaching data: %s",
                            choice.message.refusal,
                        )
                    return self._fallback_extraction(user_input, activity_type)

                coaching_data = choice.message.parsed
                extracted_data = {}

                # Add all non-null fields
                if coaching_data.session_type:
                    extracted_data["session_type"] = coaching_data.session_type
                if coaching_data.duration_minutes is not None:
                    extracted_data["duration_minutes"] = coaching_data.duration_minutes
                if coaching_data.what_went_well:
                    extracted_data["what_went_well"] = coaching_data.what_went_well
                if coaching_data.areas_for_improvement:
                    extracted_data["areas_for_improvement"] = coaching_data.areas_for_improvement
                if coaching_data.skills_practiced:
                    extracted_data["skills_practiced"] = coaching_data.skills_practiced
                if coaching_data.self_assessment_score:
                    extracted_data["self_assessment_score"] = coaching_data.self_assessment_score
                if coaching_data.confidence_level:
                    extracted_data["confidence_level"] = coaching_data.confidence_level
                if coaching_data.focus_level:
                    extracted_data["focus_level"] = coaching_data.focus_level
                if coaching_data.mental_state:
                    extracted_data["mental_state"] = coaching_data.mental_state
                if coaching_data.coach_feedback:
                    extracted_data["coach_feedback"] = coaching_data.coach_feedback
                if coaching_data.difficulty_level:
                    extracted_data["difficulty_level"] = coaching_data.difficulty_level
                if coaching_data.learning_satisfaction:
                    extracted_data["learning_satisfaction"] = coaching_data.learning_satisfaction
                if coaching_data.notes:
                    extracted_data["notes"] = coaching_data.notes

                logger.info(
                    "Extracted structured cricket coaching data: %s",
                    list(extracted_data.keys()),
                )

                # Filter out 'null' string values - these represent missing data
                filtered_data = {
                    k: v for k, v in extracted_data.items() if v != "null" and v is not None
                }
                logger.info(f"🏏 Filtered coaching data (removing 'null' values): {filtered_data}")

                return filtered_data

            # For rest day activities, use structured outputs
            if activity_type == ActivityType.REST_DAY:
                from fitness_tracking.schemas.cricket import RestDayDataExtraction

                system_prompt = """You are an expert rest day analyzer for young cricket players.

CRITICAL: You MUST extract rest day data and return it in the EXACT format specified by the schema.

IMPORTANT MAPPINGS - Use descriptive terms, repository will normalize:
- For fatigue_level: Use terms like "exhausted", "tired", "okay", "fresh", "energetic"
- For energy_level: Use terms like "very low", "low", "average", "high", "very high"
- For motivation_level: Use terms like "unmotivated", "low", "motivated", "very motivated"
- For soreness_level: Use terms like "very sore", "sore", "a bit sore", "fine"

Extract only information explicitly mentioned. Use null for missing data."""

                completion = await client.beta.chat.completions.parse(
                    model=settings.openai.gpt_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Extract rest day data from: {user_input}"},
                    ],
                    response_format=RestDayDataExtraction,
                    temperature=0.1,
                    max_tokens=500,
                )

                if not completion.choices:
                    logger.warning("No choices in OpenAI response for rest day extraction")
                    return self._fallback_extraction(user_input, activity_type)

                choice = completion.choices[0]
                if not choice.message.parsed:
                    logger.warning("No parsed response received from OpenAI for rest day")
                    if choice.message.refusal:
                        logger.warning(
                            "OpenAI refused to parse rest day data: %s",
                            choice.message.refusal,
                        )
                    return self._fallback_extraction(user_input, activity_type)

                rest_data = choice.message.parsed
                extracted_data = {}

                # Add all non-null fields
                if rest_data.rest_type:
                    extracted_data["rest_type"] = rest_data.rest_type
                if rest_data.physical_state:
                    extracted_data["physical_state"] = rest_data.physical_state
                if rest_data.fatigue_level:
                    extracted_data["fatigue_level"] = rest_data.fatigue_level
                if rest_data.energy_level:
                    extracted_data["energy_level"] = rest_data.energy_level
                if rest_data.motivation_level:
                    extracted_data["motivation_level"] = rest_data.motivation_level
                if rest_data.mood_description:
                    extracted_data["mood_description"] = rest_data.mood_description
                if rest_data.mental_state:
                    extracted_data["mental_state"] = rest_data.mental_state
                if rest_data.soreness_level:
                    extracted_data["soreness_level"] = rest_data.soreness_level
                if rest_data.training_reflections:
                    extracted_data["training_reflections"] = rest_data.training_reflections
                if rest_data.goals_concerns:
                    extracted_data["goals_concerns"] = rest_data.goals_concerns
                if rest_data.recovery_activities:
                    extracted_data["recovery_activities"] = rest_data.recovery_activities
                if rest_data.notes:
                    extracted_data["notes"] = rest_data.notes

                logger.info("Extracted structured rest day data: %s", list(extracted_data.keys()))

                # Filter out 'null' string values - these represent missing data
                filtered_data = {
                    k: v for k, v in extracted_data.items() if v != "null" and v is not None
                }
                logger.info(f"😴 Filtered rest day data (removing 'null' values): {filtered_data}")

                return filtered_data

            # All activity types now use structured outputs - no fallback needed
            logger.error(f"Unknown activity type: {activity_type}")
            return self._fallback_extraction(user_input, activity_type)

        except Exception as e:
            logger.exception("Failed to extract data from input: %s", e)
            # Fallback: try simple keyword extraction
            return self._fallback_extraction(user_input, activity_type)

    def _fallback_extraction(
        self,
        user_input: str,
        activity_type: ActivityType,
    ) -> dict[str, Any]:
        """Simple keyword-based extraction as fallback with guaranteed valid values."""
        # Defensive programming: handle both enum and string values
        if isinstance(activity_type, str):
            logger.warning(
                "activity_type received as string '%s', converting to enum",
                activity_type,
            )
            try:
                activity_type = ActivityType(activity_type)
            except ValueError:
                logger.error("Invalid activity_type string: %s", activity_type)
                # Fallback to a default
                activity_type = ActivityType.FITNESS

        extracted = {}
        user_lower = user_input.lower()

        # Simple pattern matching based on activity type
        if activity_type == ActivityType.FITNESS:
            # Ensure we return only valid FitnessType enum values
            fitness_type = "general_fitness"  # Safe default
            if any(word in user_lower for word in ["run", "running", "jog", "jogging", "sprint"]):
                fitness_type = "running"
            elif any(
                word in user_lower
                for word in ["gym", "weight", "weights", "lift", "lifting", "strength"]
            ):
                fitness_type = "strength_training"
            elif any(
                word in user_lower for word in ["cricket", "bat", "batting", "wicket", "bowl"]
            ):
                fitness_type = "cricket_specific"
            elif any(
                word in user_lower
                for word in ["cardio", "cardiovascular", "cycle", "cycling", "swim"]
            ):
                fitness_type = "cardio"
            elif any(
                word in user_lower
                for word in ["stretch", "stretching", "yoga", "flexibility", "pilates"]
            ):
                fitness_type = "flexibility"

            extracted["fitness_type"] = fitness_type

            # Extract duration with validation
            import re

            duration_match = re.search(r"(\d+)\s*(?:minutes?|mins?)", user_lower)
            if duration_match:
                duration = int(duration_match.group(1))
                extracted["duration_minutes"] = max(1, min(300, duration))  # Ensure valid range

            # Extract intensity with validation - ensure only valid values
            intensity = "medium"  # Safe default
            if any(
                word in user_lower for word in ["intense", "hard", "tough", "high", "difficult"]
            ):
                intensity = "high"
            elif any(word in user_lower for word in ["easy", "light", "gentle", "low"]):
                intensity = "low"
            extracted["intensity"] = intensity

            # Extract energy level if mentioned
            energy_match = re.search(r"(?:energy|level)\s*(?:was|is|felt)?\s*(\d+)", user_lower)
            if energy_match:
                energy = int(energy_match.group(1))
                extracted["energy_level"] = max(1, min(5, energy))  # Ensure 1-5 range

        extracted["details"] = user_input  # Always capture the full input
        return extracted

    def _analyze_data_completeness(
        self,
        collected_data: dict[str, Any],
        activity_type: ActivityType,
        transcript_confidence: float,
    ) -> DataCompleteness:
        """Analyze how complete the collected data is."""
        # Defensive programming: handle both enum and string values
        if isinstance(activity_type, str):
            logger.warning(
                "activity_type received as string '%s', converting to enum",
                activity_type,
            )
            try:
                activity_type = ActivityType(activity_type)
            except ValueError:
                logger.exception("Invalid activity_type string")
                # Fallback to a default
                activity_type = ActivityType.FITNESS

        required = self.required_fields.get(activity_type, [])
        optional = self.optional_fields.get(activity_type, [])

        # Check required fields
        missing_required = [field for field in required if field not in collected_data]
        missing_optional = [field for field in optional if field not in collected_data]

        # Calculate completeness score
        required_score = (
            (len(required) - len(missing_required)) / len(required) if required else 1.0
        )
        optional_score = (
            (len(optional) - len(missing_optional)) / len(optional) if optional else 1.0
        )

        # Weighted score (required fields are more important)
        completeness_score = (required_score * 0.8) + (optional_score * 0.2)

        # Confidence based on transcript quality and data completeness
        confidence = min(transcript_confidence, completeness_score * 1.2)

        # Determine if complete (all required fields present)
        is_complete = len(missing_required) == 0

        return DataCompleteness(
            is_complete=is_complete,
            completeness_score=completeness_score,
            missing_fields=missing_required + missing_optional[:2],  # Top 2 optional
            confidence_score=confidence,
            next_question_priority="high" if missing_required else "medium",
        )

    @observe(capture_input=True, capture_output=True)
    async def _generate_follow_up_question(
        self,
        collected_data: dict[str, Any],
        activity_type: ActivityType,
        missing_fields: list[str],
    ) -> FollowUpQuestion | None:
        """Generate a contextual follow-up question using OpenAI."""
        if not missing_fields:
            return None

        # Defensive programming: handle both enum and string values
        if isinstance(activity_type, str):
            logger.warning(
                "activity_type received as string '%s', converting to enum",
                activity_type,
            )
            try:
                activity_type = ActivityType(activity_type)
            except ValueError:
                logger.error("Invalid activity_type string: %s", activity_type)
                # Fallback to a default
                activity_type = ActivityType.FITNESS

        activity_value = (
            activity_type.value if hasattr(activity_type, "value") else str(activity_type)
        )

        client = self._get_client()

        # Priority field to ask about
        next_field = missing_fields[0]

        if client is None:
            # Mock question for testing
            return FollowUpQuestion(
                question=f"Can you tell me more about {next_field}?",
                field_target=next_field,
                question_type="required",
                priority="high",
            )

        try:
            system_prompt = f"""You are a friendly AI coach talking to a 15-year-old cricket player in Nepal.

Generate a natural, conversational follow-up question to collect the "{next_field}" field for {activity_value}.

Context - Already collected: {collected_data}
Missing field: {next_field}

Rules:
1. Keep it simple and age-appropriate
2. Sound encouraging and supportive
3. Be specific about what you need
4. Use cricket/fitness terminology they understand

Return ONLY the question text, nothing else."""

            completion = await client.chat.completions.create(
                model=settings.openai.gpt_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Generate follow-up question for field: {next_field}",
                    },
                ],
                temperature=0.7,  # Bit more creative for natural questions
                max_tokens=100,
            )

            question_text = completion.choices[0].message.content or ""
            question_text = question_text.strip().strip('"')

            return FollowUpQuestion(
                question=question_text,
                field_target=next_field,
                question_type="required"
                if next_field in self.required_fields.get(activity_type, [])
                else "optional",
                priority="high"
                if next_field in self.required_fields.get(activity_type, [])
                else "medium",
            )

        except Exception as e:
            logger.exception("Failed to generate follow-up question: %s", e)

            # Fallback questions
            fallback_questions = {
                "duration_minutes": "How long did your activity last?",
                "intensity": "How intense was it - low, medium, or high?",
                "mental_state": "How did you feel mentally during this?",
                "energy_level": "What was your energy level from 1 to 5?",
                "fitness_type": "What type of fitness activity was this?",
                "details": "Can you tell me more details about what you did?",
                "what_went_well": "What went well in your practice session?",
                "areas_for_improvement": "What areas do you think you need to improve?",
            }

            fallback_question = fallback_questions.get(
                next_field,
                f"Can you tell me about {next_field.replace('_', ' ')}?",
            )

            return FollowUpQuestion(
                question=fallback_question,
                field_target=next_field,
                question_type="required",
                priority="medium",
            )

    def complete_conversation(self, session_id: str) -> ConversationResult:
        """Complete the conversation and return final result."""
        context = self.get_conversation(session_id)
        if not context:
            raise ConversationServiceError(f"No active conversation for session {session_id}")

        context.state = ConversationState.COMPLETED

        # Calculate quality metrics
        required_fields = self.required_fields.get(context.activity_type, [])
        collected_required = [f for f in required_fields if f in context.collected_data]
        data_quality = len(collected_required) / len(required_fields) if required_fields else 1.0

        # Efficiency: fewer turns is better, but cap at 1.0
        efficiency = min(1.0, max(0.1, 1.0 - (context.turn_count - 2) * 0.1))

        result = ConversationResult(
            session_id=session_id,
            activity_type=context.activity_type,
            final_data=context.collected_data,
            total_turns=context.turn_count,
            completion_status="completed",
            data_quality_score=data_quality,
            conversation_efficiency=efficiency,
            started_at=context.created_at,
            completed_at=datetime.utcnow(),
            total_duration_seconds=(datetime.utcnow() - context.created_at).total_seconds(),
        )

        # Clean up
        if session_id in self.active_conversations:
            del self.active_conversations[session_id]

        logger.info(
            "Completed conversation %s: %d turns, %.2f quality, %.2f efficiency",
            session_id,
            result.total_turns,
            result.data_quality_score,
            result.conversation_efficiency,
        )

        return result

    def cleanup_session(self, session_id: str) -> None:
        """Clean up conversation session."""
        if session_id in self.active_conversations:
            del self.active_conversations[session_id]
            logger.info("Cleaned up conversation session: %s", session_id)


# Global conversation service instance
conversation_service = ConversationService()
