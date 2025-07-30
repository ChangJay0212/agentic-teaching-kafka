import logging
from abc import ABC, abstractmethod
from datetime import datetime
from src.core.models import Message, Response, AgentType
from src.llm.base_engine import BaseLLMEngine

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Base agent class for all teaching agents
    
    Provides common functionality for processing messages and generating responses
    """
    
    def __init__(self, agent_type: AgentType, llm_engine: BaseLLMEngine):
        self.agent_type = agent_type
        self.llm_engine = llm_engine
        self.tools = []  # Reserved for future tool system
        logger.info(f"Agent {agent_type} initialized with {llm_engine.name}")
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get system prompt for the agent

        Returns:
            System prompt string for this agent type
        """
        pass
    
    async def process_message(self, message: Message) -> Response:
        """
        Process message and generate response

        Args:
            message: Input message to process

        Returns:
            Response object with generated content and metadata
        """
        start_time = datetime.now()
        
        try:
            # Build complete prompt
            system_prompt = self.get_system_prompt()
            full_prompt = f"{system_prompt}\n\nUser Question: {message.content}"
            
            # Call LLM to generate response
            llm_response = await self.llm_engine.generate_response(full_prompt)
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Create response object
            response = Response(
                message_id=message.message_id,
                success=llm_response["success"],
                content=llm_response["content"] if llm_response["success"] else f"Processing failed: {llm_response.get('error', 'Unknown error')}",
                agent_type=self.agent_type,
                cost_info=llm_response["cost_info"],
                response_time=response_time,
                timestamp=datetime.now()
            )
            
            logger.info(f"Message processed by {self.agent_type} - Success: {response.success}, Time: {response_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message in {self.agent_type}: {e}")
            
            # Create error response
            response_time = (datetime.now() - start_time).total_seconds()
            return Response(
                message_id=message.message_id,
                success=False,
                content=f"System error: {str(e)}",
                agent_type=self.agent_type,
                cost_info=self.llm_engine.create_cost_info(0, 0),
                response_time=response_time,
                timestamp=datetime.now()
            )
    
    def analyze_tools_needed(self, prompt: str):
        """
        Analyze tools needed for the prompt (reserved for future implementation)

        Args:
            prompt: Input prompt to analyze

        Note:
            This method is reserved for future tool system implementation
        """
        # Future implementation for tool needs analysis
        pass
