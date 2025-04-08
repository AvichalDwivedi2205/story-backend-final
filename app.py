import os
import logging
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

# Import routers
from routers import (
    journal_routes,
    exercise_routes,
    gratitude_routes,
    therapy_routes,
    guide_routes,
    assistant_routes
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Story.AI Backend",
    description="API for Story.AI mental well-being agents"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(journal_routes.router)
app.include_router(exercise_routes.router)
app.include_router(gratitude_routes.router)
app.include_router(therapy_routes.router)
app.include_router(guide_routes.router)
app.include_router(assistant_routes.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Story.AI API", "status": "online"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

def init_agents(host: str, port: int):
    """Initialize all agents with the appropriate webhook URLs"""
    base_url = f"http://{host}:{port}"
    agent_addresses = {}
    
    # Initialize Journal Agent
    journal_webhook_url = f"{base_url}/api/journal/webhook"
    journal_agent = journal_routes.init_agent(journal_webhook_url)
    agent_addresses["journal"] = journal_agent.address
    logger.info(f"Initialized Journal Agent with address: {journal_agent.address}")
    
    # Initialize Exercise Agent
    exercise_webhook_url = f"{base_url}/api/exercise/webhook"
    exercise_agent = exercise_routes.init_agent(exercise_webhook_url)
    agent_addresses["exercise"] = exercise_agent.address
    logger.info(f"Initialized Exercise Agent with address: {exercise_agent.address}")
    
    # Initialize Gratitude Agent
    gratitude_webhook_url = f"{base_url}/api/gratitude/webhook"
    gratitude_agent = gratitude_routes.init_agent(gratitude_webhook_url)
    agent_addresses["gratitude"] = gratitude_agent.address
    logger.info(f"Initialized Gratitude Agent with address: {gratitude_agent.address}")
    
    # Initialize Therapy Agent
    therapy_webhook_url = f"{base_url}/api/therapy/webhook"
    therapy_agent = therapy_routes.init_agent(therapy_webhook_url)
    agent_addresses["therapy"] = therapy_agent.address
    logger.info(f"Initialized Therapy Agent with address: {therapy_agent.address}")
    
    # Initialize Guide Agent
    guide_webhook_url = f"{base_url}/api/guide/webhook"
    guide_agent = guide_routes.init_agent(guide_webhook_url)
    agent_addresses["guide"] = guide_agent.address
    logger.info(f"Initialized Guide Agent with address: {guide_agent.address}")
    
    # Initialize Assistant Agent (with addresses of all other agents)
    assistant_webhook_url = f"{base_url}/api/assistant/webhook"
    assistant_agent = assistant_routes.init_agent(assistant_webhook_url, agent_addresses)
    logger.info(f"Initialized Assistant Agent with address: {assistant_agent.address}")
    
    logger.info("All agents initialized successfully")
    return agent_addresses

if __name__ == "__main__":
    # Define host and port
    host = "0.0.0.0"
    port = 8000
    
    # Initialize all agents
    agent_addresses = init_agents(host, port)
    
    # Start the FastAPI server
    logger.info(f"Starting FastAPI server on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)