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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

gemini_client = GeminiClient("GRATITUDE_AGENT_GEMINI_API_KEY")
firebase_client = FirebaseClient()

AGENT_TITLE = "Gratitude Agent"
AGENT_SEED_PHRASE = os.getenv("FETCH_AI_SEED_PHRASE")
AGENT_INDEX = 2 
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
            description="This agent helps users identify things they should be grateful for based on their journal entries.",
            use_cases=[
                "Identify gratitude opportunities in user's journal entries",
                "Help users recognize positive aspects in their life they might have overlooked",
                "Provide personalized gratitude insights based on user's emotional state"
            ],
            payload_parameters=[
                {"parameter": "user_id", "description": "ID of the user for whom gratitude insights are being generated"},
                {"parameter": "journal_text", "description": "Journal text to analyze for gratitude opportunities"},
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
    
    def identify_gratitude_opportunities(self, user_id, journal_text=None, key_themes=None, dominant_emotion="neutral"):
        """Identify things to be grateful for in the user's journal entry"""
        try:
            if not journal_text and not key_themes:
                return "Please provide journal text or key themes to analyze for gratitude opportunities."
                
            context = ""
            if journal_text:
                context = f"\nThe user wrote this journal entry: {journal_text}"
            elif key_themes:
                context = f"\nThe user's journal entries focus on these themes: {', '.join(key_themes)}"
                
            emotional_context = ""
            if dominant_emotion in ["sadness", "anger", "fear", "disgust"]:
                emotional_context = """
                Please note that the user is experiencing challenging emotions, so be especially thoughtful 
                about finding positive aspects they might be overlooking.
                """
            
            prompt = f"""
            Analyze this journal entry and identify specific things the user can be grateful for.{context}
            {emotional_context}

            Your job is to help the user see specific things from their day or life that they can appreciate, even if they didn't explicitly recognize them in their journaling.
            
            Your response should:
            1. Find 3-5 concrete things to be grateful for based on what's directly mentioned or implied in their journal
            2. For each identified item, explain why it's worth appreciating and how it positively impacts their life
            3. Be empathetic and personal, connecting to the user's specific situation
            4. If the journal contains mostly negative content, identify small positives, capabilities, or resources they might be taking for granted
            5. Be authentic and thoughtful - don't force positivity where it doesn't fit
            
            Format your response as a warm, conversational message that feels like it's coming from a supportive friend.
            Begin with a brief acknowledgment of their feelings, then gently direct their attention to the positive elements you've identified.
            End with a brief encouraging note.
            Avoid using numbered lists - integrate the gratitude points naturally into your message.
            Keep the total response between 200-300 words.
            """
            
            gratitude_insights = gemini_client.generate_text(prompt, temperature=0.7)
            
            return gratitude_insights
        except Exception as e:
            logger.error(f"Error identifying gratitude opportunities: {e}")
            return "Unable to identify gratitude opportunities in your journal entry."
    
    def update_user_exercises(self, user_id, gratitude_text):
        """Update user exercises with gratitude insights"""
        try:
            existing_exercises = firebase_client.get_user_exercises(user_id)
            
            if existing_exercises:
                exercises = Exercises(
                    morning_reflection=Exercise(**existing_exercises.get("morning_reflection", {"text": "", "completed": False})),
                    gratitude_exercise=Exercise(text=gratitude_text, completed=False),
                    mindfulness_meditation=Exercise(**existing_exercises.get("mindfulness_meditation", {"text": "", "completed": False})),
                    cbt_exercise=Exercise(**existing_exercises.get("cbt_exercise", {"text": "", "completed": False})),
                    relaxation_techniques=Exercise(**existing_exercises.get("relaxation_techniques", {"text": "", "completed": False}))
                )
            else:
                exercises = Exercises(
                    morning_reflection=Exercise(text="", completed=False),
                    gratitude_exercise=Exercise(text=gratitude_text, completed=False),
                    mindfulness_meditation=Exercise(text="", completed=False),
                    cbt_exercise=Exercise(text="", completed=False),
                    relaxation_techniques=Exercise(text="", completed=False)
                )
            
            success = firebase_client.save_exercises(user_id, exercises)
            
            if success:
                logger.info(f"Gratitude insights updated for user {user_id}")
            else:
                logger.error(f"Failed to update gratitude insights for user {user_id}")
                
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
                
                gratitude_insights = self.identify_gratitude_opportunities(
                    user_id, journal_text, key_themes, dominant_emotion
                )
                
                success = self.update_user_exercises(user_id, gratitude_insights)
                
                response_payload = {
                    "success": success,
                    "message": "Gratitude insights generated successfully" if success else "Failed to update gratitude insights",
                }
                
                send_message_to_agent(self.identity, message.sender, response_payload)
                return {"status": "success" if success else "error"}
            else:
                logger.error("Missing user_id in payload")
                return {"status": "error", "message": "Missing user_id"}
                
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return {"status": "error", "message": str(e)}