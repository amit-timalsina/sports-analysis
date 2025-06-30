"""Repository for conversation persistence and analytics."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, join, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.conversation import (
    ActivityType,
    Conversation,
    ConversationState,
    ConversationTurn,
)
from voice_processing.schemas.conversation import ConversationContext, ConversationResult


class ConversationRepository:
    """Repository for conversation persistence."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_conversation(self, context: ConversationContext) -> Conversation:
        """Create a new conversation record."""
        conversation = Conversation(
            session_id=context.session_id,
            user_id=context.user_id,
            activity_type=ActivityType(context.activity_type.value),
            state=ConversationState(context.state.value),
            started_at=context.created_at,
        )

        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def update_conversation_state(
        self,
        session_id: str,
        state: ConversationState,
    ) -> Conversation | None:
        """Update conversation state."""
        stmt = select(Conversation).where(Conversation.session_id == session_id)
        result = await self.session.execute(stmt)
        conversation = result.scalar_one_or_none()

        if conversation:
            conversation.state = state
            conversation.updated_at = datetime.utcnow()
            await self.session.flush()

        return conversation

    async def complete_conversation(
        self,
        session_id: str,
        result: ConversationResult,
        related_entry_id: int | None = None,
        related_entry_type: str | None = None,
    ) -> Conversation | None:
        """Mark conversation as completed and store final results."""
        stmt = select(Conversation).where(Conversation.session_id == session_id)
        db_result = await self.session.execute(stmt)
        conversation = db_result.scalar_one_or_none()

        if conversation:
            conversation.state = ConversationState.COMPLETED
            conversation.completion_status = result.completion_status
            conversation.total_turns = result.total_turns
            conversation.data_quality_score = result.data_quality_score
            conversation.conversation_efficiency = result.conversation_efficiency
            conversation.final_data = result.final_data
            conversation.completed_at = result.completed_at
            conversation.total_duration_seconds = result.total_duration_seconds
            conversation.related_entry_id = related_entry_id
            conversation.related_entry_type = related_entry_type
            conversation.updated_at = datetime.utcnow()

            await self.session.flush()

        return conversation

    async def add_conversation_turn(
        self,
        session_id: str,
        turn_number: int,
        user_input: str,
        transcript_confidence: float,
        extracted_data: dict[str, Any],
        ai_response: str | None = None,
        follow_up_question: str | None = None,
        target_field: str | None = None,
        extraction_confidence: float | None = None,
        data_completeness_score: float | None = None,
        missing_fields: list[str] | None = None,
        processing_duration: float | None = None,
    ) -> ConversationTurn | None:
        """Add a turn to an existing conversation."""
        # First get the conversation
        stmt = select(Conversation).where(Conversation.session_id == session_id)
        result = await self.session.execute(stmt)
        conversation = result.scalar_one_or_none()

        if not conversation:
            return None

        turn = ConversationTurn(
            conversation_id=conversation.id,
            turn_number=turn_number,
            user_input=user_input,
            transcript_confidence=transcript_confidence,
            ai_response=ai_response,
            follow_up_question=follow_up_question,
            target_field=target_field,
            extracted_data=extracted_data,
            extraction_confidence=extraction_confidence,
            data_completeness_score=data_completeness_score,
            missing_fields=missing_fields or [],
            processing_duration=processing_duration,
        )

        self.session.add(turn)

        # Update conversation turn count
        conversation.total_turns = turn_number
        conversation.updated_at = datetime.utcnow()

        await self.session.flush()
        return turn

    async def get_conversation_with_turns(self, session_id: str) -> Conversation | None:
        """Get conversation with all its turns."""
        stmt = (
            select(Conversation)
            .where(Conversation.session_id == session_id)
            .options(selectinload(Conversation.turns))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Conversation]:
        """Get conversations for a user with pagination."""
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_conversation_analytics(
        self,
        user_id: str | None = None,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get conversation analytics for a user or globally."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Base query conditions
        conditions = [Conversation.created_at >= cutoff_date]
        if user_id:
            conditions.append(Conversation.user_id == user_id)

        # Total conversations
        total_stmt = select(func.count(Conversation.id)).where(and_(*conditions))
        total_result = await self.session.execute(total_stmt)
        total_conversations = total_result.scalar() or 0

        # Completed conversations
        completed_conditions = conditions + [Conversation.state == ConversationState.COMPLETED]
        completed_stmt = select(func.count(Conversation.id)).where(and_(*completed_conditions))
        completed_result = await self.session.execute(completed_stmt)
        completed_conversations = completed_result.scalar() or 0

        # Average metrics for completed conversations
        if completed_conversations > 0:
            avg_stmt = select(
                func.avg(Conversation.total_turns),
                func.avg(Conversation.total_duration_seconds),
                func.avg(Conversation.data_quality_score),
                func.avg(Conversation.conversation_efficiency),
            ).where(and_(*completed_conditions))
            avg_result = await self.session.execute(avg_stmt)
            avg_turns, avg_duration, avg_quality, avg_efficiency = avg_result.first()
        else:
            avg_turns = avg_duration = avg_quality = avg_efficiency = None

        # Activity type breakdown
        activity_stmt = (
            select(Conversation.activity_type, func.count(Conversation.id))
            .where(and_(*conditions))
            .group_by(Conversation.activity_type)
        )
        activity_result = await self.session.execute(activity_stmt)
        activity_breakdown = {str(activity): count for activity, count in activity_result.all()}

        return {
            "total_conversations": total_conversations,
            "completed_conversations": completed_conversations,
            "completion_rate": completed_conversations / total_conversations
            if total_conversations > 0
            else 0,
            "average_turns_per_conversation": float(avg_turns) if avg_turns else None,
            "average_duration_seconds": float(avg_duration) if avg_duration else None,
            "average_data_quality": float(avg_quality) if avg_quality else None,
            "average_efficiency": float(avg_efficiency) if avg_efficiency else None,
            "activity_breakdown": activity_breakdown,
        }

    async def get_most_asked_questions(
        self,
        activity_type: ActivityType | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get the most frequently asked follow-up questions."""
        conditions = [ConversationTurn.follow_up_question.isnot(None)]

        if activity_type:
            conditions.append(Conversation.activity_type == activity_type)

        stmt = (
            select(
                ConversationTurn.follow_up_question,
                ConversationTurn.target_field,
                func.count(ConversationTurn.id).label("frequency"),
            )
            .select_from(join(ConversationTurn, Conversation))
            .where(and_(*conditions))
            .group_by(ConversationTurn.follow_up_question, ConversationTurn.target_field)
            .order_by(func.count(ConversationTurn.id).desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return [
            {
                "question": question,
                "target_field": target_field,
                "frequency": frequency,
            }
            for question, target_field, frequency in result.all()
        ]
