import logging
import requests
from typing import Dict, Any
from src.llm.base_engine import BaseLLMEngine
from src.core.config import Config

logger = logging.getLogger(__name__)

class OllamaEngine(BaseLLMEngine):
    """
    Ollama LLM engine implementation
    
    Provides text generation using local Ollama service
    """
    
    def __init__(self):
        super().__init__("ollama")
        self.config = Config()
        self.base_url = self.config.OLLAMA_BASE_URL
        self.model = self.config.OLLAMA_MODEL
        self.available = self._check_availability()
        
        if self.available:
            logger.info(f"Ollama engine initialized successfully - Model: {self.model}")
        else:
            logger.warning(f"Ollama not available at {self.base_url}")
    
    def _check_availability(self) -> bool:
        """
        Check if Ollama service is available

        Returns:
            True if Ollama service is reachable, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama availability check failed: {e}")
            return False
    
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate response using Ollama API

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
                "error": f"Ollama service not available at {self.base_url}"
            }
        
        try:
            # Estimate input tokens
            input_tokens = self.estimate_tokens(prompt)
            
            # Call Ollama API
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json()
            content = result.get("response", "")
            
            # Estimate output tokens
            output_tokens = self.estimate_tokens(content)
            
            # Create cost information (Ollama is usually free)
            cost_info = self.create_cost_info(input_tokens, output_tokens)
            
            logger.info(f"Ollama response generated - Input: {input_tokens}, Output: {output_tokens}, Cost: ${cost_info.cost_usd:.6f}")
            
            return {
                "content": content,
                "success": True,
                "cost_info": cost_info,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return {
                "content": "",
                "success": False,
                "cost_info": self.create_cost_info(0, 0),
                "error": str(e)
            }
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost (Ollama is usually free)

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Total cost in USD (usually 0 for Ollama)
        """
        input_cost = (input_tokens / 1000) * self.config.OLLAMA_INPUT_COST_PER_1K_TOKENS
        output_cost = (output_tokens / 1000) * self.config.OLLAMA_OUTPUT_COST_PER_1K_TOKENS
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
