import asyncio

import requests

from database.session import get_session
from fitness_tracking.repositories.cricket_match_repository import CricketMatchEntryRepository
from fitness_tracking.schemas.cricket_match import CricketMatchEntryCreate
from fitness_tracking.schemas.enums import MatchFormat

# Configuration
token = "eyJhbGciOiJIUzI1NiIsImtpZCI6IlR6cDluOVBhNGNIVDFyZW8iLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL21saW5hZGdldnBhYWJxcnFnb2diLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI2YzI0YTVjZC0yYmIwLTQ0NjUtOGIxZS1jYWNmY2ZlN2Q1MDkiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzNDMyNTMyLCJpYXQiOjE3NTM0Mjg5MzIsImVtYWlsIjoidGVzdDExMUBnbWFpbC5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsX3ZlcmlmaWVkIjp0cnVlfSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc1MzQyODkzMn1dLCJzZXNzaW9uX2lkIjoiNmRmOTVhODEtOTU4Ni00YjU3LWFlNTYtYWQ1OTc3NDEzOTc4IiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.ulqRY3dS1BI71eQ-G3An7ME8Iz1lCDndawSDcWaRs-E"
BASE_URL = "http://localhost:8020/api"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


conversation_history = []


def send_message(conversation_id, user_message):
    """Send user message to API"""
    # Add context to message if available
    enhanced_message = user_message
    if conversation_history:
        context = "\n".join([f"{msg['sender']}: {msg['text']}" for msg in conversation_history])
        enhanced_message += f"\n\nRecent context:\n{context}"
        print(enhanced_message)

    data = {
        "sender": "USER",
        "conversation_id": conversation_id,
        "user_message": enhanced_message,
        "ai_extraction": {},
        "is_read": True,
        "is_completed": False,
    }

    response = requests.post(f"{BASE_URL}/messages", json=data, headers=headers, timeout=30)
    conversation_history.append({"sender": "USER", "text": user_message})
    return response.json()["id"]


def get_ai_reply(message_id):
    """Get AI response"""
    response = requests.post(f"{BASE_URL}/messages/{message_id}/reply", headers=headers, timeout=30)
    return response.json()


# async def save_database():
#     """Save conversation to database"""
#     async for session in get_session():
#         cricket_match_repo = CricketMatchEntryRepository(session=session)
#         ai_reply = CricketMatchEntryCreate(
#             conversation_id="78bb063f-31c5-4fe2-b98d-5e1e1029062e",
#             mental_state="peace",
#             sender="AI",
#             user_message=None,
#             is_read=True,
#             is_completed=True,
#             # Required cricket match fields
#             match_format=MatchFormat.T20,
#             opposition_team="Test Team",
#             venue="Test Venue",
#             home_away="home",
#             result="won",
#             team_name="My Team",
#         )

#         # Save to database
#         result = await cricket_match_repo.create(ai_reply)
#         return result


async def main():
    """Main conversation loop"""
    print("🏃‍♂️ Cricket Fitness Tracker CLI")
    print("Type 'exit' to save and quit, 'quit' to exit without saving")
    print("-" * 50)

    conversation_id = "0b8ed5e2-3d49-4358-9c92-770b4ad481c0"

    while True:
        user_input = input("\n👤 You: ").strip()

        if user_input.lower() == "quit":
            print("👋 Goodbye!")
            break

        if user_input.lower() == "exit":
            # if save_database(conversation_id):
            #     print("✅ Conversation saved!")
            print("👋 Goodbye!")
            break

        if not user_input:
            continue

        try:
            # Send message and get response
            print("📤 Sending...")
            message_id = send_message(conversation_id, user_input)

            print("🤖 AI thinking...")
            ai_reply = get_ai_reply(message_id)

            # Extract and display AI response
            if "ai_extraction" in ai_reply and "follow_up_question" in ai_reply["ai_extraction"]:
                question = ai_reply["ai_extraction"]["follow_up_question"].get("question", "")
                if question:
                    print(f"\n🤖 AI: {question}")
                    conversation_history.append({"sender": "AI", "text": question})

                    # Check if conversation is complete
                    if ai_reply["ai_extraction"]["follow_up_question"] is None:
                        print("\n✨ Conversation complete! Saving...")
                        # if save_database(conversation_id):
                        #     print("✅ Saved successfully!")
                        break
                else:
                    print("✨ No more questions. Saving...")
                    # if save_database(conversation_id):
                    #     print("✅ Saved successfully!")
                    break
            else:
                # Check if conversation is completed (is_completed = True)
                if ai_reply.get("is_completed", True):
                    print(f"\n🤖 AI: {ai_reply}")
                    print("\n✨ Conversation complete! Auto-saving...")
                    # if save_database(ai_reply):
                    #     print("✅ Saved successfully!")
                    # else:
                    #     print("❌ Failed to save")
                    break
                else:
                    print(f"\n🤖 AI: {ai_reply}")

        except Exception as e:
            print(f"❌ Error: {e}")

        print("-" * 30)
        # print conversation_history

    print(conversation_history)


if __name__ == "__main__":
    asyncio.run(main())
