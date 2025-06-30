#!/usr/bin/env python3
"""
Direct SQL script to create conversation tables.
"""

import asyncio
import asyncpg

async def create_conversation_tables():
    """Create conversation tables using direct SQL."""
    print("🔧 Creating conversation tables with direct SQL...")
    print(f"📊 Database: localhost:8432/cricket_fitness")
    
    try:
        # Connect directly to database
        conn = await asyncpg.connect(
            host="localhost",
            port=8432,
            database="cricket_fitness",
            user="postgres",
            password="postgres"
        )
        
        # Create conversation tables
        await conn.execute("""
            -- Create enum types
            DO $$ BEGIN
                CREATE TYPE activitytype AS ENUM ('fitness', 'cricket_coaching', 'cricket_match', 'rest_day');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
            
            DO $$ BEGIN
                CREATE TYPE conversationstate AS ENUM ('started', 'collecting_data', 'asking_followup', 'completed', 'error');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
            
            -- Create conversations table
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR NOT NULL UNIQUE,
                user_id VARCHAR NOT NULL,
                activity_type activitytype NOT NULL,
                state conversationstate NOT NULL DEFAULT 'started',
                total_turns INTEGER NOT NULL DEFAULT 0,
                completion_status VARCHAR NOT NULL DEFAULT 'incomplete',
                data_quality_score FLOAT,
                conversation_efficiency FLOAT,
                final_data JSONB NOT NULL DEFAULT '{}',
                started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                completed_at TIMESTAMPTZ,
                total_duration_seconds FLOAT,
                related_entry_id INTEGER,
                related_entry_type VARCHAR,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ
            );
            
            -- Create indexes for conversations table
            CREATE INDEX IF NOT EXISTS ix_conversations_session_id ON conversations (session_id);
            CREATE INDEX IF NOT EXISTS ix_conversations_user_id ON conversations (user_id);
            CREATE INDEX IF NOT EXISTS ix_conversations_activity_type ON conversations (activity_type);
            CREATE INDEX IF NOT EXISTS ix_conversations_state ON conversations (state);
            CREATE INDEX IF NOT EXISTS ix_conversations_created_at ON conversations (created_at);
            
            -- Create conversation_turns table
            CREATE TABLE IF NOT EXISTS conversation_turns (
                id SERIAL PRIMARY KEY,
                conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                turn_number INTEGER NOT NULL,
                user_input TEXT NOT NULL,
                transcript_confidence FLOAT NOT NULL,
                ai_response TEXT,
                follow_up_question TEXT,
                target_field VARCHAR,
                extracted_data JSONB NOT NULL DEFAULT '{}',
                extraction_confidence FLOAT,
                data_completeness_score FLOAT,
                missing_fields JSONB NOT NULL DEFAULT '[]',
                turn_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                processing_duration FLOAT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ
            );
            
            -- Create indexes for conversation_turns table
            CREATE INDEX IF NOT EXISTS ix_conversation_turns_conversation_id ON conversation_turns (conversation_id);
            CREATE INDEX IF NOT EXISTS ix_conversation_turns_turn_number ON conversation_turns (turn_number);
            CREATE INDEX IF NOT EXISTS ix_conversation_turns_turn_timestamp ON conversation_turns (turn_timestamp);
            
            -- Create conversation_analytics table
            CREATE TABLE IF NOT EXISTS conversation_analytics (
                id SERIAL PRIMARY KEY,
                date TIMESTAMPTZ NOT NULL,
                user_id VARCHAR,
                total_conversations INTEGER NOT NULL DEFAULT 0,
                completed_conversations INTEGER NOT NULL DEFAULT 0,
                average_turns_per_conversation FLOAT,
                average_conversation_duration FLOAT,
                average_data_quality FLOAT,
                average_efficiency FLOAT,
                activity_breakdown JSONB NOT NULL DEFAULT '{}',
                most_asked_questions JSONB NOT NULL DEFAULT '[]',
                common_missing_fields JSONB NOT NULL DEFAULT '[]',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ
            );
            
            -- Create indexes for conversation_analytics table
            CREATE INDEX IF NOT EXISTS ix_conversation_analytics_date ON conversation_analytics (date);
            CREATE INDEX IF NOT EXISTS ix_conversation_analytics_user_id ON conversation_analytics (user_id);
        """)
        
        await conn.close()
        
        print("✅ Tables created successfully!")
        print("\n📋 Created tables:")
        print("  - conversations")
        print("  - conversation_turns") 
        print("  - conversation_analytics")
        
        return True
        
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        return False

def main():
    print("🚀 Cricket Fitness Tracker - Create Conversation Tables (SQL)")
    print("=" * 65)
    
    success = asyncio.run(create_conversation_tables())
    
    if success:
        print("\n🎉 Table creation completed successfully!")
    else:
        print("\n❌ Table creation failed!")

if __name__ == "__main__":
    main()
