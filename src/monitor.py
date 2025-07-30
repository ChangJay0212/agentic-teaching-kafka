import logging
import threading
from typing import Dict
from datetime import datetime
from src.core.kafka_client import KafkaClient
from src.core.config import Config

logger = logging.getLogger(__name__)

class CostMonitor:
    """
    Cost Monitor - Collects and aggregates cost information.
    
    This class monitors cost information from various agents and provides
    statistical summaries for budget tracking and analysis.
    """
    
    def __init__(self):
        self.kafka_client = KafkaClient()
        self.config = Config()
        self.running = False
        self.thread = None
        
        # Cost statistics
        self.total_cost = 0.0
        self.cost_by_agent: Dict[str, float] = {}
        self.cost_by_model: Dict[str, float] = {}
        self.message_count = 0
        
        logger.info("Cost monitor initialized")
    
    def start(self):
        """
        Start cost monitoring.
        
        Initiates the monitoring thread to collect cost information.
        """
        if self.running:
            logger.warning("Cost monitor already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("Cost monitor started")
    
    def stop(self):
        """
        Stop cost monitoring.
        
        Gracefully stops the monitoring thread and closes connections.
        """
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.kafka_client.close_all()
        logger.info("Cost monitor stopped")
    
    def _monitor_loop(self):
        """
        Monitoring loop.
        
        Main loop that consumes cost information messages from Kafka.
        """
        try:
            # Create consumer
            consumer = self.kafka_client.create_consumer(
                topics=[self.config.TOPICS["cost_monitor"]],
                group_id="cost_monitor_group"
            )
            
            logger.info("Cost monitor loop started")
            
            while self.running:
                try:
                    # Poll for messages
                    message_pack = consumer.poll(timeout_ms=1000)
                    
                    if not message_pack:
                        continue
                    
                    # Process received cost information
                    for topic_partition, messages in message_pack.items():
                        for kafka_message in messages:
                            self._process_cost_info(kafka_message.value)
                            
                except Exception as e:
                    logger.error(f"Error in cost monitor loop: {e}")
                    if self.running:
                        import time
                        time.sleep(1)  # Wait briefly before retry
                        
        except Exception as e:
            logger.error(f"Fatal error in cost monitor: {e}")
        finally:
            self.kafka_client.close_all()
    
    def _process_cost_info(self, cost_data: Dict):
        """
        Process cost information.
        
        Args:
            cost_data: Dictionary containing cost information from agents
        """
        try:
            agent_type = cost_data.get("agent_type", "unknown")
            cost_info = cost_data.get("cost_info", {})
            
            cost_usd = cost_info.get("cost_usd", 0.0)
            model_name = cost_info.get("model_name", "unknown")
            
            # Update total cost
            self.total_cost += cost_usd
            
            # Update cost by Agent type
            if agent_type not in self.cost_by_agent:
                self.cost_by_agent[agent_type] = 0.0
            self.cost_by_agent[agent_type] += cost_usd
            
            # Update cost by model type
            if model_name not in self.cost_by_model:
                self.cost_by_model[model_name] = 0.0
            self.cost_by_model[model_name] += cost_usd
            
            # Update message count
            self.message_count += 1
            
            logger.debug(f"Cost updated - Agent: {agent_type}, Model: {model_name}, Cost: ${cost_usd:.6f}")
            
        except Exception as e:
            logger.error(f"Error processing cost info: {e}")
    
    def get_statistics(self) -> Dict:
        """
        Get cost statistics information.
        
        Returns:
            Dictionary containing comprehensive cost statistics
        """
        return {
            "total_cost": self.total_cost,
            "total_messages": self.message_count,
            "average_cost_per_message": self.total_cost / max(self.message_count, 1),
            "cost_by_agent": dict(self.cost_by_agent),
            "cost_by_model": dict(self.cost_by_model),
            "timestamp": datetime.now().isoformat()
        }
    
    def reset_statistics(self):
        """
        Reset statistics information.
        
        Clears all accumulated cost data and message counts.
        """
        self.total_cost = 0.0
        self.cost_by_agent.clear()
        self.cost_by_model.clear()
        self.message_count = 0
        logger.info("Cost statistics reset")
    
    def print_summary(self):
        """
        Print cost summary.
        
        Displays a formatted summary of all cost statistics.
        """
        stats = self.get_statistics()
        
        print("\n" + "="*50)
        print("💰 Cost Statistics Summary")
        print("="*50)
        print(f"📊 Total Messages: {stats['total_messages']}")
        print(f"💵 Total Cost: ${stats['total_cost']:.6f}")
        print(f"📈 Average Cost/Message: ${stats['average_cost_per_message']:.6f}")
        
        print("\n🤖 By Agent Type:")
        for agent, cost in stats['cost_by_agent'].items():
            percentage = (cost / max(stats['total_cost'], 0.000001)) * 100
            print(f"  {agent}: ${cost:.6f} ({percentage:.1f}%)")
        
        print("\n🔧 By Model Type:")
        for model, cost in stats['cost_by_model'].items():
            percentage = (cost / max(stats['total_cost'], 0.000001)) * 100
            print(f"  {model}: ${cost:.6f} ({percentage:.1f}%)")
        
        print("="*50)
