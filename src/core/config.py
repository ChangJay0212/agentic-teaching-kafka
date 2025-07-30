import os
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

class Config:
    """
    Configuration management for the Teaching System
    
    Loads configuration from environment variables with sensible defaults
    """
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    
    # Kafka Topics
    TOPICS = {
        "chinese_teacher": "chinese_teacher",
        "english_teacher": "english_teacher", 
        "cost_monitor": "cost_monitor",
        "responses": "responses"
    }
    
    # Gemini Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    GEMINI_INPUT_COST_PER_1K_TOKENS = float(os.getenv("GEMINI_INPUT_COST_PER_1K_TOKENS", "0.000125"))
    GEMINI_OUTPUT_COST_PER_1K_TOKENS = float(os.getenv("GEMINI_OUTPUT_COST_PER_1K_TOKENS", "0.000375"))
    
    # Ollama Configuration
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    OLLAMA_INPUT_COST_PER_1K_TOKENS = float(os.getenv("OLLAMA_INPUT_COST_PER_1K_TOKENS", "0.0"))
    OLLAMA_OUTPUT_COST_PER_1K_TOKENS = float(os.getenv("OLLAMA_OUTPUT_COST_PER_1K_TOKENS", "0.0"))
    
    # System Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """
        Validate configuration completeness

        Returns:
            Dictionary containing validation results with errors and warnings
        """
        errors = []
        warnings = []
        
        # Check required configuration
        if not cls.GEMINI_API_KEY:
            warnings.append("GEMINI_API_KEY not set - Gemini engine will not work")
            
        # Check Kafka configuration
        if not cls.KAFKA_BOOTSTRAP_SERVERS:
            errors.append("KAFKA_BOOTSTRAP_SERVERS not set")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
