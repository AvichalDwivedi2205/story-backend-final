import os
import logging
from dotenv import load_dotenv
from uagents_core.identity import Identity
from fetchai.registration import register_with_agentverse
import random
import string
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch
from typing import Dict, List, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize models at module level
logger.info("Loading sentiment analysis model...")
SENTIMENT_TOKENIZER = AutoTokenizer.from_pretrained("cardiffnlp/twitter-roberta-base-sentiment")
SENTIMENT_MODEL = AutoModelForSequenceClassification.from_pretrained("cardiffnlp/twitter-roberta-base-sentiment")

logger.info("Loading emotion analysis model...")
EMOTION_TOKENIZER = AutoTokenizer.from_pretrained("j-hartmann/emotion-english-distilroberta-base")
EMOTION_MODEL = AutoModelForSequenceClassification.from_pretrained("j-hartmann/emotion-english-distilroberta-base")

logger.info("AI models loaded successfully")

def get_agentverse_key(secondary=False):
    """Get the appropriate Agentverse API key"""
    if secondary:
        return os.getenv("AGENTVERSE_API_KEY_SECONDARY")
    return os.getenv("AGENTVERSE_API_KEY")

def create_agent_identity(seed_phrase, index):
    """Generate a deterministic agent identity from the seed phrase and index"""
    try:
        identity = Identity.from_seed(seed_phrase, index)
        logger.info(f"Created agent identity with address: {identity.address}")
        return identity
    except Exception as e:
        logger.error(f"Error creating agent identity: {e}")
        raise

def register_agent_with_agentverse(identity, agent_title, webhook_url, readme, use_secondary=False):
    """Register an agent with Agentverse"""
    try:
        agentverse_key = get_agentverse_key(secondary=use_secondary)
        
        if not agentverse_key:
            raise ValueError("Missing Agentverse API key")
            
        register_with_agentverse(
            identity=identity,
            url=webhook_url,
            agentverse_token=agentverse_key,
            agent_title=agent_title,
            readme=readme
        )
        logger.info(f"Successfully registered {agent_title} with Agentverse")
        return True
    except Exception as e:
        logger.error(f"Failed to register agent with Agentverse: {e}")
        return False

def generate_random_id(length=10):
    """Generate a random ID string"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def analyze_sentiment(text: str) -> Dict:
    """
    Analyze sentiment of text using pre-trained model
    
    Returns a dict with score and label (e.g., positive, negative, neutral)
    """
    try:
        # Use the pre-loaded model and tokenizer
        inputs = SENTIMENT_TOKENIZER(text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = SENTIMENT_MODEL(**inputs)
        
        scores = torch.nn.functional.softmax(outputs.logits, dim=1).tolist()[0]
        labels = ["negative", "neutral", "positive"]
        
        # Find the dominant sentiment
        dominant_idx = scores.index(max(scores))
        sentiment = {
            "score": scores[dominant_idx],
            "label": labels[dominant_idx]
        }
        
        return sentiment
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        return {"score": 0.5, "label": "neutral"}

def analyze_emotions(text: str) -> Dict:
    """
    Analyze emotions in text using emotion model
    
    Returns a dict with emotion probabilities and dominant emotion
    """
    try:
        # Use the pre-loaded model and tokenizer
        inputs = EMOTION_TOKENIZER(text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = EMOTION_MODEL(**inputs)
        
        scores = torch.nn.functional.softmax(outputs.logits, dim=1).tolist()[0]
        labels = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]
        
        emotions = {label: score for label, score in zip(labels, scores)}
        dominant_emotion = max(emotions, key=emotions.get)
        
        return {
            "emotions": emotions,
            "dominant_emotion": dominant_emotion
        }
    except Exception as e:
        logger.error(f"Error in emotion analysis: {e}")
        return {
            "emotions": {"neutral": 1.0},
            "dominant_emotion": "neutral"
        }

def create_readme(domain: str, description: str, use_cases: List[str], 
                  payload_parameters: List[Dict[str, str]]) -> str:
    """
    Create a standardized README for Agentverse registration
    
    Args:
        domain: The domain badge to show (e.g., "mental-health")
        description: A description of what the agent does
        use_cases: List of use case descriptions
        payload_parameters: List of dicts with 'parameter' and 'description' keys
        
    Returns:
        Formatted README string
    """
    use_cases_str = "\n".join([f"<use_case>{case}</use_case>" for case in use_cases])
    
    payload_req_str = "\n".join([
        f"<requirement>\n    <parameter>{param['parameter']}</parameter>\n    " + 
        f"<description>{param['description']}</description>\n</requirement>"
        for param in payload_parameters
    ])
    
    readme = f"""
        ![domain:{domain}](https://img.shields.io/badge/{domain}-3D8BD3)
        
        <description>{description}</description>
        <use_cases>
            {use_cases_str}
        </use_cases>
        <payload_requirements>
        <description>Payload format requirements for this agent:</description>
        <payload>
            {payload_req_str}
        </payload>
        </payload_requirements>
    """
    
    return readme