import logging
import uuid
from datetime import datetime
from typing import Dict, Any
try:
    from langdetect import detect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
from src.core.kafka_client import KafkaClient
from src.core.models import Message, LanguageType
from src.core.config import Config

logger = logging.getLogger(__name__)

class MessageProducer:
    """
    Intelligent message producer for routing and sending messages
    
    Handles language detection and routes messages to appropriate topics
    """
    
    def __init__(self):
        self.kafka_client = KafkaClient()
        self.config = Config()
        logger.info("Message producer initialized")
    
    def detect_language(self, text: str) -> LanguageType:
        """
        Detect text language

        Args:
            text: Input text to analyze

        Returns:
            Detected language type (CHINESE or ENGLISH)
        """
        try:
            if LANGDETECT_AVAILABLE:
                # Use langdetect for language detection
                detected = detect(text)
                
                # Simple rule: if Chinese detected, use Chinese teacher
                if detected in ['zh-cn', 'zh-tw', 'zh']:
                    return LanguageType.CHINESE
            
            # Check if contains Chinese characters
            if self._contains_chinese(text):
                return LanguageType.CHINESE
            
            # Default to English teacher
            return LanguageType.ENGLISH
            
        except Exception:
            # If detection fails, use simple rules
            if self._contains_chinese(text):
                return LanguageType.CHINESE
            return LanguageType.ENGLISH
    
    def _contains_chinese(self, text: str) -> bool:
        """
        Check if text contains Chinese characters

        Args:
            text: Text to check

        Returns:
            True if contains Chinese characters, False otherwise
        """
        for char in text:
            if '\u4e00' <= char <= '\u9fff':  # Chinese character range
                return True
        return False
    
    def route_to_topic(self, language: LanguageType) -> str:
        """
        Route to appropriate topic based on language

        Args:
            language: Detected language type

        Returns:
            Target topic name
        """
        if language == LanguageType.CHINESE:
            return self.config.TOPICS["chinese_teacher"]
        else:
            return self.config.TOPICS["english_teacher"]
    
    async def send_message(self, content: str, user_id: str = "default_user") -> Dict[str, Any]:
        """
        Send message to appropriate topic

        Args:
            content: Message content
            user_id: User identifier

        Returns:
            Dictionary containing operation result
        """
        try:
            # Generate message ID
            message_id = str(uuid.uuid4())
            
            # Detect language
            language = self.detect_language(content)
            
            # Create message object
            message = Message(
                message_id=message_id,
                user_id=user_id,
                content=content,
                language=language,
                timestamp=datetime.now()
            )
            
            # Select target topic
            target_topic = self.route_to_topic(language)
            
            # Send to Kafka
            self.kafka_client.send_message(
                topic=target_topic,
                message=message.dict(),
                key=message_id
            )
            
            logger.info(f"Message {message_id} sent to {target_topic} (Language: {language})")
            
            return {
                "success": True,
                "message_id": message_id,
                "topic": target_topic,
                "language": language,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return {
                "success": False,
                "message_id": None,
                "topic": None,
                "language": None,
                "error": str(e)
            }
    
    def close(self):
        """
        Close producer
        """
        self.kafka_client.close_producer()
        logger.info("Message producer closed")
