import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from kafka import KafkaProducer, KafkaConsumer
from src.core.config import Config

logger = logging.getLogger(__name__)

def json_serializer(obj):
    """
    Custom JSON serializer for handling datetime objects

    Args:
        obj: Object to serialize

    Returns:
        Serialized object

    Raises:
        TypeError: If object type is not JSON serializable
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

class KafkaClient:
    """
    Unified Kafka operations client
    
    Provides producer and consumer creation and management functionality
    """
    
    def __init__(self):
        self.config = Config()
        self.producer = None
        self.consumers: Dict[str, KafkaConsumer] = {}
        
    def create_producer(self) -> KafkaProducer:
        """
        Create Kafka producer

        Returns:
            KafkaProducer instance

        Raises:
            Exception: If producer creation fails
        """
        try:
            if not self.producer:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.config.KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v, default=json_serializer).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None
                )
                logger.info("Kafka producer created successfully")
            return self.producer
        except Exception as e:
            logger.error(f"Failed to create Kafka producer: {e}")
            raise
    
    def create_consumer(self, topics: List[str], group_id: str) -> KafkaConsumer:
        """
        Create Kafka consumer

        Args:
            topics: List of topics to subscribe to
            group_id: Consumer group identifier

        Returns:
            KafkaConsumer instance

        Raises:
            Exception: If consumer creation fails
        """
        try:
            # For CLI response consumer, use earliest to ensure all messages are read
            offset_reset = 'earliest' if 'cli_response' in group_id else 'latest'
            
            consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=self.config.KAFKA_BOOTSTRAP_SERVERS,
                group_id=group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset=offset_reset,
                enable_auto_commit=True
            )
            self.consumers[group_id] = consumer
            logger.info(f"Kafka consumer created for topics: {topics}, group: {group_id}")
            return consumer
        except Exception as e:
            logger.error(f"Failed to create Kafka consumer: {e}")
            raise
    
    def send_message(self, topic: str, message: Dict[str, Any], key: Optional[str] = None):
        """
        Send message to Kafka topic

        Args:
            topic: Target topic name
            message: Message content as dictionary
            key: Optional message key

        Raises:
            Exception: If message sending fails
        """
        try:
            producer = self.create_producer()
            future = producer.send(topic, value=message, key=key)
            producer.flush()  # Ensure message is sent
            logger.debug(f"Message sent to topic {topic}: {message}")
            return future
        except Exception as e:
            logger.error(f"Failed to send message to {topic}: {e}")
            raise
    
    def close_producer(self):
        """
        Close producer connection
        """
        if self.producer:
            self.producer.close()
            self.producer = None
            logger.info("Kafka producer closed")
    
    def close_consumer(self, group_id: str):
        """
        Close specified consumer

        Args:
            group_id: Consumer group identifier to close
        """
        if group_id in self.consumers:
            self.consumers[group_id].close()
            del self.consumers[group_id]
            logger.info(f"Kafka consumer {group_id} closed")
    
    def close_all(self):
        """
        Close all connections
        """
        self.close_producer()
        for group_id in list(self.consumers.keys()):
            self.close_consumer(group_id)
        logger.info("All Kafka connections closed")
    
    def health_check(self) -> bool:
        """
        Check Kafka connection status

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            producer = self.create_producer()
            # Try sending a test message to check connection
            future = producer.send('health_check', {'test': 'connection'})
            # Wait for completion (max 5 seconds)
            future.get(timeout=5)
            return True
        except Exception as e:
            logger.error(f"Kafka health check failed: {e}")
            return False
