from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

from agents.assistant_agent import AssistantAgent
from models.data_models import AgentResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/assistant", tags=["Assistant"])

# Initialize agent with webhook URL (will be updated in main.py)
_assistant_agent = None

class AssistantRequest(BaseModel):
    user_id: str
    query: str
    context: Optional[str] = None

def get_assistant_agent():
    if _assistant_agent is None:
        raise HTTPException(status_code=500, detail="Assistant agent not initialized")
    return _assistant_agent

@router.post("/query", response_model=AgentResponse)
async def process_query(request: AssistantRequest, agent: AssistantAgent = Depends(get_assistant_agent)):
    """Process a user query and route to appropriate specialized agents"""
    try:
        response = agent.process_query(
            request.user_id, 
            request.query, 
            request.context
        )
        
        return AgentResponse(
            success=True,
            data=response,
            message="Query processed successfully"
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return AgentResponse(
            success=False,
            data={},
            message=f"Error processing query: {str(e)}"
        )

@router.post("/webhook", response_model=Dict[str, Any])
async def assistant_webhook(request: Request, agent: AssistantAgent = Depends(get_assistant_agent)):
    """Webhook endpoint for the Assistant Agent"""
    try:
        data = await request.body()
        data_str = data.decode("utf-8")
        
        return agent.handle_webhook(data_str)
    except Exception as e:
        logger.error(f"Error processing assistant webhook: {e}")
        return {"status": "error", "message": str(e)}

def init_agent(webhook_url: str, agent_addresses: Dict[str, str] = None):
    """Initialize the Assistant Agent with the correct webhook URL and agent addresses"""
    global _assistant_agent
    _assistant_agent = AssistantAgent(webhook_url, agent_addresses)
    
    # Register the agent with Agentverse
    success = _assistant_agent.register_with_agentverse()
    if success:
        logger.info(f"Assistant agent registered with address: {_assistant_agent.address}")
    else:
        logger.error("Failed to register assistant agent with Agentverse")
        
    return _assistant_agent