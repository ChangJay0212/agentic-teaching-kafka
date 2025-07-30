from pydantic import BaseModel
from typing import List
from datetime import datetime
from enum import Enum

class LanguageType(str, Enum):
    """
    Supported language types for message routing
    """
    CHINESE = "chinese"
    ENGLISH = "english"
    AUTO = "auto"

class AgentType(str, Enum):
    """
    Available agent types in the system
    """
    CHINESE_TEACHER = "chinese_teacher"
    ENGLISH_TEACHER = "english_teacher"

class Message(BaseModel):
    """
    Message model for user questions

    Attributes:
        message_id: Unique identifier for the message
        user_id: User identifier
        content: Message content/question
        language: Detected or specified language
        timestamp: When the message was created
    """
    message_id: str
    user_id: str
    content: str
    language: LanguageType
    timestamp: datetime
    
    class Config:
        use_enum_values = True

class CostInfo(BaseModel):
    """
    Cost information for LLM API calls

    Attributes:
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens generated
        total_tokens: Total tokens (input + output)
        cost_usd: Total cost in USD
        model_name: Name of the model used
    """
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    model_name: str

class Response(BaseModel):
    """
    Response model for agent replies

    Attributes:
        message_id: ID of the original message
        success: Whether the response was successful
        content: Response content/answer
        agent_type: Type of agent that generated the response
        cost_info: Cost information for the response
        response_time: Time taken to generate response in seconds
        timestamp: When the response was created
    """
    message_id: str
    success: bool
    content: str
    agent_type: AgentType
    cost_info: CostInfo
    response_time: float
    timestamp: datetime
    
    class Config:
        use_enum_values = True

class SystemStatus(BaseModel):
    """
    System status information

    Attributes:
        kafka_connected: Whether Kafka is connected
        active_consumers: List of active consumer names
        total_messages_processed: Total number of messages processed
        total_cost: Total cost accumulated
        uptime_seconds: System uptime in seconds
    """
    kafka_connected: bool
    active_consumers: List[str]
    total_messages_processed: int
    total_cost: float
    uptime_seconds: float
