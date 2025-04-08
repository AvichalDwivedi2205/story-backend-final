from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

from agents.gratitude_agent import GratitudeAgent
from models.data_models import AgentResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gratitude", tags=["Gratitude"])

# Initialize agent with webhook URL (will be updated in main.py)
_gratitude_agent = None

class GratitudeRequest(BaseModel):
    user_id: str
    journal_text: Optional[str] = None
    key_themes: Optional[List[str]] = None
    dominant_emotion: Optional[str] = "neutral"

def get_gratitude_agent():
    if _gratitude_agent is None:
        raise HTTPException(status_code=500, detail="Gratitude agent not initialized")
    return _gratitude_agent

@router.post("/generate", response_model=AgentResponse)
async def generate_gratitude_exercise(request: GratitudeRequest, agent: GratitudeAgent = Depends(get_gratitude_agent)):
    """Generate a personalized gratitude exercise"""
    try:
        gratitude_text = agent.generate_gratitude_exercise(
            request.user_id, 
            request.journal_text, 
            request.key_themes, 
            request.dominant_emotion
        )
        
        # Update user exercises with the generated gratitude exercise
        success = agent.update_user_exercises(request.user_id, gratitude_text)
        
        if success:
            return AgentResponse(
                success=True,
                data={"gratitude_exercise": gratitude_text},
                message="Gratitude exercise generated successfully"
            )
        else:
            return AgentResponse(
                success=False,
                data={"gratitude_exercise": gratitude_text},
                message="Generated gratitude exercise but failed to update user data"
            )
    except Exception as e:
        logger.error(f"Error generating gratitude exercise: {e}")
        return AgentResponse(
            success=False,
            data={},
            message=f"Error generating gratitude exercise: {str(e)}"
        )

@router.post("/webhook", response_model=Dict[str, Any])
async def gratitude_webhook(request: Request, agent: GratitudeAgent = Depends(get_gratitude_agent)):
    """Webhook endpoint for the Gratitude Agent"""
    try:
        data = await request.body()
        data_str = data.decode("utf-8")
        
        return agent.handle_webhook(data_str)
    except Exception as e:
        logger.error(f"Error processing gratitude webhook: {e}")
        return {"status": "error", "message": str(e)}

def init_agent(webhook_url: str):
    """Initialize the Gratitude Agent with the correct webhook URL"""
    global _gratitude_agent
    _gratitude_agent = GratitudeAgent(webhook_url)
    
    # Register the agent with Agentverse
    success = _gratitude_agent.register_with_agentverse()
    if success:
        logger.info(f"Gratitude agent registered with address: {_gratitude_agent.address}")
    else:
        logger.error("Failed to register gratitude agent with Agentverse")
        
    return _gratitude_agent