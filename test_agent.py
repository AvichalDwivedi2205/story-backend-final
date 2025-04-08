import os
import sys
import json
import logging
import asyncio
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# API base URL (assuming FastAPI server is running locally on port 8000)
BASE_URL = "http://localhost:8000"

async def test_assistant_agent():
    """Test the Assistant Agent functionality"""
    print("\n=== Testing Assistant Agent ===")
    
    # Test user query for routing to therapy agent
    test_user_id = "test_user_123"
    
    query_payload = {
        "user_id": test_user_id,
        "query": "I've been feeling anxious and overwhelmed lately. Can we talk about it?",
        "context": "Previous interactions: User has been journaling about work stress."
    }
    
    try:
        print(f"Sending query: {query_payload['query']}")
        response = requests.post(
            f"{BASE_URL}/api/assistant/query",
            json=query_payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nResponse Status: {'Success' if result.get('success') else 'Failed'}")
            print(f"Message: {result.get('message')}")
            print("\nResponse Data:")
            print(json.dumps(result.get('data', {}), indent=2))
        else:
            print(f"Error: Status code {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"Error testing assistant agent: {e}")

async def test_therapy_agent():
    """Test the Therapy Agent functionality directly"""
    print("\n=== Testing Therapy Agent ===")
    
    test_user_id = "test_user_123"
    
    # Step 1: Start a therapy session
    try:
        print("Starting therapy session...")
        start_payload = {
            "user_id": test_user_id,
            "action": "start_session"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/therapy/session",
            json=start_payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nSession started: {'Success' if result.get('success') else 'Failed'}")
            print(f"Initial message: {result.get('data', {}).get('message')}")
        else:
            print(f"Error: Status code {response.status_code}")
            print(response.text)
            return
            
        # Step 2: Continue the session with a message
        print("\nContinuing therapy session...")
        continue_payload = {
            "user_id": test_user_id,
            "action": "continue_session",
            "message": "I've been feeling really anxious about work lately. There's so much pressure and I'm not sleeping well."
        }
        
        response = requests.post(
            f"{BASE_URL}/api/therapy/session",
            json=continue_payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nResponse: {'Success' if result.get('success') else 'Failed'}")
            print(f"Therapist: {result.get('data', {}).get('message')}")
        else:
            print(f"Error: Status code {response.status_code}")
            print(response.text)
            
        # Step 3: End the session
        print("\nEnding therapy session...")
        end_payload = {
            "user_id": test_user_id,
            "action": "end_session"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/therapy/session",
            json=end_payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nSession ended: {'Success' if result.get('success') else 'Failed'}")
            print(f"Closing message: {result.get('data', {}).get('closing_message')}")
            print(f"\nSession summary:\n{result.get('data', {}).get('session_summary')}")
        else:
            print(f"Error: Status code {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error testing therapy agent: {e}")

async def main():
    """Run all tests"""
    print("Starting agent tests...\n")
    
    # Test each agent
    await test_assistant_agent()
    await test_therapy_agent()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    asyncio.run(main())