from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from agents.journal_agent import JournalAgent
from models.data_models import JournalEntry, AgentResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/journal", tags=["Journal"])

# Initialize agent with webhook URL (will be updated in main.py)
_journal_agent = None

class JournalRequest(BaseModel):
    user_id: str
    content: str

def get_journal_agent():
    if _journal_agent is None:
        raise HTTPException(status_code=500, detail="Journal agent not initialized")
    return _journal_agent

@router.post("/analyze", response_model=AgentResponse)
async def analyze_journal(request: JournalRequest, agent: JournalAgent = Depends(get_journal_agent)):
    """Analyze a journal entry and generate insights"""
    try:
        journal_analysis = agent.analyze_journal(request.content, request.user_id)
        
        return AgentResponse(
            success=True,
            data=journal_analysis.dict(),
            message="Journal analysis completed successfully"
        )
    except Exception as e:
        logger.error(f"Error analyzing journal: {e}")
        return AgentResponse(
            success=False,
            data={},
            message=f"Error analyzing journal: {str(e)}"
        )

@router.post("/webhook", response_model=Dict[str, Any])
async def journal_webhook(request: Request, agent: JournalAgent = Depends(get_journal_agent)):
    """Webhook endpoint for the Journal Analysis Agent"""
    try:
        data = await request.body()
        data_str = data.decode("utf-8")
        
        return agent.handle_webhook(data_str)
    except Exception as e:
        logger.error(f"Error processing journal webhook: {e}")
        return {"status": "error", "message": str(e)}

def init_agent(webhook_url: str):
    """Initialize the Journal Agent with the correct webhook URL"""
    global _journal_agent
    _journal_agent = JournalAgent(webhook_url)
    
    # Register the agent with Agentverse
    success = _journal_agent.register_with_agentverse()
    if success:
        logger.info(f"Journal agent registered with address: {_journal_agent.address}")
    else:
        logger.error("Failed to register journal agent with Agentverse")
        
    return _journal_agent