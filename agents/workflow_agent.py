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
from models.data_models import WorkflowPlan, WorkflowRequirement, AgentComponent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize Gemini client
gemini_client = GeminiClient("WORKFLOW_AGENT_GEMINI_API_KEY")
firebase_client = FirebaseClient()

# Agent configuration
AGENT_TITLE = "AI Workflow Planning Agent"
AGENT_SEED_PHRASE = os.getenv("FETCH_AI_SEED_PHRASE")
AGENT_INDEX = 6  # Using index 6 for Workflow Agent
USE_SECONDARY_KEY = True  # Using secondary API key since this is beyond the first 4 agents

class WorkflowAgent:
    def __init__(self, webhook_url):
        """Initialize AI Workflow Planning Agent"""
        self.identity = create_agent_identity(AGENT_SEED_PHRASE, AGENT_INDEX)
        self.webhook_url = webhook_url
        self.address = self.identity.address
        
    def register_with_agentverse(self):
        """Register this agent with Agentverse"""
        readme = create_readme(
            domain="development",
            description="This agent helps developers design AI agent workflows by analyzing requirements and discovering relevant agents from Agentverse.",
            use_cases=[
                "Design personalized AI assistant workflows",
                "Discover and integrate agents from Agentverse",
                "Create architecture plans for multi-agent systems",
                "Generate integration steps for agent communication"
            ],
            payload_parameters=[
                {"parameter": "user_id", "description": "ID of the user creating the workflow"},
                {"parameter": "project_description", "description": "Description of the AI assistant project"},
                {"parameter": "requirements", "description": "List of workflow requirements and features"},
                {"parameter": "industry_domain", "description": "Target industry or domain for the AI assistant"}
            ]
        )
        
        return register_agent_with_agentverse(
            identity=self.identity,
            agent_title=AGENT_TITLE,
            webhook_url=self.webhook_url,
            readme=readme,
            use_secondary=USE_SECONDARY_KEY
        )
    
    def analyze_requirements(self, project_description, requirements_list, industry_domain):
        """Analyze requirements and categorize them"""
        try:
            prompt = f"""
            As an AI Workflow Planning specialist, analyze the following project requirements and categorize them 
            into functional categories. For each requirement, determine its priority (high, medium, low) based on 
            importance to the core functionality.
            
            Project Description: {project_description}
            Industry/Domain: {industry_domain}
            
            Requirements:
            {requirements_list}
            
            Format your response as a JSON array of objects with the following structure:
            [
                {{
                    "category": "category name",
                    "description": "detailed description of the requirement",
                    "priority": "priority level (high, medium, low)"
                }}
            ]
            """
            
            structure = [
                {
                    "category": "Category name",
                    "description": "Requirement description",
                    "priority": "priority"
                }
            ]
            
            response = gemini_client.generate_structured_response(
                prompt, 
                structure,
                temperature=0.2
            )
            
            # Convert the response to WorkflowRequirement objects
            workflow_requirements = []
            if isinstance(response, list):
                for req in response:
                    workflow_requirements.append(WorkflowRequirement(
                        category=req.get("category", "General"),
                        description=req.get("description", ""),
                        priority=req.get("priority", "medium")
                    ))
            
            return workflow_requirements
            
        except Exception as e:
            logger.error(f"Error analyzing requirements: {e}")
            # Return a default requirement if analysis fails
            return [WorkflowRequirement(
                category="General",
                description="AI assistant functionality",
                priority="high"
            )]
    
    def search_agentverse(self, project_description, requirements, industry_domain):
        """
        Search for relevant agents on Agentverse that could fulfill the requirements.
        
        In a real implementation, this would use the Search and Discover feature
        of Agentverse. For now, we'll simulate this with a structured response.
        """
        try:
            # This would be an actual API call to Agentverse in a real implementation
            logger.info(f"Searching Agentverse for agents relevant to: {project_description}")
            
            requirements_text = "\n".join([f"- {req.category}: {req.description} (Priority: {req.priority})" 
                                        for req in requirements])
            
            prompt = f"""
            As an AI agent specializing in agent discovery, find the most relevant agents that would 
            fulfill the following project requirements. For each agent, provide a relevance score 
            between 0.0 and 1.0 based on how well it matches the requirements.
            
            Project Description: {project_description}
            Industry/Domain: {industry_domain}
            
            Requirements:
            {requirements_text}
            
            Format your response as a JSON array of objects with the following structure:
            [
                {{
                    "name": "agent name",
                    "description": "what the agent does",
                    "capabilities": ["capability 1", "capability 2", ...],
                    "relevance_score": 0.95
                }}
            ]
            
            Return the top 5 most relevant agents.
            """
            
            structure = [
                {
                    "name": "Agent name",
                    "description": "Agent description",
                    "capabilities": ["Capability 1", "Capability 2"],
                    "relevance_score": 0.9
                }
            ]
            
            response = gemini_client.generate_structured_response(
                prompt, 
                structure,
                temperature=0.3
            )
            
            # Convert to AgentComponent objects
            agent_components = []
            if isinstance(response, list):
                for agent in response:
                    agent_components.append(AgentComponent(
                        name=agent.get("name", ""),
                        description=agent.get("description", ""),
                        capabilities=agent.get("capabilities", []),
                        relevance_score=agent.get("relevance_score", 0.0)
                    ))
            
            # Sort by relevance score
            agent_components.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return agent_components
            
        except Exception as e:
            logger.error(f"Error searching Agentverse: {e}")
            return []
    
    def generate_integration_steps(self, project_description, requirements, recommended_agents):
        """Generate step-by-step integration instructions for the recommended agents"""
        try:
            requirements_text = "\n".join([f"- {req.category}: {req.description} (Priority: {req.priority})" 
                                        for req in requirements])
            
            agents_text = "\n".join([f"- {agent.name}: {agent.description}" 
                                    for agent in recommended_agents])
            
            prompt = f"""
            As an expert in AI agent integration, create a detailed step-by-step plan for integrating the 
            following agents into a cohesive AI assistant workflow. Focus on how these agents will communicate
            with each other and how they should be orchestrated to work together seamlessly.
            
            Project Description: {project_description}
            
            Requirements:
            {requirements_text}
            
            Recommended Agents:
            {agents_text}
            
            Format your response as a JSON array of strings, where each string represents a step in the 
            integration process. Be specific and detailed, including code concepts where appropriate.
            
            Example:
            [
                "Step 1: Set up a central orchestrator agent that will coordinate communication between specialized agents",
                "Step 2: Implement webhook endpoints for each agent to receive messages from the orchestrator",
                ...
            ]
            """
            
            structure = ["Step 1: Do something", "Step 2: Do something else"]
            
            response = gemini_client.generate_structured_response(
                prompt, 
                structure,
                temperature=0.3
            )
            
            if isinstance(response, list):
                return response
            return []
            
        except Exception as e:
            logger.error(f"Error generating integration steps: {e}")
            return ["Set up communication between agents", "Implement error handling"]
    
    def generate_architecture_diagram(self, project_description, requirements, recommended_agents):
        """Generate a text-based architecture diagram"""
        try:
            requirements_text = "\n".join([f"- {req.category}: {req.description}" 
                                        for req in requirements])
            
            agents_text = "\n".join([f"- {agent.name}" 
                                    for agent in recommended_agents])
            
            prompt = f"""
            Create a text-based architecture diagram showing how the agents will work together.
            Use ASCII art to create boxes, arrows, and connections between the agents.
            
            Project: {project_description}
            
            Requirements:
            {requirements_text}
            
            Agents:
            {agents_text}
            
            The diagram should show:
            1. The user entry point
            2. The central orchestrator/coordinator
            3. Each specialized agent and its responsibility
            4. Data flows between agents
            
            Keep the diagram compact but clear.
            """
            
            diagram = gemini_client.generate_text(
                prompt,
                temperature=0.1
            )
            
            return diagram
            
        except Exception as e:
            logger.error(f"Error generating architecture diagram: {e}")
            return "Architecture diagram generation failed"
    
    def create_workflow_plan(self, user_id, project_description, requirements_list, industry_domain):
        """Create a comprehensive workflow plan for an AI agent system"""
        try:
            # Step 1: Analyze and categorize requirements
            workflow_requirements = self.analyze_requirements(
                project_description, requirements_list, industry_domain
            )
            
            # Step 2: Search Agentverse for relevant agents
            recommended_agents = self.search_agentverse(
                project_description, workflow_requirements, industry_domain
            )
            
            # Step 3: Generate integration steps
            integration_steps = self.generate_integration_steps(
                project_description, workflow_requirements, recommended_agents
            )
            
            # Step 4: Generate architecture diagram
            architecture_diagram = self.generate_architecture_diagram(
                project_description, workflow_requirements, recommended_agents
            )
            
            # Create the complete workflow plan
            workflow_plan = WorkflowPlan(
                title=f"AI Assistant Workflow for {industry_domain}",
                description=project_description,
                requirements=workflow_requirements,
                recommended_agents=recommended_agents,
                integration_steps=integration_steps,
                architecture_diagram=architecture_diagram,
                user_id=user_id
            )
            
            # Save to Firebase
            document_id = firebase_client.save_workflow_plan(workflow_plan.dict())
            
            if document_id:
                logger.info(f"Workflow plan saved with ID: {document_id}")
            
            return workflow_plan
            
        except Exception as e:
            logger.error(f"Error creating workflow plan: {e}")
            raise
    
    def handle_webhook(self, data):
        """Handle incoming webhook from Agentverse"""
        try:
            message = parse_message_from_agent(data)
            payload = message.payload
            
            logger.info(f"Received message from {message.sender} with payload: {payload}")
            
            if all(key in payload for key in ["user_id", "project_description", "requirements", "industry_domain"]):
                user_id = payload["user_id"]
                project_description = payload["project_description"]
                requirements_list = payload["requirements"]
                industry_domain = payload["industry_domain"]
                
                workflow_plan = self.create_workflow_plan(
                    user_id, project_description, requirements_list, industry_domain
                )
                
                # Send response back to the requesting agent
                response_payload = {
                    "success": True,
                    "workflow_title": workflow_plan.title,
                    "recommended_agents": [agent.dict() for agent in workflow_plan.recommended_agents],
                    "integration_steps": workflow_plan.integration_steps,
                    "architecture_diagram": workflow_plan.architecture_diagram
                }
                
                send_message_to_agent(self.identity, message.sender, response_payload)
                return {"status": "success"}
            else:
                logger.error("Missing required fields in payload")
                return {"status": "error", "message": "Missing required fields"}
                
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return {"status": "error", "message": str(e)}