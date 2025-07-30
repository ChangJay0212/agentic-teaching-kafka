import logging
import asyncio
import threading
from typing import Dict, List
from src.core.kafka_client import KafkaClient
from src.core.models import Message, Response
from src.agents.base_agent import BaseAgent
from src.core.config import Config

logger = logging.getLogger(__name__)

class AgentConsumer:
    """
    Agent Consumer - Manages message consumption for a single agent
    
    Handles message processing and response publishing for specific agent types
    """
    
    def __init__(self, agent: BaseAgent, topics: List[str]):
        self.agent = agent
        self.topics = topics
        self.kafka_client = KafkaClient()
        self.config = Config()
        self.running = False
        self.thread = None
        logger.info(f"Agent consumer created for {agent.agent_type} - Topics: {topics}")
    
    def start(self):
        """
        Start consumer

        Starts the consumer thread for processing messages
        """
        if self.running:
            logger.warning(f"Consumer for {self.agent.agent_type} already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._consume_loop, daemon=True)
        self.thread.start()
        logger.info(f"Consumer for {self.agent.agent_type} started")
    
    def stop(self):
        """
        Stop consumer

        Stops the consumer thread and closes connections
        """
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.kafka_client.close_all()
        logger.info(f"Consumer for {self.agent.agent_type} stopped")
    
    def _consume_loop(self):
        """
        Consumer loop

        Main loop for consuming and processing messages
        """
        try:
            # Create consumer
            consumer = self.kafka_client.create_consumer(
                topics=self.topics,
                group_id=f"{self.agent.agent_type}_group"
            )
            
            logger.info(f"Consumer loop started for {self.agent.agent_type}")
            
            while self.running:
                try:
                    # Poll for messages
                    message_pack = consumer.poll(timeout_ms=1000)
                    
                    if not message_pack:
                        continue
                    
                    # Process received messages
                    for topic_partition, messages in message_pack.items():
                        for kafka_message in messages:
                            # Run async function in current thread
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                loop.run_until_complete(self._process_message(kafka_message.value))
                            finally:
                                loop.close()
                            
                except Exception as e:
                    logger.error(f"Error in consume loop for {self.agent.agent_type}: {e}")
                    if self.running:
                        import time
                        time.sleep(1)  # Wait briefly before retry
                        
        except Exception as e:
            logger.error(f"Fatal error in consumer for {self.agent.agent_type}: {e}")
        finally:
            self.kafka_client.close_all()
    
    async def _process_message(self, message_data: Dict):
        """
        Process a single message.
        
        Args:
            message_data: Message data dictionary
        """
        try:
            # Parse message
            message = Message(**message_data)
            logger.debug(f"Processing message {message.message_id} with {self.agent.agent_type}")
            
            # Let Agent process message
            response = await self.agent.process_message(message)
            
            # Send response to responses topic
            await self._send_response(response)
            
            # Send cost information to cost_monitor topic
            await self._send_cost_info(response)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def _send_response(self, response: Response):
        """
        Send response to responses topic.
        
        Args:
            response: Response object to send
        """
        try:
            self.kafka_client.send_message(
                topic=self.config.TOPICS["responses"],
                message=response.dict(),
                key=response.message_id
            )
            logger.debug(f"Response sent for message {response.message_id}")
        except Exception as e:
            logger.error(f"Failed to send response: {e}")
    
    async def _send_cost_info(self, response: Response):
        """
        Send cost information to cost_monitor topic.
        
        Args:
            response: Response object containing cost information
        """
        try:
            cost_data = {
                "message_id": response.message_id,
                "agent_type": response.agent_type,
                "cost_info": response.cost_info.dict(),
                "timestamp": response.timestamp.isoformat()
            }
            
            self.kafka_client.send_message(
                topic=self.config.TOPICS["cost_monitor"],
                message=cost_data,
                key=response.message_id
            )
            logger.debug(f"Cost info sent for message {response.message_id}")
        except Exception as e:
            logger.error(f"Failed to send cost info: {e}")


class ConsumerManager:
    """
    Consumer Manager - Manages all Agent consumers.
    
    This class handles the lifecycle of multiple consumer instances,
    allowing centralized management of all agent message consumers.
    """
    
    def __init__(self):
        self.consumers: Dict[str, AgentConsumer] = {}
        logger.info("Consumer manager initialized")
    
    def add_agent_consumer(self, agent: BaseAgent, topics: List[str]):
        """
        Add Agent consumer.
        
        Args:
            agent: Agent instance to create consumer for
            topics: List of topics to subscribe to
        """
        agent_key = str(agent.agent_type)
        consumer = AgentConsumer(agent, topics)
        self.consumers[agent_key] = consumer
        logger.info(f"Added consumer for {agent.agent_type}")
    
    def start_all(self):
        """
        Start all consumers.
        
        Begins message consumption for all registered agent consumers.
        """
        for agent_key, consumer in self.consumers.items():
            consumer.start()
        logger.info(f"Started {len(self.consumers)} consumers")
    
    def stop_all(self):
        """
        Stop all consumers.
        
        Gracefully stops message consumption for all registered consumers.
        """
        for agent_key, consumer in self.consumers.items():
            consumer.stop()
        logger.info("All consumers stopped")
    
    def get_status(self) -> Dict[str, bool]:
        """
        Get status of all consumers.
        
        Returns:
            Dictionary mapping agent keys to their running status
        """
        return {
            agent_key: consumer.running 
            for agent_key, consumer in self.consumers.items()
        }
