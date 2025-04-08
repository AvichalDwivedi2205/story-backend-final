import os
import sys
import json
import logging
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

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_menu():
    """Display the main menu options"""
    clear_screen()
    print("=== Mental Health Agent Tester ===\n")
    print("1. Test Assistant Agent")
    print("2. Test Therapy Agent")
    print("3. Exit")
    return input("\nSelect an option (1-3): ")

def test_assistant_agent():
    """Interactive test for the Assistant Agent"""
    clear_screen()
    print("=== Assistant Agent Test ===\n")
    
    user_id = input("Enter user ID (default: test_user): ") or "test_user"
    
    while True:
        print("\nEnter your query (or 'exit' to return to main menu):")
        query = input("> ")
        
        if query.lower() == "exit":
            break
            
        context = input("\nOptional context (press Enter to skip): ") or None
        
        payload = {
            "user_id": user_id,
            "query": query,
            "context": context
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/assistant/query",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                print("\n=== RESPONSE ===")
                if result.get("success"):
                    print(json.dumps(result.get("data", {}), indent=2))
                else:
                    print(f"Error: {result.get('message')}")
            else:
                print(f"\nError: Status code {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"\nError: {e}")
            
        input("\nPress Enter to continue...")

def test_therapy_agent():
    """Interactive test for the Therapy Agent"""
    clear_screen()
    print("=== Therapy Agent Test ===\n")
    
    user_id = input("Enter user ID (default: test_user): ") or "test_user"
    
    # Start therapy session
    try:
        start_payload = {
            "user_id": user_id,
            "action": "start_session"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/therapy/session",
            json=start_payload
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"\nTherapist: {result.get('data', {}).get('message')}")
            else:
                print(f"\nError starting session: {result.get('message')}")
                return
        else:
            print(f"\nError: Status code {response.status_code}")
            print(response.text)
            return
    except Exception as e:
        print(f"\nError: {e}")
        return
        
    # Continue conversation
    while True:
        print("\nEnter your message (or 'end' to end session, 'exit' to return to menu):")
        message = input("> ")
        
        if message.lower() == "exit":
            # Exit without ending session
            break
            
        if message.lower() == "end":
            # End the therapy session
            end_payload = {
                "user_id": user_id,
                "action": "end_session"
            }
            
            try:
                response = requests.post(
                    f"{BASE_URL}/api/therapy/session",
                    json=end_payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        print(f"\nTherapist: {result.get('data', {}).get('closing_message')}")
                        print(f"\n=== Session Summary ===\n{result.get('data', {}).get('session_summary')}")
                    else:
                        print(f"\nError ending session: {result.get('message')}")
                else:
                    print(f"\nError: Status code {response.status_code}")
                    print(response.text)
            except Exception as e:
                print(f"\nError: {e}")
                
            break
            
        # Continue session with message
        continue_payload = {
            "user_id": user_id,
            "action": "continue_session",
            "message": message
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/therapy/session",
                json=continue_payload
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"\nTherapist: {result.get('data', {}).get('message')}")
                else:
                    print(f"\nError: {result.get('message')}")
            else:
                print(f"\nError: Status code {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"\nError: {e}")
    
    input("\nPress Enter to continue...")

def main():
    """Main CLI loop"""
    while True:
        choice = display_menu()
        
        if choice == "1":
            test_assistant_agent()
        elif choice == "2":
            test_therapy_agent()
        elif choice == "3":
            print("\nExiting. Goodbye!")
            sys.exit(0)
        else:
            input("Invalid option. Press Enter to try again...")

if __name__ == "__main__":
    main()