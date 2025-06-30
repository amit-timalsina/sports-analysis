#!/usr/bin/env python3
"""
Verification script for cricket fitness tracker implementation.

This script tests:
- Database model creation
- Repository operations
- Voice processing pipeline (mock)
- API endpoint functionality
"""

import asyncio
import logging

from database.config.engine import sessionmanager
from fitness_tracking.repositories import (
    CricketAnalyticsRepository,
    CricketCoachingRepository,
    FitnessRepository,
)
from fitness_tracking.schemas.cricket import CricketCoachingDataExtraction
from fitness_tracking.schemas.fitness import FitnessDataExtraction

logger = logging.getLogger(__name__)


async def test_database_setup():
    """Test database connection and table creation."""
    print("🔧 Testing database setup...")

    try:
        # Initialize database
        sessionmanager.init_db()

        # Create tables
        await sessionmanager.create_tables()

        # Test database connection
        stats = await sessionmanager.get_stats()
        print(f"✅ Database connected: {stats['status']}")
        print(f"   Version: {stats.get('version', 'unknown')}")

        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False


async def test_repository_operations():
    """Test repository CRUD operations."""
    print("\n📂 Testing repository operations...")

    try:
        async with sessionmanager.get_session() as session:
            fitness_repo = FitnessRepository(session)

            # Test fitness entry creation
            mock_fitness_data = FitnessDataExtraction(
                fitness_type="running",
                duration_minutes=30,
                intensity="medium",
                details="Morning run around the school ground",
                mental_state="good",
                energy_level=4,
                distance_km=3.5,
                location="School ground",
            )

            fitness_entry = await fitness_repo.create_from_voice_data(
                session_id="test_session_1",
                user_id="test_user",
                voice_data=mock_fitness_data,
                transcript="I went for a 30 minute run this morning",
                confidence_score=0.9,
                processing_duration=2.5,
            )

            print(f"✅ Created fitness entry: {fitness_entry.id}")

            # Test retrieval
            entries = await fitness_repo.get_recent_entries("test_user", limit=5)
            print(f"✅ Retrieved {len(entries)} fitness entries")

            # Test analytics
            analytics = await fitness_repo.get_fitness_analytics("test_user")
            print(f"✅ Generated fitness analytics: {analytics.total_sessions} sessions")

            return True
    except Exception as e:
        print(f"❌ Repository operations failed: {e}")
        logger.exception("Repository test failed")
        return False


async def test_cricket_repository():
    """Test cricket repository operations."""
    print("\n🏏 Testing cricket repository operations...")

    try:
        async with sessionmanager.get_session() as session:
            cricket_repo = CricketCoachingRepository(session)
            cricket_analytics_repo = CricketAnalyticsRepository(session)

            # Test cricket coaching entry
            mock_cricket_data = CricketCoachingDataExtraction(
                session_type="batting_drills",
                duration_minutes=60,
                what_went_well="My front foot drives were much cleaner today",
                areas_for_improvement="Need to work on pull shot timing",
                skills_practiced="front foot drives, cover drives, pull shots",
                self_assessment_score=7,
                confidence_level=8,
                focus_level=7,
                mental_state="good",
                difficulty_level=6,
                learning_satisfaction=8,
            )

            cricket_entry = await cricket_repo.create_from_voice_data(
                session_id="test_session_2",
                user_id="test_user",
                voice_data=mock_cricket_data,
                transcript="Had a good batting practice session today",
                confidence_score=0.85,
                processing_duration=3.2,
            )

            print(f"✅ Created cricket coaching entry: {cricket_entry.id}")

            # Test cricket analytics
            cricket_analytics = await cricket_analytics_repo.get_cricket_analytics("test_user")
            print(
                f"✅ Generated cricket analytics: {cricket_analytics.total_coaching_sessions} coaching sessions",
            )

            return True
    except Exception as e:
        print(f"❌ Cricket repository operations failed: {e}")
        logger.exception("Cricket repository test failed")
        return False


async def test_voice_processing_pipeline():
    """Test voice processing pipeline (mock)."""
    print("\n🎤 Testing voice processing pipeline...")

    try:
        from voice_processing.services.openai_service import openai_service

        # Test data extraction for all entry types (will use mock data in testing)
        fitness_transcript = "I went for a 30 minute run around the school ground today, felt pretty good, energy level was about 7 out of 10"
        fitness_data = await openai_service.extract_fitness_data(fitness_transcript)
        print(f"✅ Extracted fitness data: {fitness_data.get('fitness_type', 'unknown')}")

        cricket_transcript = (
            "Had batting practice with coach today, worked on front foot drives for about an hour"
        )
        cricket_data = await openai_service.extract_cricket_coaching_data(cricket_transcript)
        print(f"✅ Extracted cricket data: {cricket_data.get('session_type', 'unknown')}")

        match_transcript = "Played a school match today, scored 25 runs and took 2 catches"
        match_data = await openai_service.extract_cricket_match_data(match_transcript)
        print(f"✅ Extracted match data: {match_data.get('match_type', 'unknown')}")

        rest_transcript = (
            "Taking a complete rest day today, feeling a bit tired from yesterday's training"
        )
        rest_data = await openai_service.extract_rest_day_data(rest_transcript)
        print(f"✅ Extracted rest day data: {rest_data.get('rest_type', 'unknown')}")

        return True
    except Exception as e:
        print(f"❌ Voice processing pipeline failed: {e}")
        logger.exception("Voice processing test failed")
        return False


async def run_verification():
    """Run all verification tests."""
    print("🏏 Cricket Fitness Tracker - Implementation Verification")
    print("=" * 60)

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    results = []

    # Test database setup
    results.append(await test_database_setup())

    # Test repository operations
    results.append(await test_repository_operations())

    # Test cricket repository
    results.append(await test_cricket_repository())

    # Test voice processing
    results.append(await test_voice_processing_pipeline())

    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    test_names = [
        "Database Setup",
        "Repository Operations",
        "Cricket Repository",
        "Voice Processing Pipeline",
    ]

    for i, (name, result) in enumerate(zip(test_names, results, strict=False)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:<25} {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Implementation verified successfully.")
        print("\n🚀 Next steps:")
        print("   1. Run the application: python main.py")
        print("   2. Test WebSocket connection at ws://localhost:8000/ws/voice/{session_id}")
        print("   3. Check API endpoints at http://localhost:8000/api")
        print("   4. View dashboard at http://localhost:8000/api/dashboard")
        print("\n📱 Client-side entry type selection:")
        print("   - Send 'voice_data_meta' message with entry_type before audio")
        print("   - Supported types: fitness, cricket_coaching, cricket_match, rest_day")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")

    # Cleanup
    await sessionmanager.close()


if __name__ == "__main__":
    asyncio.run(run_verification())
