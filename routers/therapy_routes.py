from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

from agents.therapy_agent import TherapyAgent
from models.data_models import AgentResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/therapy", tags=["Therapy"])

# Initialize agent with webhook URL (will be updated in main.py)
_therapy_agent = None

class TherapySessionRequest(BaseModel):
    user_id: str
    action: str  # start_session, continue_session, end_session
    message: Optional[str] = None

def get_therapy_agent():
    if _therapy_agent is None:
        raise HTTPException(status_code=500, detail="Therapy agent not initialized")
    return _therapy_agent

@router.post("/session", response_model=AgentResponse)
async def therapy_session(request: TherapySessionRequest, agent: TherapyAgent = Depends(get_therapy_agent)):
    """Handle therapy session actions (start, continue, end)"""
    try:
        if request.action == "start_session":
            response = agent.initialize_chat_session(request.user_id)
            return AgentResponse(
                success=True,
                data={"message": response},
                message="Therapy session started"
            )
        elif request.action == "continue_session":
            if not request.message:
                return AgentResponse(
                    success=False,
                    data={},
                    message="Message is required for continuing a session"
                )
            response = agent.continue_chat_session(request.user_id, request.message)
            return AgentResponse(
                success=True,
                data={"message": response},
                message="Therapy response generated"
            )
        elif request.action == "end_session":
            response = agent.end_chat_session(request.user_id)
            return AgentResponse(
                success=True,
                data={
                    "closing_message": response["closing_message"],
                    "session_summary": response["session_summary"]
                },
                message="Therapy session ended"
            )
        else:
            return AgentResponse(
                success=False,
                data={},
                message=f"Invalid action: {request.action}"
            )
    except Exception as e:
        logger.error(f"Error in therapy session: {e}")
        return AgentResponse(
            success=False,
            data={},
            message=f"Error in therapy session: {str(e)}"
        )

@router.post("/webhook", response_model=Dict[str, Any])
async def therapy_webhook(request: Request, agent: TherapyAgent = Depends(get_therapy_agent)):
    """Webhook endpoint for the Therapy Agent"""
    try:
        data = await request.body()
        data_str = data.decode("utf-8")
        
        return agent.handle_webhook(data_str)
    except Exception as e:
        logger.error(f"Error processing therapy webhook: {e}")
        return {"status": "error", "message": str(e)}

def init_agent(webhook_url: str):
    """Initialize the Therapy Agent with the correct webhook URL"""
    global _therapy_agent
    _therapy_agent = TherapyAgent(webhook_url)
    
    # Register the agent with Agentverse
    success = _therapy_agent.register_with_agentverse()
    if success:
        logger.info(f"Therapy agent registered with address: {_therapy_agent.address}")
    else:
        logger.error("Failed to register therapy agent with Agentverse")
        
    return _therapy_agent