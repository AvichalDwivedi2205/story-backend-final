from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

from agents.workflow_agent import WorkflowAgent
from models.data_models import AgentResponse, WorkflowPlan

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflow", tags=["Workflow"])

_workflow_agent = None

class WorkflowRequest(BaseModel):
    user_id: str
    project_description: str
    requirements: List[str]
    industry_domain: str

def get_workflow_agent():
    if _workflow_agent is None:
        raise HTTPException(status_code=500, detail="Workflow agent not initialized")
    return _workflow_agent

@router.post("/generate", response_model=AgentResponse)
async def generate_workflow(request: WorkflowRequest, agent: WorkflowAgent = Depends(get_workflow_agent)):
    """Generate an AI agent workflow plan based on requirements"""
    try:
        workflow_plan = agent.create_workflow_plan(
            request.user_id, 
            request.project_description, 
            request.requirements, 
            request.industry_domain
        )
        
        return AgentResponse(
            success=True,
            data=workflow_plan.dict(),
            message="Workflow plan generated successfully"
        )
    except Exception as e:
        logger.error(f"Error generating workflow plan: {e}")
        return AgentResponse(
            success=False,
            data={},
            message=f"Error generating workflow plan: {str(e)}"
        )

@router.post("/webhook", response_model=Dict[str, Any])
async def workflow_webhook(request: Request, agent: WorkflowAgent = Depends(get_workflow_agent)):
    """Webhook endpoint for the Workflow Agent"""
    try:
        data = await request.body()
        data_str = data.decode("utf-8")
        
        return agent.handle_webhook(data_str)
    except Exception as e:
        logger.error(f"Error processing workflow webhook: {e}")
        return {"status": "error", "message": str(e)}

def init_agent(webhook_url: str):
    """Initialize the Workflow Agent with the correct webhook URL"""
    global _workflow_agent
    _workflow_agent = WorkflowAgent(webhook_url)
    
    success = _workflow_agent.register_with_agentverse()
    if success:
        logger.info(f"Workflow agent registered with address: {_workflow_agent.address}")
    else:
        logger.error("Failed to register workflow agent with Agentverse")
        
    return _workflow_agent