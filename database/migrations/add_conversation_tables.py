"""
Add conversation persistence tables.

Migration: add_conversation_tables
Created: 2024-12-19
"""

import sqlalchemy as sa
from alembic import op


def upgrade():
    """Add conversation tables."""
    # Create conversations table
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column(
            "activity_type",
            sa.Enum(
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
            sa.Enum(
                "started",
                "collecting_data",
                "asking_followup",
                "completed",
                "error",
                name="conversationstate",
            ),
            nullable=False,
        ),
        sa.Column("total_turns", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_status", sa.String(), nullable=False, server_default="incomplete"),
        sa.Column("data_quality_score", sa.Float(), nullable=True),
        sa.Column("conversation_efficiency", sa.Float(), nullable=True),
        sa.Column("final_data", sa.JSON(), nullable=False, server_default="{}"),
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
    )

    # Create indexes for conversations table
    op.create_index("ix_conversations_session_id", "conversations", ["session_id"], unique=True)
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])
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
        sa.Column("extracted_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("extraction_confidence", sa.Float(), nullable=True),
        sa.Column("data_completeness_score", sa.Float(), nullable=True),
        sa.Column("missing_fields", sa.JSON(), nullable=False, server_default="[]"),
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
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
    )

    # Create indexes for conversation_turns table
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
        sa.Column("total_conversations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_conversations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_turns_per_conversation", sa.Float(), nullable=True),
        sa.Column("average_conversation_duration", sa.Float(), nullable=True),
        sa.Column("average_data_quality", sa.Float(), nullable=True),
        sa.Column("average_efficiency", sa.Float(), nullable=True),
        sa.Column("activity_breakdown", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("most_asked_questions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("common_missing_fields", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for conversation_analytics table
    op.create_index("ix_conversation_analytics_date", "conversation_analytics", ["date"])
    op.create_index("ix_conversation_analytics_user_id", "conversation_analytics", ["user_id"])


def downgrade():
    """Remove conversation tables."""
    # Drop tables in reverse order (due to foreign key dependencies)
    op.drop_table("conversation_analytics")
    op.drop_table("conversation_turns")
    op.drop_table("conversations")

    # Drop custom enum types
    op.execute("DROP TYPE IF EXISTS conversationstate")
    op.execute("DROP TYPE IF EXISTS activitytype")
