"""Service for completing conversations and persisting all related data."""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from common.schemas.entry_type import EntryType
from fitness_tracking.models.cricket import CricketCoachingEntry, CricketMatchEntry
from fitness_tracking.repositories import (
    CricketCoachingEntryRepository,
    CricketMatchEntryRepository,
    FitnessEntryRepository,
    RestDayEntryRepository,
)
from fitness_tracking.schemas.exercise_type import ExerciseType
from fitness_tracking.schemas.fitness import FitnessEntryCreate, FitnessEntryRead
from fitness_tracking.schemas.intensity_level import IntensityLevel
from voice_processing.models.conversation import (
    ConversationState,
)
from voice_processing.repositories import (
    ConversationMessageRepository,
    ConversationRepository,
    ConversationTurnRepository,
)
from voice_processing.schemas.conversation import (
    ConversationCreate,
    ConversationMessageCreate,
    ConversationRead,
    ConversationResult,
    ConversationTurnCreate,
    ConversationTurnRead,
    MessageType,
)

logger = logging.getLogger(__name__)


class CompletionResult:
    """Result of completing and persisting a conversation."""

    def __init__(
        self,
        conversation_id: int,
        activity_id: int,
        turns: list[int],
    ) -> None:
        """Initialize completion result."""
        self.conversation_id = conversation_id
        self.activity_id = activity_id
        self.turns = turns


class ConversationCompletionService:
    """Handles completion and persistence of conversations and derived entries."""

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        message_repo: ConversationMessageRepository,
        turn_repo: ConversationTurnRepository,
        fitness_repo: FitnessEntryRepository,
        cricket_repo: CricketMatchEntryRepository,
        coaching_repo: CricketCoachingEntryRepository,
        rest_repo: RestDayEntryRepository,
    ) -> None:
        """Initialize completion service with repositories."""
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.turn_repo = turn_repo
        self.fitness_repo = fitness_repo
        self.cricket_repo = cricket_repo
        self.coaching_repo = coaching_repo
        self.rest_repo = rest_repo

    async def complete_conversation(
        self,
        conversation_result: ConversationResult,
        transcript_history: list[dict[str, Any]],
        metadata: dict[str, Any],
    ) -> CompletionResult:
        """Complete conversation and persist all related data atomically."""
        async with self.conversation_repo.session.begin():
            # 1. Save base conversation
            conversation = await self._save_conversation(conversation_result)

            # 2. Save turns and messages
            turns = await self._save_conversation_turns(
                int(conversation.id),  # Convert UUID to int
                transcript_history,
            )

            # 3. Save activity-specific entry
            entry = await self._save_activity_entry(
                int(conversation.id),  # Convert UUID to int
                conversation_result,
                metadata,
            )

            return CompletionResult(
                conversation_id=int(conversation.id),  # Convert UUID to int
                activity_id=int(entry.id),  # Convert UUID to int
                turns=[int(t.id) for t in turns],  # Convert UUIDs to ints
            )

    async def _save_conversation(self, result: ConversationResult) -> ConversationRead:
        """Save the conversation record."""
        # Extract required fields with validation
        try:
            user_id = result.final_data["user_id"]
            activity_type = result.final_data["activity_type"]
        except KeyError as e:
            msg = f"Missing required field in conversation data: {e.args[0]}"
            raise ValueError(
                msg,
            ) from e

        conv = ConversationCreate(
            session_id=result.session_id,
            user_id=user_id,
            activity_type=activity_type,
            state=ConversationState.COMPLETED,
            current_data=result.final_data,
            data_confidence={"overall": result.data_quality_score},
        )
        return await self.conversation_repo.create(conv)

    async def _save_conversation_turns(
        self,
        conversation_id: int,
        transcript_history: list[dict[str, Any]],
    ) -> list[ConversationTurnRead]:
        """Save all turns and their messages."""
        turns = []
        for turn in transcript_history:
            # Create turn
            turn_data = ConversationTurnCreate(
                conversation_id=conversation_id,
                turn_number=turn["turn"],
                data_extracted_this_turn=turn.get("extracted_data", {}),
                turn_effectiveness_score=None,  # Optional score
                data_completeness_after_turn=None,  # Optional score
            )
            saved_turn = await self.turn_repo.create(turn_data)

            # Create message for transcript
            msg_data = ConversationMessageCreate(
                conversation_id=conversation_id,
                turn_id=int(saved_turn.id),  # Convert UUID to int
                message_type=MessageType.USER_INPUT,  # Enum value
                sequence_number=turn["turn"],
                content=turn["transcript"],
                transcript_confidence=turn["confidence"],
                extraction_confidence=None,  # Optional confidence
            )
            await self.message_repo.create(msg_data)

            turns.append(saved_turn)

        return turns

    async def _save_activity_entry(
        self,
        conversation_id: int,
        result: ConversationResult,
        metadata: dict[str, Any],
    ) -> FitnessEntryRead | CricketMatchEntry | CricketCoachingEntry:
        """Save the activity-specific entry."""
        activity_type = metadata["entry_type"]

        if activity_type == "fitness":
            return await self._save_fitness_entry(conversation_id, result)
        if activity_type == "cricket_match":
            return await self._save_cricket_match(conversation_id, result)
        if activity_type == "cricket_coaching":
            return await self._save_cricket_coaching(conversation_id, result)
        if activity_type == "rest_day":
            msg = "Rest day persistence not yet implemented"
            raise NotImplementedError(msg)
        msg = f"Unsupported activity type: {activity_type}"
        raise ValueError(msg)

    async def _save_fitness_entry(
        self,
        conversation_id: int,
        result: ConversationResult,
    ) -> FitnessEntryRead:
        """Save fitness-specific entry."""
        # Extract required fields with validation
        try:
            entry = FitnessEntryCreate(
                user_id=result.final_data["user_id"],
                session_id=result.session_id,
                conversation_id=UUID(int=conversation_id),  # Convert int to UUID
                entry_type=EntryType.FITNESS,
                original_transcript=result.final_data.get("original_transcript", ""),
                overall_confidence_score=result.data_quality_score,
                # Required timestamp
                activity_timestamp=datetime.now(UTC),
                # Map conversation fields to entry fields
                exercise_type=ExerciseType(result.final_data["fitness_type"]),
                exercise_name=result.final_data["fitness_type"],
                duration_minutes=result.final_data["duration_minutes"],
                intensity=IntensityLevel(result.final_data["intensity"]),
                mental_state=result.final_data["mental_state"],
                energy_level=result.final_data["energy_level"],
                # Required fields with defaults
                calories_burned=None,  # Optional in schema
                # More required fields with defaults
                sets=None,  # Optional for non-strength activities
                reps=None,  # Optional for non-strength activities
                # Advanced metrics with defaults
                weight_kg=None,  # Optional for non-strength activities
                heart_rate_avg=None,  # Optional heart rate data
                heart_rate_max=None,  # Optional heart rate data
                workout_rating=None,  # Optional rating
                # Optional fields
                equipment_used=None,  # Optional equipment list
                gym_name=None,  # Optional gym name
                weather_conditions=None,  # Optional weather info
                temperature=None,  # Optional temperature
                workout_partner=None,  # Optional partner name
                trainer_name=None,  # Optional trainer name
                start_time=None,  # Optional start time
                end_time=None,  # Optional end time
                processing_duration=None,  # Optional processing time
                data_quality_score=result.data_quality_score,  # Quality from conversation
                distance_km=result.final_data.get("distance_km"),
                location=result.final_data.get("location"),
                notes=result.final_data.get("notes"),
                manual_overrides=None,
                validation_notes=None,
            )
        except KeyError as e:
            msg = f"Missing required field for fitness entry: {e.args[0]}"
            raise ValueError(
                msg,
            ) from e
        return await self.fitness_repo.create(entry)

    async def _save_cricket_match(
        self,
        conversation_id: int,
        result: ConversationResult,
    ) -> CricketMatchEntry:
        """Save cricket match entry."""
        # TODO: Implement cricket match persistence
        msg = "Cricket match persistence not yet implemented"
        raise NotImplementedError(msg)

    async def _save_cricket_coaching(
        self,
        conversation_id: int,
        result: ConversationResult,
    ) -> CricketCoachingEntry:
        """Save cricket coaching entry."""
        # TODO: Implement cricket coaching persistence
        msg = "Cricket coaching persistence not yet implemented"
        raise NotImplementedError(msg)

    async def _save_rest_day(
        self,
        conversation_id: int,
        result: ConversationResult,
    ) -> None:
        """Save rest day entry."""
        # TODO: Implement rest day persistence
        msg = "Rest day persistence not yet implemented"
        raise NotImplementedError(msg)
