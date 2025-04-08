import os
import json
import logging
from dotenv import load_dotenv
from fastapi import APIRouter, Request
from fetchai.communication import parse_message_from_agent, send_message_to_agent
from uagents_core.identity import Identity

from utils.gemini_client import GeminiClient
from utils.agent_utils import create_agent_identity, register_agent_with_agentverse, create_readme
from firebase.firebase_client import FirebaseClient
from models.data_models import Exercise, Exercises

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize Gemini client
gemini_client = GeminiClient("GRATITUDE_AGENT_GEMINI_API_KEY")
firebase_client = FirebaseClient()

# Agent configuration
AGENT_TITLE = "Gratitude Agent"
AGENT_SEED_PHRASE = os.getenv("FETCH_AI_SEED_PHRASE")
AGENT_INDEX = 2  # Using index 2 for Gratitude Agent
USE_SECONDARY_KEY = False

class GratitudeAgent:
    def __init__(self, webhook_url):
        """Initialize Gratitude Agent"""
        self.identity = create_agent_identity(AGENT_SEED_PHRASE, AGENT_INDEX)
        self.webhook_url = webhook_url
        self.address = self.identity.address
        
    def register_with_agentverse(self):
        """Register this agent with Agentverse"""
        readme = create_readme(
            domain="mental-health",
            description="This agent helps users recognize and appreciate positive aspects in their life through gratitude exercises.",
            use_cases=[
                "Generate personalized gratitude exercises based on journal entries",
                "Help users identify things they're grateful for when struggling",
                "Create structured gratitude practices tailored to user's emotional state"
            ],
            payload_parameters=[
                {"parameter": "user_id", "description": "ID of the user for whom gratitude exercise is being generated"},
                {"parameter": "journal_text", "description": "Optional journal text to analyze for gratitude opportunities"},
                {"parameter": "key_themes", "description": "Optional key themes identified in journal entries"},
                {"parameter": "dominant_emotion", "description": "Optional dominant emotion identified in journal analysis"}
            ]
        )
        
        return register_agent_with_agentverse(
            identity=self.identity,
            agent_title=AGENT_TITLE,
            webhook_url=self.webhook_url,
            readme=readme,
            use_secondary=USE_SECONDARY_KEY
        )
    
    def generate_gratitude_exercise(self, user_id, journal_text=None, key_themes=None, dominant_emotion="neutral"):
        """Generate a gratitude exercise based on journal content or themes"""
        try:
            context = ""
            if journal_text:
                context = f"\nThe user wrote this journal entry: {journal_text}"
            elif key_themes:
                context = f"\nThe user's journal entries focus on these themes: {', '.join(key_themes)}"
                
            difficulty_level = ""
            if dominant_emotion in ["sadness", "anger", "fear", "disgust"]:
                difficulty_level = """
                Please note that the user is experiencing challenging emotions, so include specific guidance 
                for finding gratitude during difficult times.
                """
            
            prompt = f"""
            Create a personalized gratitude exercise for someone experiencing {dominant_emotion}.{context}
            {difficulty_level}
            
            The exercise should:
            1. Be specific and actionable
            2. Help the user identify things they're genuinely grateful for
            3. Include thoughtful prompts if they're struggling to think of things
            4. Explain the benefits of gratitude practice
            5. Include a structured format (e.g., writing prompts, reflection questions)
            6. Be written in a warm, encouraging tone
            7. Follow a clear structure with a title, introduction, steps, and conclusion
            8. Be 200-300 words in length
            
            Format the exercise in a clear, structured way that's easy to follow.
            """
            
            # Generate gratitude exercise
            gratitude_exercise_text = gemini_client.generate_text(prompt, temperature=0.7)
            
            return gratitude_exercise_text
        except Exception as e:
            logger.error(f"Error generating gratitude exercise: {e}")
            return "Unable to generate gratitude exercise."
    
    def update_user_exercises(self, user_id, gratitude_exercise_text):
        """Update user exercises with gratitude exercise"""
        try:
            # Get existing exercises
            existing_exercises = firebase_client.get_user_exercises(user_id)
            
            if existing_exercises:
                # Create exercises object with updated gratitude exercise
                exercises = Exercises(
                    morning_reflection=Exercise(**existing_exercises.get("morning_reflection", {"text": "", "completed": False})),
                    gratitude_exercise=Exercise(text=gratitude_exercise_text, completed=False),
                    mindfulness_meditation=Exercise(**existing_exercises.get("mindfulness_meditation", {"text": "", "completed": False})),
                    cbt_exercise=Exercise(**existing_exercises.get("cbt_exercise", {"text": "", "completed": False})),
                    relaxation_techniques=Exercise(**existing_exercises.get("relaxation_techniques", {"text": "", "completed": False}))
                )
            else:
                # Create new exercises object with only gratitude exercise
                exercises = Exercises(
                    morning_reflection=Exercise(text="", completed=False),
                    gratitude_exercise=Exercise(text=gratitude_exercise_text, completed=False),
                    mindfulness_meditation=Exercise(text="", completed=False),
                    cbt_exercise=Exercise(text="", completed=False),
                    relaxation_techniques=Exercise(text="", completed=False)
                )
            
            # Save to Firebase
            success = firebase_client.save_exercises(user_id, exercises)
            
            if success:
                logger.info(f"Gratitude exercise updated for user {user_id}")
            else:
                logger.error(f"Failed to update gratitude exercise for user {user_id}")
                
            return success
        except Exception as e:
            logger.error(f"Error updating user exercises: {e}")
            return False
    
    def handle_webhook(self, data):
        """Handle incoming webhook from Agentverse"""
        try:
            message = parse_message_from_agent(data)
            payload = message.payload
            
            logger.info(f"Received message from {message.sender} with payload: {payload}")
            
            if "user_id" in payload:
                user_id = payload["user_id"]
                journal_text = payload.get("journal_text", None)
                key_themes = payload.get("key_themes", [])
                dominant_emotion = payload.get("dominant_emotion", "neutral")
                
                gratitude_exercise_text = self.generate_gratitude_exercise(
                    user_id, journal_text, key_themes, dominant_emotion
                )
                
                success = self.update_user_exercises(user_id, gratitude_exercise_text)
                
                # Send response back to the requesting agent
                response_payload = {
                    "success": success,
                    "message": "Gratitude exercise generated successfully" if success else "Failed to update gratitude exercise",
                }
                
                send_message_to_agent(self.identity, message.sender, response_payload)
                return {"status": "success" if success else "error"}
            else:
                logger.error("Missing user_id in payload")
                return {"status": "error", "message": "Missing user_id"}
                
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return {"status": "error", "message": str(e)}