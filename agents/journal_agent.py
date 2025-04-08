import os
import json
import logging
from dotenv import load_dotenv
from fastapi import APIRouter, Request
from fetchai.communication import parse_message_from_agent, send_message_to_agent
from uagents_core.identity import Identity

from utils.gemini_client import GeminiClient
from utils.agent_utils import (
    analyze_sentiment, analyze_emotions, create_agent_identity, 
    register_agent_with_agentverse, create_readme
)
from firebase.firebase_client import FirebaseClient
from models.data_models import JournalEntry, SentimentAnalysis, EmotionAnalysis, JournalInsight, JournalAnalysis

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

gemini_client = GeminiClient("JOURNAL_AGENT_GEMINI_API_KEY")
firebase_client = FirebaseClient()

AGENT_TITLE = "Journal Analysis Agent"
AGENT_SEED_PHRASE = os.getenv("FETCH_AI_SEED_PHRASE")
AGENT_INDEX = 0 
USE_SECONDARY_KEY = False

class JournalAgent:
    def __init__(self, webhook_url):
        """Initialize Journal Analysis Agent"""
        self.identity = create_agent_identity(AGENT_SEED_PHRASE, AGENT_INDEX)
        self.webhook_url = webhook_url
        self.address = self.identity.address
        
    def register_with_agentverse(self):
        """Register this agent with Agentverse"""
        readme = create_readme(
            domain="mental-health",
            description="This agent analyzes journal entries, detects emotions and sentiments, and provides therapeutic insights.",
            use_cases=[
                "Process and analyze personal journal entries",
                "Detect emotions and sentiments in text",
                "Generate therapeutic insights and actionable advice"
            ],
            payload_parameters=[
                {"parameter": "journal_text", "description": "The journal entry text to analyze"},
                {"parameter": "user_id", "description": "ID of the user whose journal is being analyzed"}
            ]
        )
        
        return register_agent_with_agentverse(
            identity=self.identity,
            agent_title=AGENT_TITLE,
            webhook_url=self.webhook_url,
            readme=readme,
            use_secondary=USE_SECONDARY_KEY
        )
    
    def analyze_journal(self, journal_text, user_id):
        """Analyze a journal entry and generate insights"""
        try:
            journal_entry = JournalEntry(
                content=journal_text,
                user_id=user_id
            )
            
            sentiment_result = analyze_sentiment(journal_text)
            sentiment_analysis = SentimentAnalysis(
                score=sentiment_result["score"],
                label=sentiment_result["label"]
            )
            
            emotion_result = analyze_emotions(journal_text)
            emotion_analysis = EmotionAnalysis(
                emotions=emotion_result["emotions"],
                dominant_emotion=emotion_result["dominant_emotion"]
            )
            
            insights_prompt = f"""
            Please analyze the following journal entry and provide therapeutic insights.
            
            Journal Entry: {journal_text}
            
            Sentiment: {sentiment_analysis.label} (Score: {sentiment_analysis.score:.2f})
            Dominant Emotion: {emotion_analysis.dominant_emotion}
            
            Provide a compassionate, therapeutic analysis that includes:
            1. A brief summary of the journal entry
            2. Key themes present in the text
            3. Any cognitive distortions that might be present
            4. Growth indicators or positive aspects
            5. Thoughtful reflection questions for the writer
            6. Practical, actionable advice
            """
            
            insights_structure = {
                "summary": "A concise summary of the journal entry",
                "key_themes": ["Theme 1", "Theme 2", "Theme 3"],
                "cognitive_distortions": ["Distortion 1", "Distortion 2"],
                "growth_indicators": ["Growth indicator 1", "Growth indicator 2"],
                "reflection_questions": ["Question 1?", "Question 2?", "Question 3?"],
                "actionable_advice": ["Advice 1", "Advice 2", "Advice 3"]
            }
            
            insights_response = gemini_client.generate_structured_response(
                insights_prompt, 
                insights_structure,
                temperature=0.2
            )
            
            journal_insight = JournalInsight(
                summary=insights_response.get("summary", "Summary not available"),
                key_themes=insights_response.get("key_themes", []),
                cognitive_distortions=insights_response.get("cognitive_distortions", []),
                growth_indicators=insights_response.get("growth_indicators", []),
                reflection_questions=insights_response.get("reflection_questions", []),
                actionable_advice=insights_response.get("actionable_advice", [])
            )
            
            journal_analysis = JournalAnalysis(
                journal_entry=journal_entry,
                sentiment_analysis=sentiment_analysis,
                emotion_analysis=emotion_analysis,
                insights=journal_insight
            )
            
            document_id = firebase_client.save_journal_entry(
                user_id=user_id,
                journal_data=journal_analysis.dict()
            )
            
            logger.info(f"Journal analysis saved with ID: {document_id}")
            
            self.trigger_exercise_generator(user_id, journal_insight)
            
            return journal_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing journal: {e}")
            raise
    
    def trigger_exercise_generator(self, user_id, journal_insight):
        """Trigger the Exercise Generator Agent with journal insights"""
        try:
            logger.info(f"Triggering Exercise Generator Agent for user {user_id}")
            
            return True
        except Exception as e:
            logger.error(f"Error triggering exercise generator: {e}")
            return False
    
    def handle_webhook(self, data):
        """Handle incoming webhook from Agentverse"""
        try:
            message = parse_message_from_agent(data)
            payload = message.payload
            
            logger.info(f"Received message from {message.sender} with payload: {payload}")
            
            if "journal_text" in payload and "user_id" in payload:
                journal_text = payload["journal_text"]
                user_id = payload["user_id"]
                
                journal_analysis = self.analyze_journal(journal_text, user_id)
                
                response_payload = {
                    "success": True,
                    "message": "Journal analysis completed successfully",
                    "sentiment": journal_analysis.sentiment_analysis.label,
                    "dominant_emotion": journal_analysis.emotion_analysis.dominant_emotion,
                }
                
                send_message_to_agent(self.identity, message.sender, response_payload)
                return {"status": "success"}
            else:
                logger.error("Missing required fields in payload")
                return {"status": "error", "message": "Missing required fields"}
                
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return {"status": "error", "message": str(e)}