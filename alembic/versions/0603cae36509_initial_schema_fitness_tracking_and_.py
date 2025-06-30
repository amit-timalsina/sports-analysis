"""Initial schema: fitness tracking and conversation tables

Revision ID: 0603cae36509
Revises:
Create Date: 2025-06-30 19:56:47.012693

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0603cae36509"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create all tables and enums."""

    # Note: SQLAlchemy will automatically create the enum types when creating tables

    # Create fitness_entries table
    op.create_table(
        "fitness_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("transcript", sa.String(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("processing_duration", sa.Float(), nullable=True),
        sa.Column(
            "fitness_type",
            postgresql.ENUM(
                "RUNNING",
                "STRENGTH_TRAINING",
                "CRICKET_SPECIFIC",
                "CARDIO",
                "FLEXIBILITY",
                "GENERAL_FITNESS",
                name="fitnesstype",
            ),
            nullable=False,
        ),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column(
            "intensity",
            postgresql.ENUM("LOW", "MEDIUM", "HIGH", name="intensity"),
            nullable=False,
        ),
        sa.Column("details", sa.String(), nullable=False),
        sa.Column("mental_state", sa.String(), nullable=False),
        sa.Column("energy_level", sa.Integer(), nullable=False),
        sa.Column("distance_km", sa.Float(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fitness_entries_user_id", "fitness_entries", ["user_id"])
    op.create_index("ix_fitness_entries_session_id", "fitness_entries", ["session_id"])

    # Create cricket_coaching_entries table
    op.create_table(
        "cricket_coaching_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("transcript", sa.String(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("processing_duration", sa.Float(), nullable=True),
        sa.Column(
            "session_type",
            postgresql.ENUM(
                "BATTING_DRILLS",
                "WICKET_KEEPING",
                "NETTING",
                "PERSONAL_COACHING",
                "TEAM_PRACTICE",
                "OTHER",
                name="cricketsessiontype",
            ),
            nullable=False,
        ),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("what_went_well", sa.String(), nullable=False),
        sa.Column("areas_for_improvement", sa.String(), nullable=False),
        sa.Column("coach_feedback", sa.String(), nullable=True),
        sa.Column("self_assessment_score", sa.Integer(), nullable=False),
        sa.Column("skills_practiced", sa.String(), nullable=False),
        sa.Column("difficulty_level", sa.Integer(), nullable=False),
        sa.Column("confidence_level", sa.Integer(), nullable=False),
        sa.Column("focus_level", sa.Integer(), nullable=False),
        sa.Column("learning_satisfaction", sa.Integer(), nullable=False),
        sa.Column("mental_state", sa.String(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cricket_coaching_entries_user_id", "cricket_coaching_entries", ["user_id"])
    op.create_index(
        "ix_cricket_coaching_entries_session_id",
        "cricket_coaching_entries",
        ["session_id"],
    )

    # Create cricket_match_entries table
    op.create_table(
        "cricket_match_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("transcript", sa.String(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("processing_duration", sa.Float(), nullable=True),
        sa.Column(
            "match_type",
            postgresql.ENUM("PRACTICE", "TOURNAMENT", "SCHOOL", "CLUB", "OTHER", name="matchtype"),
            nullable=False,
        ),
        sa.Column("opposition_strength", sa.Integer(), nullable=False),
        sa.Column("runs_scored", sa.Integer(), nullable=True),
        sa.Column("balls_faced", sa.Integer(), nullable=True),
        sa.Column("boundaries_4s", sa.Integer(), nullable=True),
        sa.Column("boundaries_6s", sa.Integer(), nullable=True),
        sa.Column("how_out", sa.String(), nullable=True),
        sa.Column("key_shots_played", sa.String(), nullable=True),
        sa.Column("catches_taken", sa.Integer(), nullable=True),
        sa.Column("catches_dropped", sa.Integer(), nullable=True),
        sa.Column("stumpings", sa.Integer(), nullable=True),
        sa.Column("pre_match_nerves", sa.Integer(), nullable=False),
        sa.Column("post_match_satisfaction", sa.Integer(), nullable=False),
        sa.Column("mental_state", sa.String(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cricket_match_entries_user_id", "cricket_match_entries", ["user_id"])
    op.create_index("ix_cricket_match_entries_session_id", "cricket_match_entries", ["session_id"])

    # Create rest_day_entries table
    op.create_table(
        "rest_day_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("transcript", sa.String(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("processing_duration", sa.Float(), nullable=True),
        sa.Column(
            "rest_type",
            postgresql.ENUM("COMPLETE_REST", "ACTIVE_RECOVERY", "INJURY_RECOVERY", name="resttype"),
            nullable=False,
        ),
        sa.Column("physical_state", sa.String(), nullable=False),
        sa.Column("fatigue_level", sa.Integer(), nullable=False),
        sa.Column("energy_level", sa.Integer(), nullable=False),
        sa.Column("motivation_level", sa.Integer(), nullable=False),
        sa.Column("mood_description", sa.String(), nullable=False),
        sa.Column("mental_state", sa.String(), nullable=False),
        sa.Column("soreness_level", sa.Integer(), nullable=True),
        sa.Column("training_reflections", sa.String(), nullable=True),
        sa.Column("goals_concerns", sa.String(), nullable=True),
        sa.Column("recovery_activities", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rest_day_entries_user_id", "rest_day_entries", ["user_id"])
    op.create_index("ix_rest_day_entries_session_id", "rest_day_entries", ["session_id"])

    # Create conversations table
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column(
            "activity_type",
            postgresql.ENUM(
                "fitness",
                "cricket_coaching",
                "cricket_match",
                "rest_day",
                name="activitytype",
            ),
            nullable=False,
        ),
        sa.Column(
            "state",
            postgresql.ENUM(
                "started",
                "collecting_data",
                "asking_followup",
                "completed",
                "error",
                name="conversationstate",
            ),
            server_default="started",
            nullable=False,
        ),
        sa.Column("total_turns", sa.Integer(), server_default="0", nullable=False),
        sa.Column("completion_status", sa.String(), server_default="incomplete", nullable=False),
        sa.Column("data_quality_score", sa.Float(), nullable=True),
        sa.Column("conversation_efficiency", sa.Float(), nullable=True),
        sa.Column(
            "final_data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_duration_seconds", sa.Float(), nullable=True),
        sa.Column("related_entry_id", sa.Integer(), nullable=True),
        sa.Column("related_entry_type", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])
    op.create_index("ix_conversations_session_id", "conversations", ["session_id"])
    op.create_index("ix_conversations_activity_type", "conversations", ["activity_type"])
    op.create_index("ix_conversations_state", "conversations", ["state"])
    op.create_index("ix_conversations_created_at", "conversations", ["created_at"])

    # Create conversation_turns table
    op.create_table(
        "conversation_turns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("turn_number", sa.Integer(), nullable=False),
        sa.Column("user_input", sa.Text(), nullable=False),
        sa.Column("transcript_confidence", sa.Float(), nullable=False),
        sa.Column("ai_response", sa.Text(), nullable=True),
        sa.Column("follow_up_question", sa.Text(), nullable=True),
        sa.Column("target_field", sa.String(), nullable=True),
        sa.Column(
            "extracted_data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("extraction_confidence", sa.Float(), nullable=True),
        sa.Column("data_completeness_score", sa.Float(), nullable=True),
        sa.Column(
            "missing_fields",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
        sa.Column(
            "turn_timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("processing_duration", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_conversation_turns_conversation_id",
        "conversation_turns",
        ["conversation_id"],
    )
    op.create_index("ix_conversation_turns_turn_number", "conversation_turns", ["turn_number"])
    op.create_index(
        "ix_conversation_turns_turn_timestamp",
        "conversation_turns",
        ["turn_timestamp"],
    )

    # Create conversation_analytics table
    op.create_table(
        "conversation_analytics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("total_conversations", sa.Integer(), server_default="0", nullable=False),
        sa.Column("completed_conversations", sa.Integer(), server_default="0", nullable=False),
        sa.Column("average_turns_per_conversation", sa.Float(), nullable=True),
        sa.Column("average_conversation_duration", sa.Float(), nullable=True),
        sa.Column("average_data_quality", sa.Float(), nullable=True),
        sa.Column("average_efficiency", sa.Float(), nullable=True),
        sa.Column(
            "activity_breakdown",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "most_asked_questions",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
        sa.Column(
            "common_missing_fields",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversation_analytics_date", "conversation_analytics", ["date"])
    op.create_index("ix_conversation_analytics_user_id", "conversation_analytics", ["user_id"])


def downgrade() -> None:
    """Drop all tables and enums."""

    # Drop tables (order matters due to foreign keys)
    op.drop_table("conversation_turns")
    op.drop_table("conversation_analytics")
    op.drop_table("conversations")
    op.drop_table("rest_day_entries")
    op.drop_table("cricket_match_entries")
    op.drop_table("cricket_coaching_entries")
    op.drop_table("fitness_entries")

    # Drop custom enum types
    op.execute("DROP TYPE IF EXISTS conversationstate")
    op.execute("DROP TYPE IF EXISTS activitytype")
    op.execute("DROP TYPE IF EXISTS resttype")
    op.execute("DROP TYPE IF EXISTS matchtype")
    op.execute("DROP TYPE IF EXISTS cricketsessiontype")
    op.execute("DROP TYPE IF EXISTS intensity")
    op.execute("DROP TYPE IF EXISTS fitnesstype")
