"""Conversation service for managing multi-turn voice interactions."""

import json
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

        # Data field requirements for each activity type
        self.required_fields = {
            ActivityType.FITNESS: [
                "fitness_type",
                "duration_minutes",
                "intensity",
                "details",
                "mental_state",
                "energy_level",
            ],
            ActivityType.CRICKET_COACHING: [
                "activity",
                "what_went_well",
                "areas_for_improvement",
                "mental_state",
            ],
            ActivityType.CRICKET_MATCH: [
                "match_type",
                "runs_scored",
                "mental_state_pre_match",
                "mental_state_during_batting",
            ],
            ActivityType.REST_DAY: [
                "activities",
                "recovery_quality",
                "mental_state",
            ],
        }

        # Optional fields that enhance data quality
        self.optional_fields = {
            ActivityType.FITNESS: [
                "distance_km",
                "location",
                "calories_burned",
            ],
            ActivityType.CRICKET_COACHING: [
                "coach_feedback",
                "self_assessment_score",
                "skills_practiced",
            ],
            ActivityType.CRICKET_MATCH: [
                "balls_faced",
                "boundaries",
                "catches_taken",
                "opposition_strength",
            ],
            ActivityType.REST_DAY: [
                "notes",
                "physical_state",
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
        Process user input and determine next steps in conversation.

        Args:
            session_id: Session identifier
            user_input: User's voice input (transcript)
            transcript_confidence: Confidence score from speech-to-text

        Returns:
            Analysis of conversation state and next steps

        """
        context = self.get_conversation(session_id)
        if not context:
            raise ConversationServiceError(f"No active conversation for session {session_id}")

        # Update conversation history
        context.conversation_history.append(
            {
                "turn": str(context.turn_count + 1),
                "user": user_input,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        context.turn_count += 1
        context.updated_at = datetime.utcnow()

        # Extract data from current input
        extracted_data = await self._extract_data_from_input(
            user_input,
            context.activity_type,
            context.collected_data,
        )

        # Merge with existing data
        context.collected_data.update(extracted_data)

        # Analyze data completeness
        completeness = self._analyze_data_completeness(
            context.collected_data,
            context.activity_type,
            transcript_confidence,
        )

        # Determine next steps
        if completeness.is_complete or context.turn_count >= 8:  # Max 8 turns
            # Generate final output
            context.state = ConversationState.COMPLETED
            return ConversationAnalysis(
                data_completeness=completeness,
                next_question=None,
                should_continue=False,
                can_generate_final_output=True,
                analysis_confidence=completeness.confidence_score,
                reasoning="Data collection complete or max turns reached",
            )

        # Generate follow-up question
        next_question = await self._generate_follow_up_question(
            context.collected_data,
            context.activity_type,
            completeness.missing_fields,
        )

        context.state = ConversationState.ASKING_FOLLOWUP

        return ConversationAnalysis(
            data_completeness=completeness,
            next_question=next_question,
            should_continue=True,
            can_generate_final_output=False,
            analysis_confidence=0.85,
            reasoning=f"Need more data for fields: {', '.join(completeness.missing_fields[:3])}",
        )

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

            # For non-fitness activities, use the original approach
            system_prompt = self._create_extraction_prompt(activity_type, existing_data)

            completion = await client.chat.completions.create(
                model=settings.openai.gpt_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract data from: {user_input}"},
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=500,
            )

            response_text = completion.choices[0].message.content or ""

            # Parse the response to extract key-value pairs
            extracted_data = self._parse_extraction_response(response_text, activity_type)

            logger.info("Extracted data from input: %s", list(extracted_data.keys()))
            return extracted_data

        except Exception as e:
            logger.exception("Failed to extract data from input: %s", e)
            # Fallback: try simple keyword extraction
            return self._fallback_extraction(user_input, activity_type)

    def _create_extraction_prompt(
        self,
        activity_type: ActivityType,
        existing_data: dict[str, Any],
    ) -> str:
        """Create system prompt for data extraction."""
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

        if activity_type == ActivityType.FITNESS:
            base_prompt = f"""You are extracting {activity_value} data from a 15-year-old cricket player's voice input.

CRITICAL VALIDATION RULES:
- fitness_type MUST be exactly one of: "running", "strength_training", "cricket_specific", "cardio", "flexibility", "general_fitness"
- Map variations: jog/jogging -> "running", gym/weights -> "strength_training", etc.
- intensity MUST be exactly: "low", "medium", or "high"
- energy_level MUST be integer 1-5

Required fields for {activity_value}:
{", ".join(self.required_fields.get(activity_type, []))}

Optional fields:
{", ".join(self.optional_fields.get(activity_type, []))}

Current collected data: {existing_data}

Return ONLY a JSON object with extracted fields. Use null for fields not mentioned.
Example: {{"fitness_type": "running", "duration_minutes": 30, "intensity": "medium", "details": "morning jog"}}

IMPORTANT: Only extract information explicitly mentioned in the user's input. Do not make assumptions."""
        else:
            base_prompt = f"""You are extracting {activity_value} data from a 15-year-old cricket player's voice input.

IMPORTANT: Only extract information that is explicitly mentioned in the user's input. Do not make assumptions.

Required fields for {activity_value}:
{", ".join(self.required_fields.get(activity_type, []))}

Optional fields:
{", ".join(self.optional_fields.get(activity_type, []))}

Current collected data: {existing_data}

Return ONLY a JSON object with extracted fields. Use null for fields not mentioned.
Example: {{"duration_minutes": 30, "intensity": "medium", "details": "morning session"}}"""

        return base_prompt

    def _parse_extraction_response(
        self,
        response: str,
        activity_type: ActivityType,
    ) -> dict[str, Any]:
        """Parse OpenAI response to extract structured data."""
        try:
            # Try to find JSON in the response
            start = response.find("{")
            end = response.rfind("}") + 1

            if start != -1 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)

                # Filter to only expected fields
                all_fields = self.required_fields.get(activity_type, []) + self.optional_fields.get(
                    activity_type,
                    [],
                )

                filtered_data = {k: v for k, v in data.items() if k in all_fields and v is not None}

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse JSON from response: %s", e)
        else:
            return filtered_data
        # Fallback: empty dict
        return {}

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
                logger.error("Invalid activity_type string: %s", activity_type)
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
