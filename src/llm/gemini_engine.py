import logging
from typing import Dict, Any
import google.generativeai as genai
from src.llm.base_engine import BaseLLMEngine
from src.core.config import Config

logger = logging.getLogger(__name__)

class GeminiEngine(BaseLLMEngine):
    """
    Gemini LLM engine implementation
    
    Provides text generation using Google's Gemini API
    """
    
    def __init__(self):
        super().__init__(Config.GEMINI_MODEL)
        self.config = Config()
        
        # Configure API key
        if self.config.GEMINI_API_KEY:
            genai.configure(api_key=self.config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(self.config.GEMINI_MODEL)
            self.available = True
            logger.info("Gemini engine initialized successfully")
        else:
            self.available = False
            logger.warning("Gemini API key not found - engine disabled")
    
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate response using Gemini API

        Args:
            prompt: Input prompt for generation
            **kwargs: Additional parameters

        Returns:
            Dictionary containing generated content and metadata
        """
        if not self.available:
            return {
                "content": "",
                "success": False,
                "cost_info": self.create_cost_info(0, 0),
                "error": "Gemini API key not configured"
            }
        
        try:
            # Estimate input tokens
            input_tokens = self.estimate_tokens(prompt)
            
            # Call Gemini API
            response = self.model.generate_content(prompt)
            
            # Estimate output tokens
            output_tokens = self.estimate_tokens(response.text)
            
            # Create cost information
            cost_info = self.create_cost_info(input_tokens, output_tokens)
            
            logger.info(f"Gemini response generated - Input: {input_tokens}, Output: {output_tokens}, Cost: ${cost_info.cost_usd:.6f}")
            
            return {
                "content": response.text,
                "success": True,
                "cost_info": cost_info,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return {
                "content": "",
                "success": False,
                "cost_info": self.create_cost_info(0, 0),
                "error": str(e)
            }
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost in USD

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Total cost in USD
        """
        input_cost = (input_tokens / 1000) * self.config.GEMINI_INPUT_COST_PER_1K_TOKENS
        output_cost = (output_tokens / 1000) * self.config.GEMINI_OUTPUT_COST_PER_1K_TOKENS
        return input_cost + output_cost
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (simple approximation)

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated number of tokens
        """
        # Simple estimation: 1 token ≈ 4 characters
        return len(text) // 4 + 1
