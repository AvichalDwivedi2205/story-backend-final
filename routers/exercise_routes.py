from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

from agents.exercise_agent import ExerciseAgent
from models.data_models import AgentResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/exercise", tags=["Exercise"])

# Initialize agent with webhook URL (will be updated in main.py)
_exercise_agent = None

class ExerciseRequest(BaseModel):
    user_id: str
    key_themes: Optional[List[str]] = None
    cognitive_distortions: Optional[List[str]] = None
    dominant_emotion: Optional[str] = "neutral"

def get_exercise_agent():
    if _exercise_agent is None:
        raise HTTPException(status_code=500, detail="Exercise agent not initialized")
    return _exercise_agent

@router.post("/generate", response_model=AgentResponse)
async def generate_exercises(request: ExerciseRequest, agent: ExerciseAgent = Depends(get_exercise_agent)):
    """Generate personalized exercises based on provided insights"""
    try:
        exercises = agent.generate_exercises(
            request.user_id, 
            request.key_themes, 
            request.cognitive_distortions, 
            request.dominant_emotion
        )
        
        return AgentResponse(
            success=True,
            data=exercises.dict(),
            message="Gratitude generated successfully"
        )
    except Exception as e:
        logger.error(f"Error generating exercises: {e}")
        return AgentResponse(
            success=False,
            data={},
            message=f"Error generating exercises: {str(e)}"
        )

@router.post("/webhook", response_model=Dict[str, Any])
async def exercise_webhook(request: Request, agent: ExerciseAgent = Depends(get_exercise_agent)):
    """Webhook endpoint for the Exercise Generator Agent"""
    try:
        data = await request.body()
        data_str = data.decode("utf-8")
        
        return agent.handle_webhook(data_str)
    except Exception as e:
        logger.error(f"Error processing exercise webhook: {e}")
        return {"status": "error", "message": str(e)}

def init_agent(webhook_url: str):
    """Initialize the Exercise Agent with the correct webhook URL"""
    global _exercise_agent
    _exercise_agent = ExerciseAgent(webhook_url)
    
    # Register the agent with Agentverse
    success = _exercise_agent.register_with_agentverse()
    if success:
        logger.info(f"Exercise agent registered with address: {_exercise_agent.address}")
    else:
        logger.error("Failed to register exercise agent with Agentverse")
        
    return _exercise_agent