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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize Gemini client
gemini_client = GeminiClient("GUIDE_AGENT_GEMINI_API_KEY")
firebase_client = FirebaseClient()

# Agent configuration
AGENT_TITLE = "Story.AI Guide Agent"
AGENT_SEED_PHRASE = os.getenv("FETCH_AI_SEED_PHRASE")
AGENT_INDEX = 4  # Using index 4 for Guide Agent
USE_SECONDARY_KEY = True  # Using secondary API key since we're now beyond the first 4 agents

class GuideAgent:
    def __init__(self, webhook_url):
        """Initialize Story.AI Guide Agent"""
        self.identity = create_agent_identity(AGENT_SEED_PHRASE, AGENT_INDEX)
        self.webhook_url = webhook_url
        self.address = self.identity.address
        
    def register_with_agentverse(self):
        """Register this agent with Agentverse"""
        readme = create_readme(
            domain="mental-health",
            description="This agent acts as an intelligent assistant, helping users navigate Story.AI's features and suggesting the most relevant activities based on their specific worries and needs.",
            use_cases=[
                "Guide users through Story.AI's various features",
                "Recommend appropriate mental well-being activities based on user's expressed worries",
                "Connect with other agents on Agentverse to provide comprehensive support"
            ],
            payload_parameters=[
                {"parameter": "user_id", "description": "ID of the user seeking guidance"},
                {"parameter": "query", "description": "User's worry, question, or need statement"}
            ]
        )
        
        return register_agent_with_agentverse(
            identity=self.identity,
            agent_title=AGENT_TITLE,
            webhook_url=self.webhook_url,
            readme=readme,
            use_secondary=USE_SECONDARY_KEY
        )
    
    def recommend_feature(self, user_id, query):
        """Recommend the most suitable Story.AI feature based on user's worries/query"""
        try:
            prompt = f"""
            As the Story.AI Guide, you help users navigate the platform's features based on their expressed worries and needs. 
            Given the following user's concern, recommend the most appropriate feature and provide a supportive, empathetic explanation.
            
            User's concern: "{query}"
            
            Available features in Story.AI:
            1. Journaling - The user can write journal entries and receive analysis of emotions, sentiments, and therapeutic insights about their day with actionable advice.
            2. Exercises - Five types of mental well-being exercises:
               - Morning Reflection: Start the day with mindful intention
               - CBT Exercises: Challenge negative thought patterns
               - Gratitude Practice: Focus on positive aspects of life
               - Mindfulness Meditation: Present-moment awareness
               - Relaxation Techniques: Methods to reduce stress and anxiety
            3. Routine Builder - Create a personalized daily schedule that promotes mental well-being and productivity.
            4. Self-Assessment - Science-based assessments including:
               - PSS (Perceived Stress Scale)
               - Personality Test
               - Anxiety Assessment
            
            Format your response as a JSON object with the following structure:
            {{
              "recommended_feature": "name of the feature", 
              "explanation": "compassionate explanation of why this feature could help with their specific worry",
              "next_steps": "specific next steps for the user to take"
            }}
            """
            
            structure = {
                "recommended_feature": "Feature name",
                "explanation": "Explanation text",
                "next_steps": "Next steps text"
            }
            
            response = gemini_client.generate_structured_response(
                prompt, 
                structure,
                temperature=0.3
            )
            
            return response
        except Exception as e:
            logger.error(f"Error recommending feature: {e}")
            return {
                "recommended_feature": "Journaling",
                "explanation": "I'm having trouble processing your request right now, but journaling can help you explore and understand your feelings better.",
                "next_steps": "Try writing about your specific worries in the journal section, and our AI will provide personalized insights."
            }
    
    def search_agentverse(self, query):
        """
        Search for relevant agents on Agentverse that could help the user.
        
        In a real implementation, this would use the Search and Discover feature
        of Agentverse. For now, we'll simulate this with a predefined response.
        """
        # This would be an actual API call to Agentverse in a real implementation
        logger.info(f"Searching Agentverse for agents relevant to: {query}")
        
        # Simulated response
        external_agents = [
            {
                "agent_name": "Meditation Guide Agent",
                "agent_description": "Guides users through personalized meditation exercises",
                "relevance_score": 0.85 if "meditation" in query.lower() or "stress" in query.lower() else 0.4
            },
            {
                "agent_name": "Sleep Improvement Agent",
                "agent_description": "Provides recommendations for better sleep",
                "relevance_score": 0.9 if "sleep" in query.lower() or "insomnia" in query.lower() else 0.3
            },
            {
                "agent_name": "Exercise Motivation Agent",
                "agent_description": "Helps users stay motivated with physical exercise routines",
                "relevance_score": 0.8 if "exercise" in query.lower() or "motivation" in query.lower() else 0.2
            }
        ]
        
        # Sort by relevance
        sorted_agents = sorted(external_agents, key=lambda x: x["relevance_score"], reverse=True)
        
        # Return the most relevant agents
        return sorted_agents[:2] if sorted_agents else []
    
    def generate_comprehensive_response(self, user_id, query):
        """Generate a comprehensive response that combines Story.AI features and external Agentverse agents"""
        try:
            # Get internal feature recommendation
            feature_recommendation = self.recommend_feature(user_id, query)
            
            # Search Agentverse for relevant external agents
            relevant_agents = self.search_agentverse(query)
            
            # Build comprehensive response
            response = {
                "story_ai_recommendation": feature_recommendation,
                "external_agents": relevant_agents,
                "personalized_message": self.generate_personalized_message(query, feature_recommendation, relevant_agents)
            }
            
            return response
        except Exception as e:
            logger.error(f"Error generating comprehensive response: {e}")
            return {
                "story_ai_recommendation": {
                    "recommended_feature": "Journaling",
                    "explanation": "I'm having trouble processing your request, but journaling can help you explore your feelings.",
                    "next_steps": "Try writing about your specific concerns in the journal section."
                },
                "external_agents": [],
                "personalized_message": "Based on what you've shared, I think our journaling feature could help you work through these feelings and gain new insights."
            }
    
    def generate_personalized_message(self, query, feature_recommendation, relevant_agents):
        """Generate a personalized message combining all recommendations"""
        try:
            external_agent_text = ""
            if relevant_agents:
                agent_names = [agent["agent_name"] for agent in relevant_agents]
                external_agent_text = f" You might also find {' and '.join(agent_names)} helpful for additional support."
            
            message = f"I understand your concern about '{query}'. I recommend trying our {feature_recommendation['recommended_feature']} feature. {feature_recommendation['explanation']}{external_agent_text} {feature_recommendation['next_steps']}"
            return message
        except Exception as e:
            logger.error(f"Error generating personalized message: {e}")
            return "Based on what you've shared, I think our journaling feature could help you work through these feelings and gain new insights."
    
    def handle_webhook(self, data):
        """Handle incoming webhook from Agentverse"""
        try:
            message = parse_message_from_agent(data)
            payload = message.payload
            
            logger.info(f"Received message from {message.sender} with payload: {payload}")
            
            if "user_id" in payload and "query" in payload:
                user_id = payload["user_id"]
                query = payload["query"]
                
                response = self.generate_comprehensive_response(user_id, query)
                
                # Send response back to the requesting agent
                response_payload = {
                    "success": True,
                    "recommended_feature": response["story_ai_recommendation"]["recommended_feature"],
                    "explanation": response["story_ai_recommendation"]["explanation"],
                    "next_steps": response["story_ai_recommendation"]["next_steps"],
                    "external_agents": response["external_agents"],
                    "personalized_message": response["personalized_message"]
                }
                
                send_message_to_agent(self.identity, message.sender, response_payload)
                return {"status": "success"}
            else:
                logger.error("Missing required fields in payload")
                return {"status": "error", "message": "Missing required fields"}
                
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return {"status": "error", "message": str(e)}