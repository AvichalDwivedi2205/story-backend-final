import os
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class GeminiClient:
    def __init__(self, api_key_env: str):
        """
        Initialize the Gemini client with the specified API key environment variable.
        
        Args:
            api_key_env: Environment variable name containing the Gemini API key
        """
        try:
            api_key = os.getenv(api_key_env)
            if not api_key:
                raise ValueError(f"API key not found for {api_key_env}")
                
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
            logger.info(f"Gemini client initialized for {api_key_env}")
            
        except Exception as e:
            logger.error(f"Error initializing Gemini client: {e}")
            raise

    def generate_text(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Generate text using the Gemini API.
        
        Args:
            prompt: The prompt to send to the model
            temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
            
        Returns:
            Generated text response
        """
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={"temperature": temperature}
            )
            return response.text
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return f"Error generating text: {str(e)}"

    def generate_structured_response(self, 
                                    prompt: str, 
                                    structure: Dict[str, Any], 
                                    temperature: float = 0.3) -> Dict[str, Any]:
        """
        Generate structured response based on given schema.
        
        Args:
            prompt: The prompt to send to the model
            structure: Dictionary defining the expected structure
            temperature: Controls randomness
            
        Returns:
            Structured response matching the provided schema
        """
        try:
            # Enhance prompt to guide model to output in the desired structure
            enhanced_prompt = f"""{prompt}
            
            Please provide response in the following JSON structure:
            {structure}
            
            Important: Return a valid JSON object that strictly follows this structure.
            """
            
            response = self.model.generate_content(
                enhanced_prompt,
                generation_config={"temperature": temperature}
            )
            
            # Try to parse JSON response
            response_text = response.text
            
            # Clean up the response text to extract proper JSON
            # Remove any markdown code block syntax
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
                
            import json
            try:
                parsed_response = json.loads(response_text)
                return parsed_response
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response: {response_text}")
                # Fall back to returning the raw text
                return {"raw_response": response_text}
            
        except Exception as e:
            logger.error(f"Error generating structured response: {e}")
            return {"error": str(e)}