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
from models.data_models import TherapyMessage, TherapySession

from langchain.memory import ConversationBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import ConversationChain

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

gemini_client = GeminiClient("THERAPY_AGENT_GEMINI_API_KEY")
firebase_client = FirebaseClient()

AGENT_TITLE = "Therapy Conversation Agent"
AGENT_SEED_PHRASE = os.getenv("FETCH_AI_SEED_PHRASE")
AGENT_INDEX = 3 
USE_SECONDARY_KEY = False

class TherapyAgent:
    def __init__(self, webhook_url):
        """Initialize Therapy Conversation Agent"""
        self.identity = create_agent_identity(AGENT_SEED_PHRASE, AGENT_INDEX)
        self.webhook_url = webhook_url
        self.address = self.identity.address
        self.active_sessions = {} 
        
    def register_with_agentverse(self):
        """Register this agent with Agentverse"""
        readme = create_readme(
            domain="mental-health",
            description="This agent provides context-aware AI therapy sessions using conversational memory.",
            use_cases=[
                "Provide therapeutic conversations using CBT principles",
                "Maintain context across conversation sessions",
                "Generate therapy session summaries"
            ],
            payload_parameters=[
                {"parameter": "user_id", "description": "ID of the user in therapy session"},
                {"parameter": "message", "description": "The user's message in the therapy conversation"},
                {"parameter": "action", "description": "Action to perform (start_session, continue_session, end_session)"}
            ]
        )
        
        return register_agent_with_agentverse(
            identity=self.identity,
            agent_title=AGENT_TITLE,
            webhook_url=self.webhook_url,
            readme=readme,
            use_secondary=USE_SECONDARY_KEY
        )
    
    def initialize_chat_session(self, user_id):
        """Initialize a new therapy chat session with LangChain"""
        try:
            api_key = os.getenv("THERAPY_AGENT_GEMINI_API_KEY")
            memory = ConversationBufferMemory()
            
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                google_api_key=api_key,
                temperature=0.7,
                convert_system_message_to_human=True
            )
            
            system_prompt = """
            You are an empathetic AI therapist specializing in Cognitive Behavioral Therapy (CBT), 
            mindfulness, and self-reflection techniques. Your goal is to help the user explore their 
            thoughts and feelings in a supportive, non-judgmental way.

            Guidelines for your responses:
            1. Use therapeutic techniques from CBT, mindfulness, and positive psychology
            2. Ask thoughtful questions to help users gain insight
            3. Validate emotions while gently challenging unhelpful thought patterns
            4. Suggest practical exercises or techniques when appropriate
            5. Maintain a warm, empathetic tone
            6. Keep responses concise (3-5 sentences)
            7. Never diagnose or replace professional mental health care

            You'll be having a conversation with someone seeking emotional support. Focus on being present, 
            understanding their situation, and offering guidance when helpful.
            """
            
            conversation = ConversationChain(
                llm=llm,
                memory=memory,
                verbose=True
            )
            
            memory.chat_memory.add_user_message("I'd like to start a therapy session.")
            memory.chat_memory.add_ai_message(f"{system_prompt} I'm here to listen and support you. How are you feeling today?")
            
            self.active_sessions[user_id] = {
                "conversation": conversation,
                "messages": [
                    TherapyMessage(content="I'd like to start a therapy session.", is_user=True),
                    TherapyMessage(content="I'm here to listen and support you. How are you feeling today?", is_user=False)
                ]
            }
            
            return "I'm here to listen and support you. How are you feeling today?"
            
        except Exception as e:
            logger.error(f"Error initializing chat session: {e}")
            return "I'm having trouble connecting right now. Please try again in a moment."
    
    def continue_chat_session(self, user_id, message):
        """Continue an existing therapy chat session"""
        try:
            if user_id not in self.active_sessions:
                return self.initialize_chat_session(user_id)
            
            conversation = self.active_sessions[user_id]["conversation"]
            
            self.active_sessions[user_id]["messages"].append(
                TherapyMessage(content=message, is_user=True)
            )
            
            response = conversation.predict(input=message)
            
            self.active_sessions[user_id]["messages"].append(
                TherapyMessage(content=response, is_user=False)
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error continuing chat session: {e}")
            return "I'm having trouble processing that right now. Could you try expressing that differently?"
    
    def end_chat_session(self, user_id):
        """End a therapy session and generate a summary"""
        try:
            if user_id not in self.active_sessions:
                return "No active session to end."
            
            session_messages = self.active_sessions[user_id]["messages"]
            
            conversation_text = ""
            for msg in session_messages:
                role = "User" if msg.is_user else "Therapist"
                conversation_text += f"{role}: {msg.content}\n\n"
       
            summary_prompt = f"""
            As a professional therapist, please review the following therapy conversation and
            provide a concise summary from a therapist's perspective.
            
            Focus on:
            1. Main themes discussed
            2. Emotional state of the client
            3. Insights or breakthroughs
            4. Recommended next steps or areas to explore
            
            Conversation:
            {conversation_text}
            
            Please write a professional therapy session summary in 3-5 paragraphs.
            """
            
            session_summary = gemini_client.generate_text(summary_prompt, temperature=0.3)
            
            therapy_session = TherapySession(
                messages=session_messages,
                session_summary=session_summary,
                user_id=user_id
            )
            
            document_id = firebase_client.save_therapy_session(therapy_session)
            
            if document_id:
                logger.info(f"Therapy session saved with ID: {document_id}")
            else:
                logger.error("Failed to save therapy session")
            
            del self.active_sessions[user_id]
            
            return {
                "closing_message": "Thank you for sharing today. I hope our conversation was helpful. Take care of yourself, and remember to practice some of the techniques we discussed.",
                "session_summary": session_summary
            }
            
        except Exception as e:
            logger.error(f"Error ending chat session: {e}")
            return {
                "closing_message": "Thank you for our conversation today. I hope it was helpful.",
                "session_summary": "Unable to generate session summary."
            }
    
    def handle_webhook(self, data):
        """Handle incoming webhook from Agentverse"""
        try:
            message = parse_message_from_agent(data)
            payload = message.payload
            
            logger.info(f"Received message from {message.sender} with payload: {payload}")
            
            if "user_id" in payload and "action" in payload:
                user_id = payload["user_id"]
                action = payload["action"]
                
                if action == "start_session":
                    response = self.initialize_chat_session(user_id)
                    
                    response_payload = {
                        "success": True,
                        "message": response
                    }
                    
                elif action == "continue_session" and "message" in payload:
                    user_message = payload["message"]
                    response = self.continue_chat_session(user_id, user_message)
                    
                    response_payload = {
                        "success": True,
                        "message": response
                    }
                    
                elif action == "end_session":
                    response = self.end_chat_session(user_id)
                    
                    response_payload = {
                        "success": True,
                        "closing_message": response["closing_message"],
                        "session_summary": response["session_summary"]
                    }
                    
                else:
                    logger.error(f"Invalid action: {action}")
                    response_payload = {
                        "success": False,
                        "message": f"Invalid action: {action}"
                    }
                
                send_message_to_agent(self.identity, message.sender, response_payload)
                return {"status": "success"}
            else:
                logger.error("Missing required fields in payload")
                return {"status": "error", "message": "Missing required fields"}
                
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return {"status": "error", "message": str(e)}