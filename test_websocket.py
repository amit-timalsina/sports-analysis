#!/usr/bin/env python3
"""Simple WebSocket test for the voice processing endpoint."""

import asyncio
import json
import sys
import traceback

import requests
import websockets


async def test_websocket():
    """Test WebSocket connection and message handling."""
    print("🔧 Testing WebSocket connection...")

    # First create a session
    try:
        response = requests.post("http://localhost:8020/api/sessions")
        if response.status_code != 200:
            print(f"❌ Failed to create session: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return None

    session_data = response.json()
    session_id = session_data["data"]["session_id"]
    print(f"✅ Created session: {session_id}")

    # Connect to WebSocket
    uri = f"ws://localhost:8020/ws/voice/{session_id}"

    try:
        async with websockets.connect(uri, timeout=10) as websocket:
            print("✅ WebSocket connected")

            # Wait for welcome message
            try:
                print("⏳ Waiting for welcome message...")
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"📨 Raw message received: {message}")

                try:
                    data = json.loads(message)
                    print(f"📋 Parsed message: {json.dumps(data, indent=2)}")

                    if data.get("type") == "connection_established":
                        print("🎯 Connection established successfully!")
                        print("✅ WebSocket test passed!")
                        return True
                    print(f"❌ Unexpected message type: {data.get('type')}")

                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON: {e}")
                    print(f"Raw message: {message}")

            except TimeoutError:
                print("❌ Timeout waiting for welcome message")

    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ WebSocket connection closed: {e}")
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ WebSocket invalid status: {e}")
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        print(f"Exception type: {type(e)}")
        traceback.print_exc()

    print("❌ WebSocket test failed!")
    return False


if __name__ == "__main__":
    try:
        result = asyncio.run(test_websocket())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
        sys.exit(1)
