from abc import ABC, abstractmethod
from typing import Dict, Any
from src.core.models import CostInfo

class BaseLLMEngine(ABC):
    """
    Base interface for LLM engines
    
    Defines the contract that all LLM engines must implement
    """
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate response from the LLM

        Args:
            prompt: Input prompt for the LLM
            **kwargs: Additional parameters for the LLM

        Returns:
            Dictionary containing:
                content (str): Generated content
                success (bool): Whether generation was successful
                cost_info (CostInfo): Cost information
                error (str): Error message if any
        """
        pass
    
    @abstractmethod
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost based on token usage

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Total cost in USD
        """
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for given text

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated number of tokens
        """
        pass
    
    def create_cost_info(self, input_tokens: int, output_tokens: int) -> CostInfo:
        """
        Create cost information object

        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated

        Returns:
            CostInfo object with cost details
        """
        total_tokens = input_tokens + output_tokens
        cost_usd = self.calculate_cost(input_tokens, output_tokens)
        
        return CostInfo(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            model_name=self.name
        )
