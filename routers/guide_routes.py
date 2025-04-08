from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

from agents.guide_agent import GuideAgent
from models.data_models import AgentResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/guide", tags=["Guide"])

# Initialize agent with webhook URL (will be updated in main.py)
_guide_agent = None

class GuideRequest(BaseModel):
    user_id: str
    query: str
    user_history: Optional[str] = None

def get_guide_agent():
    if _guide_agent is None:
        raise HTTPException(status_code=500, detail="Guide agent not initialized")
    return _guide_agent

@router.post("/recommend", response_model=AgentResponse)
async def get_recommendations(request: GuideRequest, agent: GuideAgent = Depends(get_guide_agent)):
    """Get recommendations for features based on user query"""
    try:
        response = agent.generate_comprehensive_response(
            request.user_id, 
            request.query, 
            request.user_history
        )
        
        return AgentResponse(
            success=True,
            data=response,
            message="Recommendations generated successfully"
        )
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return AgentResponse(
            success=False,
            data={},
            message=f"Error generating recommendations: {str(e)}"
        )

@router.post("/webhook", response_model=Dict[str, Any])
async def guide_webhook(request: Request, agent: GuideAgent = Depends(get_guide_agent)):
    """Webhook endpoint for the Guide Agent"""
    try:
        data = await request.body()
        data_str = data.decode("utf-8")
        
        return agent.handle_webhook(data_str)
    except Exception as e:
        logger.error(f"Error processing guide webhook: {e}")
        return {"status": "error", "message": str(e)}

def init_agent(webhook_url: str):
    """Initialize the Guide Agent with the correct webhook URL"""
    global _guide_agent
    _guide_agent = GuideAgent(webhook_url)
    
    # Register the agent with Agentverse
    success = _guide_agent.register_with_agentverse()
    if success:
        logger.info(f"Guide agent registered with address: {_guide_agent.address}")
    else:
        logger.error("Failed to register guide agent with Agentverse")
        
    return _guide_agent