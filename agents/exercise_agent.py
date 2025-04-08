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
gemini_client = GeminiClient("EXERCISE_AGENT_GEMINI_API_KEY")
firebase_client = FirebaseClient()

# Agent configuration
AGENT_TITLE = "Exercise Generator Agent"
AGENT_SEED_PHRASE = os.getenv("FETCH_AI_SEED_PHRASE")
AGENT_INDEX = 1  # Using index 1 for Exercise Generator Agent
USE_SECONDARY_KEY = False

class ExerciseAgent:
    def __init__(self, webhook_url):
        """Initialize Exercise Generator Agent"""
        self.identity = create_agent_identity(AGENT_SEED_PHRASE, AGENT_INDEX)
        self.webhook_url = webhook_url
        self.address = self.identity.address
        
    def register_with_agentverse(self):
        """Register this agent with Agentverse"""
        readme = create_readme(
            domain="mental-health",
            description="This agent generates customized exercises based on journal insights to improve mental well-being.",
            use_cases=[
                "Generate morning reflection exercises based on journal themes",
                "Create CBT exercises to challenge negative thoughts",
                "Customize exercises based on user's emotional state and cognitive patterns"
            ],
            payload_parameters=[
                {"parameter": "user_id", "description": "ID of the user for whom exercises are being generated"},
                {"parameter": "key_themes", "description": "Key themes identified in journal entries"},
                {"parameter": "cognitive_distortions", "description": "Cognitive distortions identified in journal entries"},
                {"parameter": "dominant_emotion", "description": "Dominant emotion identified in journal analysis"}
            ]
        )
        
        return register_agent_with_agentverse(
            identity=self.identity,
            agent_title=AGENT_TITLE,
            webhook_url=self.webhook_url,
            readme=readme,
            use_secondary=USE_SECONDARY_KEY
        )
    
    def generate_morning_reflection(self, user_id, key_themes, dominant_emotion):
        """Generate a morning reflection exercise based on journal themes"""
        try:
            prompt = f"""
            Create a morning reflection exercise tailored to someone experiencing {dominant_emotion} 
            and focused on the following themes from their journal: {', '.join(key_themes)}.
            
            The exercise should:
            1. Be specific and actionable
            2. Take 5-10 minutes to complete
            3. Include step-by-step instructions
            4. Have a clear purpose/benefit
            5. Be written in a warm, encouraging tone
            6. Follow a clear structure with a title, introduction, steps, and conclusion
            7. Be 200-300 words in length
            
            Format the exercise in a clear, structured way that's easy to follow.
            """
            
            # First API call to generate morning reflection
            morning_reflection_text = gemini_client.generate_text(prompt, temperature=0.7)
            
            return morning_reflection_text
        except Exception as e:
            logger.error(f"Error generating morning reflection: {e}")
            return "Unable to generate morning reflection exercise."
    
    def generate_cbt_exercise(self, user_id, cognitive_distortions, dominant_emotion):
        """Generate a CBT exercise to challenge negative thoughts"""
        try:
            prompt = f"""
            Create a Cognitive Behavioral Therapy (CBT) exercise tailored to someone experiencing {dominant_emotion} 
            and showing these cognitive distortions: {', '.join(cognitive_distortions)}.
            
            The exercise should:
            1. Be specific and actionable
            2. Focus on identifying and challenging negative thought patterns
            3. Include a thought record template or similar structured approach
            4. Take 10-15 minutes to complete
            5. Be written in a supportive, non-judgmental tone
            6. Follow a clear structure with a title, introduction, steps, and conclusion
            7. Be 200-300 words in length
            
            Format the exercise in a clear, structured way that's easy to follow.
            """
            
            # Second API call to generate CBT exercise
            cbt_exercise_text = gemini_client.generate_text(prompt, temperature=0.7)
            
            return cbt_exercise_text
        except Exception as e:
            logger.error(f"Error generating CBT exercise: {e}")
            return "Unable to generate CBT exercise."
    
    def generate_exercises(self, user_id, key_themes=None, cognitive_distortions=None, dominant_emotion="neutral"):
        """Generate exercises based on provided insights"""
        try:
            if not key_themes:
                key_themes = ["self-reflection", "personal growth"]
            if not cognitive_distortions:
                cognitive_distortions = ["negative thinking", "overgeneralization"]
                
            # Generate morning reflection
            morning_reflection_text = self.generate_morning_reflection(
                user_id, key_themes, dominant_emotion
            )
            
            # Generate CBT exercise
            cbt_exercise_text = self.generate_cbt_exercise(
                user_id, cognitive_distortions, dominant_emotion
            )
            
            # Create exercises with the generated content
            exercises = Exercises(
                morning_reflection=Exercise(text=morning_reflection_text, completed=False),
                gratitude_exercise=Exercise(text="", completed=False),  # Will be filled by Gratitude Agent
                mindfulness_meditation=Exercise(text="", completed=False),
                cbt_exercise=Exercise(text=cbt_exercise_text, completed=False),
                relaxation_techniques=Exercise(text="", completed=False)
            )
            
            # Save to Firebase
            success = firebase_client.save_exercises(user_id, exercises)
            
            if success:
                logger.info(f"Exercises saved for user {user_id}")
            else:
                logger.error(f"Failed to save exercises for user {user_id}")
            
            # Trigger Gratitude Agent to fill in the gratitude exercise
            self.trigger_gratitude_agent(user_id, key_themes, dominant_emotion)
            
            return exercises
        except Exception as e:
            logger.error(f"Error generating exercises: {e}")
            raise
    
    def trigger_gratitude_agent(self, user_id, key_themes, dominant_emotion):
        """Trigger the Gratitude Agent to generate a gratitude exercise"""
        try:
            logger.info(f"Triggering Gratitude Agent for user {user_id}")
            
            # In a real implementation, this would send a message to the Gratitude Agent
            # via the Agentverse platform
            # gratitude_agent_address = "agent_address_here" 
            # payload = {
            #     "user_id": user_id,
            #     "key_themes": key_themes,
            #     "dominant_emotion": dominant_emotion,
            # }
            # send_message_to_agent(self.identity, gratitude_agent_address, payload)
            
            return True
        except Exception as e:
            logger.error(f"Error triggering gratitude agent: {e}")
            return False
    
    def handle_webhook(self, data):
        """Handle incoming webhook from Agentverse"""
        try:
            message = parse_message_from_agent(data)
            payload = message.payload
            
            logger.info(f"Received message from {message.sender} with payload: {payload}")
            
            if "user_id" in payload:
                user_id = payload["user_id"]
                key_themes = payload.get("key_themes", [])
                cognitive_distortions = payload.get("cognitive_distortions", [])
                dominant_emotion = payload.get("dominant_emotion", "neutral")
                
                exercises = self.generate_exercises(
                    user_id, key_themes, cognitive_distortions, dominant_emotion
                )
                
                # Send response back to the requesting agent
                response_payload = {
                    "success": True,
                    "message": "Exercise generation completed successfully",
                    "morning_reflection_generated": bool(exercises.morning_reflection.text),
                    "cbt_exercise_generated": bool(exercises.cbt_exercise.text)
                }
                
                send_message_to_agent(self.identity, message.sender, response_payload)
                return {"status": "success"}
            else:
                logger.error("Missing user_id in payload")
                return {"status": "error", "message": "Missing user_id"}
                
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return {"status": "error", "message": str(e)}