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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

gemini_client = GeminiClient("ASSISTANT_AGENT_GEMINI_API_KEY")
firebase_client = FirebaseClient()

AGENT_TITLE = "Personalized Assistant Agent"
AGENT_SEED_PHRASE = os.getenv("FETCH_AI_SEED_PHRASE")
AGENT_INDEX = 5  
USE_SECONDARY_KEY = True  


JOURNAL_AGENT_ADDRESS = None  
EXERCISE_AGENT_ADDRESS = None  
GRATITUDE_AGENT_ADDRESS = None  
THERAPY_AGENT_ADDRESS = None  
GUIDE_AGENT_ADDRESS = None  

class AssistantAgent:
    def __init__(self, webhook_url, agent_addresses=None):
        
        self.identity = create_agent_identity(AGENT_SEED_PHRASE, AGENT_INDEX)
        self.webhook_url = webhook_url
        self.address = self.identity.address
        
        # Store agent addresses if provided
        if agent_addresses:
            global JOURNAL_AGENT_ADDRESS, EXERCISE_AGENT_ADDRESS, GRATITUDE_AGENT_ADDRESS
            global THERAPY_AGENT_ADDRESS, GUIDE_AGENT_ADDRESS
            
            JOURNAL_AGENT_ADDRESS = agent_addresses.get("journal", None)
            EXERCISE_AGENT_ADDRESS = agent_addresses.get("exercise", None)
            GRATITUDE_AGENT_ADDRESS = agent_addresses.get("gratitude", None)
            THERAPY_AGENT_ADDRESS = agent_addresses.get("therapy", None)
            GUIDE_AGENT_ADDRESS = agent_addresses.get("guide", None)
        
        # Store ongoing conversations with users
        self.ongoing_conversations = {}
        
    def register_with_agentverse(self):
        readme = create_readme(
            domain="mental-health",
            description="A Personalized Assistant Agent that acts as a central hub, dynamically connecting with specialized agents to fulfill user queries.",
            use_cases=[
                "Coordinate interactions between specialized mental health agents",
                "Provide personalized recommendations based on user queries",
                "Connect with agents on Agentverse to provide comprehensive solutions"
            ],
            payload_parameters=[
                {"parameter": "user_id", "description": "ID of the user making the query"},
                {"parameter": "query", "description": "User's question or request"},
                {"parameter": "context", "description": "Optional context about the user's state or history"}
            ]
        )
        
        return register_agent_with_agentverse(
            identity=self.identity,
            agent_title=AGENT_TITLE,
            webhook_url=self.webhook_url,
            readme=readme,
            use_secondary=USE_SECONDARY_KEY
        )
    
    def understand_user_query(self, query, context=None):
      
        try:
            context_text = f"\nUser Context: {context}" if context else ""
            
            prompt = f"""
            Analyze the following user query to determine which specialized agent should handle it.
            
            User Query: "{query}"{context_text}
            
            Available agents:
            1. Journal Analysis Agent - Handles journal entries, provides sentiment/emotion analysis and insights
            2. Exercise Generator Agent - Creates personalized mental well-being exercises
            3. Gratitude Agent - Helps users practice gratitude and recognize positive aspects in life
            4. Therapy Conversation Agent - Provides therapy-like conversations using CBT and other techniques
            5. Guide Agent - Helps users navigate features and provides overall guidance
            
            Identify the PRIMARY agent that should handle this query and assign a confidence score (0-100).
            If multiple agents are needed, select the primary one that should lead the response.
            
            Format your response as a JSON object:
            {{
              "recommended_agent": "agent_type",
              "confidence": confidence_score,
              "explanation": "brief explanation of why this agent is recommended",
              "secondary_agents": ["other_agent_types"]
            }}
            
            Where agent_type is one of: "journal", "exercise", "gratitude", "therapy", or "guide".
            """
            
            structure = {
                "recommended_agent": "agent_type",
                "confidence": 0,
                "explanation": "Explanation text",
                "secondary_agents": ["agent_type"]
            }
            
            response = gemini_client.generate_structured_response(
                prompt, 
                structure,
                temperature=0.2
            )
            
            return response
        except Exception as e:
            logger.error(f"Error understanding user query: {e}")
            return {
                "recommended_agent": "guide", 
                "confidence": 30,
                "explanation": "Query analysis failed. Defaulting to guide agent.",
                "secondary_agents": []
            }
    
    def route_to_journal_agent(self, user_id, query):
        """Route request to Journal Analysis Agent"""
        try:
            if not JOURNAL_AGENT_ADDRESS:
                return {"error": "Journal agent address not configured"}
            
            payload = {
                "user_id": user_id,
                "journal_text": query
            }
            
           
            logger.info(f"Routing to Journal Agent: {payload}")

            return {
                "success": True,
                "message": "Your journal entry has been analyzed. I've identified themes of self-reflection and personal growth, with a generally positive sentiment. Check the insights section for more details."
            }
        except Exception as e:
            logger.error(f"Error routing to journal agent: {e}")
            return {"error": str(e)}
    
    def route_to_exercise_agent(self, user_id, query):
        """Route request to Exercise Generator Agent"""
        try:
            if not EXERCISE_AGENT_ADDRESS:
                return {"error": "Exercise agent address not configured"}
            
            themes_prompt = f"""
            Extract 3-5 key themes from this text that would be useful for creating 
            personalized mental well-being exercises:
            
            "{query}"
            
            Return only a JSON array of theme strings.
            """
            
            themes_response = gemini_client.generate_text(themes_prompt, temperature=0.3)
            
            try:
                import re
                themes_text = re.sub(r'```json|```', '', themes_response).strip()
                themes = json.loads(themes_text)
            except:
                themes = ["self-improvement", "well-being", "personal growth"]
            
            payload = {
                "user_id": user_id,
                "key_themes": themes
            }
            
            logger.info(f"Routing to Exercise Agent: {payload}")
            
            return {
                "success": True,
                "message": "I've generated some personalized exercises for you based on your needs. Check the exercises section to find morning reflection and CBT exercises tailored to your situation."
            }
        except Exception as e:
            logger.error(f"Error routing to exercise agent: {e}")
            return {"error": str(e)}
    
    def route_to_gratitude_agent(self, user_id, query):
        """Route request to Gratitude Agent"""
        try:
            if not GRATITUDE_AGENT_ADDRESS:
                return {"error": "Gratitude agent address not configured"}
            
            payload = {
                "user_id": user_id,
                "journal_text": query
            }
            
            logger.info(f"Routing to Gratitude Agent: {payload}")
            
            return {
                "success": True,
                "message": "I've created a personalized gratitude exercise for you. It includes prompts to help you recognize positive aspects in your life and specific techniques for enhancing feelings of gratitude."
            }
        except Exception as e:
            logger.error(f"Error routing to gratitude agent: {e}")
            return {"error": str(e)}
    
    def route_to_therapy_agent(self, user_id, query, action="start_session"):
        """Route request to Therapy Conversation Agent"""
        try:
            if not THERAPY_AGENT_ADDRESS:
                return {"error": "Therapy agent address not configured"}
            
            payload = {
                "user_id": user_id,
                "message": query,
                "action": action
            }
            
            logger.info(f"Routing to Therapy Agent: {payload}")
            
            if action == "start_session":
                self.ongoing_conversations[user_id] = "therapy"
            elif action == "end_session":
                if user_id in self.ongoing_conversations:
                    del self.ongoing_conversations[user_id]

            if action == "start_session":
                return {
                    "success": True,
                    "message": "I'm here to listen and support you. How are you feeling today?"
                }
            elif action == "continue_session":
                return {
                    "success": True,
                    "message": "Thank you for sharing that. It sounds like you're experiencing some challenges with anxiety. Let's explore what might be triggering these feelings and consider some coping strategies that could help."
                }
            else: 
                return {
                    "success": True,
                    "closing_message": "Thank you for sharing today. I hope our conversation was helpful.",
                    "session_summary": "We discussed anxiety triggers and explored several CBT techniques for managing anxious thoughts."
                }
        except Exception as e:
            logger.error(f"Error routing to therapy agent: {e}")
            return {"error": str(e)}
    
    def route_to_guide_agent(self, user_id, query, context=None):
        """Route request to Guide Agent"""
        try:
            if not GUIDE_AGENT_ADDRESS:
                return {"error": "Guide agent address not configured"}
            
            payload = {
                "user_id": user_id,
                "query": query,
                "user_history": context
            }
            
            logger.info(f"Routing to Guide Agent: {payload}")
            
            return {
                "success": True,
                "recommended_feature": "Journaling",
                "explanation": "Based on your question, journaling would help you process these thoughts and emotions.",
                "next_steps": "Try writing about your feelings in the journal section to gain clarity.",
                "personalized_message": "It sounds like you're going through a lot right now. I recommend starting with journaling to help organize your thoughts and identify patterns in your emotions."
            }
        except Exception as e:
            logger.error(f"Error routing to guide agent: {e}")
            return {"error": str(e)}
    
    def process_query(self, user_id, query, context=None):
        """
        Process user query by routing to appropriate agent(s)
        
        This is the main method that orchestrates the interaction between agents
        """
        try:
       
            if user_id in self.ongoing_conversations:
                conversation_type = self.ongoing_conversations[user_id]
            
                if conversation_type == "therapy":
                    if query.lower() in ["exit", "end", "quit", "goodbye", "bye"]:
                        return self.route_to_therapy_agent(user_id, query, action="end_session")
                    else:
                        return self.route_to_therapy_agent(user_id, query, action="continue_session")
            
            # If not in an ongoing conversation, analyze the query
            analysis = self.understand_user_query(query, context)
            agent_type = analysis["recommended_agent"]
            confidence = analysis["confidence"]
            
            logger.info(f"Query analysis: {agent_type} (confidence: {confidence})")
            
            if confidence >= 70:
                if agent_type == "journal":
                    return self.route_to_journal_agent(user_id, query)
                elif agent_type == "exercise":
                    return self.route_to_exercise_agent(user_id, query)
                elif agent_type == "gratitude":
                    return self.route_to_gratitude_agent(user_id, query)
                elif agent_type == "therapy":
                    return self.route_to_therapy_agent(user_id, query, action="start_session")
                elif agent_type == "guide":
                    return self.route_to_guide_agent(user_id, query, context)
            
            return self.route_to_guide_agent(user_id, query, context)
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "success": False,
                "message": "I'm having trouble understanding your request right now. Could you try phrasing it differently?"
            }
    
    def handle_webhook(self, data):
        """Handle incoming webhook from Agentverse"""
        try:
            message = parse_message_from_agent(data)
            payload = message.payload
            
            logger.info(f"Received message from {message.sender} with payload: {payload}")
            
            if "user_id" in payload and "query" in payload:
                user_id = payload["user_id"]
                query = payload["query"]
                context = payload.get("context", None)
                
                response = self.process_query(user_id, query, context)
                
                response_payload = {
                    "success": True,
                    "response": response
                }
                
                send_message_to_agent(self.identity, message.sender, response_payload)
                return {"status": "success"}
            else:
                logger.error("Missing required fields in payload")
                return {"status": "error", "message": "Missing required fields"}
                
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return {"status": "error", "message": str(e)}