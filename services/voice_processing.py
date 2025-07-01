from voice_processing.websocket.manager import connection_manager
from voice_processing.schemas.processing import WebSocketMessage
from voice_processing.services.audio_storage import audio_storage
from voice_processing.services.openai_service import openai_service
from voice_processing.schemas.conversation import ActivityType
from voice_processing.services.conversation_service import conversation_service
from database.config.engine import  sessionmanager
from langfuse import observe
from datetime import UTC, datetime
import logging

logger = logging.getLogger(__name__)

@observe(capture_input=True, capture_output=False)
async def handle_complete_audio_processing(session_id: str) -> None:
    """Process complete accumulated audio with multi-turn conversation support."""
    try:
        start_time = datetime.now(UTC)

        # Get accumulated audio data
        voice_data = connection_manager.get_accumulated_audio(session_id)

        if len(voice_data) == 0:
            error_message = WebSocketMessage(
                type="error",
                session_id=session_id,
                error="no_audio_data",
                message="No audio data accumulated for processing",
            )
            await connection_manager.send_message(error_message, session_id)
            return

        # Check minimum audio size for meaningful content
        min_audio_size = 1000  # At least 1KB for meaningful audio
        if len(voice_data) < min_audio_size:
            error_message = WebSocketMessage(
                type="error",
                session_id=session_id,
                error="insufficient_audio_data",
                message=f"Audio data too small: {len(voice_data)} bytes. Please record for longer.",
            )
            await connection_manager.send_message(error_message, session_id)
            return

        # Get session metadata (entry_type and user_id)
        session_metadata = connection_manager.get_session_metadata(session_id)
        if not session_metadata:
            error_message = WebSocketMessage(
                type="error",
                session_id=session_id,
                error="no_session_metadata",
                message="Please send voice_data_meta message first with entry_type",
            )
            await connection_manager.send_message(error_message, session_id)
            return

        entry_type = session_metadata.get("entry_type")
        user_id = session_metadata.get("user_id", "demo_user")

        # Send processing start acknowledgment
        processing_message = WebSocketMessage(
            type="audio_processing_started",
            session_id=session_id,
            data={
                "status": "processing_complete_audio",
                "total_audio_size": len(voice_data),
                "entry_type": entry_type,
                "user_id": user_id,
            },
        )
        await connection_manager.send_message(processing_message, session_id)

        # 1. Save complete audio using refactored audio storage
        logger.info(
            "Processing complete audio for session %s: %s bytes, type: %s",
            session_id,
            len(voice_data),
            entry_type,
        )

        audio_save_result = await audio_storage.save_raw_audio(
            session_id=session_id,
            audio_data=voice_data,
            audio_format="webm",
        )

        # 2. Transcribe complete audio using improved OpenAI service
        transcription_result = await openai_service.transcribe_audio(voice_data)

        # Send transcript to user for confirmation
        transcript_message = WebSocketMessage(
            type="transcript_ready",
            session_id=session_id,
            data={
                "transcript": transcription_result.text,
                "confidence": transcription_result.confidence,
                "language": transcription_result.language,
                "entry_type": entry_type,
            },
        )
        await connection_manager.send_message(transcript_message, session_id)

        # 3. **NEW**: Use conversation service for multi-turn processing
        # Map entry_type to ActivityType
        activity_type_mapping = {
            "fitness": ActivityType.FITNESS,
            "cricket_coaching": ActivityType.CRICKET_COACHING,
            "cricket_match": ActivityType.CRICKET_MATCH,
            "rest_day": ActivityType.REST_DAY,
        }
        activity_type = activity_type_mapping.get(entry_type)

        if not activity_type:
            error_message = WebSocketMessage(
                type="error",
                session_id=session_id,
                error="invalid_activity_type",
                message=f"Unsupported activity type: {entry_type}",
            )
            await connection_manager.send_message(error_message, session_id)
            return

        # Start or continue conversation
        conversation_context = conversation_service.get_conversation(session_id)
        if not conversation_context:
            # Start new conversation
            conversation_context = conversation_service.start_conversation(
                session_id=session_id,
                user_id=user_id,
                activity_type=activity_type,
            )

            # Send conversation started message
            conversation_started_message = WebSocketMessage(
                type="conversation_started",
                session_id=session_id,
                data={
                    "activity_type": activity_type.value,
                    "message": "I'll help you log your activity. Let's start with what you've told me and I'll ask follow-up questions to get all the details.",
                },
            )
            await connection_manager.send_message(conversation_started_message, session_id)

        # Process user input and get conversation analysis
        conversation_analysis = await conversation_service.process_user_input(
            session_id=session_id,
            user_input=transcription_result.text,
            transcript_confidence=transcription_result.confidence,
        )

        # 4. Determine next step based on conversation analysis
        if conversation_analysis.should_continue and conversation_analysis.next_question:
            # Ask follow-up question
            follow_up_message = WebSocketMessage(
                type="follow_up_question",
                session_id=session_id,
                data={
                    "question": conversation_analysis.next_question.question,
                    "field_target": conversation_analysis.next_question.field_target,
                    "question_type": conversation_analysis.next_question.question_type,
                    "priority": conversation_analysis.next_question.priority,
                    "turn_number": conversation_context.turn_count,
                    "completeness_score": conversation_analysis.data_completeness.completeness_score,
                    "collected_data": conversation_context.collected_data,
                    "missing_fields": conversation_analysis.data_completeness.missing_fields,
                    "instructions": "Please answer the question and then tap the microphone to record your response.",
                },
            )
            await connection_manager.send_message(follow_up_message, session_id)

            logger.info(
                "Sent follow-up question for session %s: %s (targeting field: %s)",
                session_id,
                conversation_analysis.next_question.question,
                conversation_analysis.next_question.field_target,
            )

        elif conversation_analysis.can_generate_final_output:
            # Complete conversation and save to database
            conversation_result = conversation_service.complete_conversation(session_id)

            # Save final structured data to database
            structured_data = conversation_result.final_data
            saved_entry = None
            processing_duration = (datetime.now(UTC) - start_time).total_seconds()

            # Get all transcripts from the conversation context
            conversation_context = conversation_service.get_conversation(session_id)
            all_transcripts = ""
            if conversation_context and hasattr(conversation_context, "transcript_history"):
                # Combine all transcripts with turn numbers
                transcript_parts = []
                for turn_data in conversation_context.transcript_history:
                    turn_num = turn_data.get("turn", "N/A")
                    transcript = turn_data.get("transcript", "")
                    confidence = turn_data.get("confidence", 0.0)
                    transcript_parts.append(
                        f"Turn {turn_num} (conf: {confidence:.2f}): {transcript}"
                    )
                all_transcripts = "\n\n".join(transcript_parts)
            else:
                # Fallback to final transcript if history not available
                all_transcripts = transcription_result.text

            # Get database session for saving
            async with sessionmanager.get_session() as db_session:
                from fitness_tracking.repositories.cricket_repository import (
                    CricketCoachingRepository,
                    CricketMatchRepository,
                    RestDayRepository,
                )
                from fitness_tracking.repositories.fitness_repository import FitnessRepository

                if entry_type == "fitness":
                    fitness_repo = FitnessRepository(db_session)
                    saved_entry = await fitness_repo.create_from_voice_data(
                        session_id=session_id,
                        user_id=user_id,
                        voice_data=structured_data,
                        transcript=all_transcripts,
                        confidence_score=transcription_result.confidence,
                        processing_duration=processing_duration,
                    )

                elif entry_type == "cricket_coaching":
                    cricket_repo = CricketCoachingRepository(db_session)
                    saved_entry = await cricket_repo.create_from_voice_data(
                        session_id=session_id,
                        user_id=user_id,
                        voice_data=structured_data,
                        transcript=all_transcripts,
                        confidence_score=transcription_result.confidence,
                        processing_duration=processing_duration,
                    )

                elif entry_type == "cricket_match":
                    match_repo = CricketMatchRepository(db_session)
                    saved_entry = await match_repo.create_from_voice_data(
                        session_id=session_id,
                        user_id=user_id,
                        voice_data=structured_data,
                        transcript=all_transcripts,
                        confidence_score=transcription_result.confidence,
                        processing_duration=processing_duration,
                    )

                elif entry_type == "rest_day":
                    rest_repo = RestDayRepository(db_session)
                    saved_entry = await rest_repo.create_from_voice_data(
                        session_id=session_id,
                        user_id=user_id,
                        voice_data=structured_data,
                        transcript=all_transcripts,
                        confidence_score=transcription_result.confidence,
                        processing_duration=processing_duration,
                    )

            # Send conversation completed message
            result_message = WebSocketMessage(
                type="conversation_completed",
                session_id=session_id,
                data={
                    "status": "success",
                    "entry_type": entry_type,
                    "structured_data": structured_data,
                    "saved_entry_id": saved_entry.id if saved_entry else None,
                    "audio_file": audio_save_result.get("filename"),
                    "total_turns": conversation_result.total_turns,
                    "data_quality_score": conversation_result.data_quality_score,
                    "conversation_efficiency": conversation_result.conversation_efficiency,
                    "processing_time": processing_duration,
                    "database_saved": saved_entry is not None,
                    "user_id": user_id,
                    "message": f"Great! I've saved your {entry_type.replace('_', ' ')} entry with {len(structured_data)} data points collected over {conversation_result.total_turns} turns.",
                },
            )
            await connection_manager.send_message(result_message, session_id)

            logger.info(
                "✅ Conversation completed for session %s: %d turns, %.2f quality, %.2f efficiency",
                session_id,
                conversation_result.total_turns,
                conversation_result.data_quality_score,
                conversation_result.conversation_efficiency,
            )

        else:
            # Error case - something went wrong
            error_message = WebSocketMessage(
                type="error",
                session_id=session_id,
                error="conversation_analysis_failed",
                message=f"Conversation analysis failed: {conversation_analysis.reasoning}",
            )
            await connection_manager.send_message(error_message, session_id)
            conversation_service.cleanup_session(session_id)

        # Clear the audio buffer after processing
        connection_manager.clear_audio_buffer(session_id)

    except Exception as e:
        logger.exception("Complete audio processing failed for session %s", session_id)
        error_message = WebSocketMessage(
            type="error",
            session_id=session_id,
            error="voice_processing_failed",
            message=str(e),
        )
        await connection_manager.send_message(error_message, session_id)
        # Clean up on error
        connection_manager.clear_audio_buffer(session_id)
        conversation_service.cleanup_session(session_id)