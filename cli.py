#!/usr/bin/env python3
"""
Teaching System V1 - Interactive CLI
Supports free-form question input with instant responses and cost information
"""

import asyncio
import logging
import os
import signal
import sys
from typing import Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from src.producer import MessageProducer
from src.consumer import ConsumerManager
from src.monitor import CostMonitor
from src.agents.chinese_agent import ChineseAgent
from src.agents.english_agent import EnglishAgent
from src.llm.gemini_engine import GeminiEngine
from src.llm.ollama_engine import OllamaEngine
from src.core.kafka_client import KafkaClient
from src.core.config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TeachingSystemCLI:
    """
    Teaching System CLI
    
    Main interface for the intelligent teaching system with interactive capabilities
    """
    
    def __init__(self):
        self.console = Console()
        self.config = Config()
        self.running = False
        
        # Core components
        self.producer = None
        self.consumer_manager = None
        self.cost_monitor = None
        self.kafka_client = None
        
        # Response collection
        self.responses: Dict[str, Any] = {}
        self.response_event = asyncio.Event()
        
    async def initialize(self):
        """
        Initialize system components

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.console.print(Panel.fit("🚀 Initializing Teaching System...", style="blue"))
            
            # Check configuration
            config_status = self.config.validate_config()
            if not config_status["valid"]:
                for error in config_status["errors"]:
                    self.console.print(f"❌ Configuration error: {error}", style="red")
                return False
            
            for warning in config_status["warnings"]:
                self.console.print(f"⚠️  {warning}", style="yellow")
            
            # Check Kafka connection
            self.kafka_client = KafkaClient()
            if not self.kafka_client.health_check():
                self.console.print("❌ Kafka connection failed! Please ensure Kafka service is running.", style="red")
                return False
            
            self.console.print("✅ Kafka connection successful", style="green")
            
            # Initialize LLM engines
            gemini_engine = GeminiEngine()
            ollama_engine = OllamaEngine()
            
            # Check environment variable for preferred engine
            preferred_engine = os.getenv("PREFERRED_ENGINE", "").lower()
            
            if preferred_engine == "gemini":
                if gemini_engine.available:
                    primary_engine = gemini_engine
                    self.console.print("✅ Force using Gemini engine", style="green")
                else:
                    self.console.print("❌ Gemini engine unavailable, trying Ollama", style="red")
                    if ollama_engine.available:
                        primary_engine = ollama_engine
                        self.console.print("✅ Switched to Ollama engine", style="green")
                    else:
                        self.console.print("❌ No available LLM engine!", style="red")
                        return False
            elif preferred_engine == "ollama":
                if ollama_engine.available:
                    primary_engine = ollama_engine
                    self.console.print("✅ Force using Ollama engine", style="green")
                else:
                    self.console.print("❌ Ollama engine unavailable, trying Gemini", style="red")
                    if gemini_engine.available:
                        primary_engine = gemini_engine
                        self.console.print("✅ Switched to Gemini engine", style="green")
                    else:
                        self.console.print("❌ No available LLM engine!", style="red")
                        return False
            else:
                # Auto selection (prefer Gemini)
                if gemini_engine.available:
                    primary_engine = gemini_engine
                    self.console.print("✅ Gemini engine enabled", style="green")
                elif ollama_engine.available:
                    primary_engine = ollama_engine
                    self.console.print("✅ Ollama engine enabled", style="green")
                else:
                    self.console.print("❌ No available LLM engine!", style="red")
                    return False
            
            # Initialize Agents
            chinese_agent = ChineseAgent(primary_engine)
            english_agent = EnglishAgent(primary_engine)
            
            # Initialize consumer manager
            self.consumer_manager = ConsumerManager()
            self.consumer_manager.add_agent_consumer(
                chinese_agent, 
                [self.config.TOPICS["chinese_teacher"]]
            )
            self.consumer_manager.add_agent_consumer(
                english_agent, 
                [self.config.TOPICS["english_teacher"]]
            )
            
            # Initialize cost monitor
            self.cost_monitor = CostMonitor()
            
            # Initialize producer
            self.producer = MessageProducer()
            
            # Setup response listener
            await self._setup_response_listener()
            
            self.console.print("✅ System initialization complete", style="green")
            return True
            
        except Exception as e:
            self.console.print(f"❌ Initialization failed: {e}", style="red")
            logger.error(f"Initialization failed: {e}")
            return False
    
    async def _setup_response_listener(self):
        """
        Setup response listener

        Creates and starts the response listener task for handling incoming responses
        """
        try:
            # Create response consumer
            response_consumer = self.kafka_client.create_consumer(
                topics=[self.config.TOPICS["responses"]],
                group_id="cli_response_group"
            )
            
            # Start response listener task
            self.response_listener_task = asyncio.create_task(self._listen_responses(response_consumer))
            logger.info("Response listener task created")
            
        except Exception as e:
            logger.error(f"Failed to setup response listener: {e}")
    
    async def _listen_responses(self, consumer):
        """
        Listen for responses

        Args:
            consumer: Kafka consumer for responses topic
        """
        logger.info("Response listener started")
        while True:  # Run permanently, not dependent on self.running
            try:
                message_pack = consumer.poll(timeout_ms=100)
                
                if not message_pack:
                    await asyncio.sleep(0.1)
                    continue
                
                for topic_partition, messages in message_pack.items():
                    for kafka_message in messages:
                        response_data = kafka_message.value
                        message_id = response_data.get("message_id")
                        
                        if message_id:
                            logger.info(f"Received response for message_id: {message_id}")
                            self.responses[message_id] = response_data
                            self.response_event.set()
                            
            except Exception as e:
                logger.error(f"Error listening responses: {e}")
                await asyncio.sleep(1)
    
    async def start_system(self):
        """
        Start system services

        Starts all necessary services including consumers and monitoring
        """
        try:
            # Start consumers
            self.consumer_manager.start_all()
            await asyncio.sleep(0.5)  # Wait for consumers to start
            
            # Start cost monitoring
            self.cost_monitor.start()
            await asyncio.sleep(0.5)  # Wait for monitoring to start
            
            # Set running state to enable response listening
            self.running = True
            
            self.console.print("✅ All services started", style="green")
            
        except Exception as e:
            self.console.print(f"❌ Failed to start services: {e}", style="red")
            raise
    
    async def ask_question(self, question: str) -> Dict[str, Any]:
        """
        Send question and wait for answer

        Args:
            question: Question to be answered

        Returns:
            Dictionary containing response data
        """
        try:
            # Send message
            result = await self.producer.send_message(question)
            
            if not result["success"]:
                return {
                    "success": False,
                    "content": f"Send failed: {result['error']}",
                    "cost_info": None
                }
            
            message_id = result["message_id"]
            
            # Wait for response (max 30 seconds)
            timeout = 30
            start_time = asyncio.get_event_loop().time()
            
            while True:
                # Check if response received
                if message_id in self.responses:
                    response_data = self.responses.pop(message_id)
                    logger.info(f"Found response for message_id: {message_id}")
                    return response_data
                
                # Check timeout
                if asyncio.get_event_loop().time() - start_time > timeout:
                    logger.warning(f"Timeout waiting for response to message_id: {message_id}")
                    return {
                        "success": False,
                        "content": "Response timeout",
                        "cost_info": None
                    }
                
                # Clear event and wait for new response
                self.response_event.clear()
                try:
                    await asyncio.wait_for(self.response_event.wait(), timeout=1.0)
                except asyncio.TimeoutError:
                    # Check every second, continue loop
                    continue
                
        except asyncio.TimeoutError:
            return {
                "success": False,
                "content": "Response timeout",
                "cost_info": None
            }
        except Exception as e:
            logger.error(f"Error asking question: {e}")
            return {
                "success": False,
                "content": f"Processing error: {str(e)}",
                "cost_info": None
            }
    
    def print_response(self, response: Dict[str, Any]):
        """
        Format and print response

        Args:
            response: Response dictionary to display
        """
        if response.get("success"):
            # Successful response
            agent_type = response.get("agent_type", "unknown")
            content = response.get("content", "")
            cost_info = response.get("cost_info", {})
            response_time = response.get("response_time", 0)
            
            # Choose icon and title
            if agent_type == "chinese_teacher":
                icon = "🧑‍🏫"
                title = "Chinese Teacher Answer"
            else:
                icon = "👨‍🏫"
                title = "English Teacher Answer"
            
            # Print answer
            self.console.print(Panel(
                content,
                title=f"{icon} {title}",
                style="green"
            ))
            
            # Print cost information
            if cost_info:
                cost_table = Table(show_header=True, header_style="bold magenta")
                cost_table.add_column("Item", style="cyan")
                cost_table.add_column("Value", style="white")
                
                cost_table.add_row("Input tokens", str(cost_info.get("input_tokens", 0)))
                cost_table.add_row("Output tokens", str(cost_info.get("output_tokens", 0)))
                cost_table.add_row("Total cost", f"${cost_info.get('cost_usd', 0):.6f}")
                cost_table.add_row("Model", cost_info.get("model_name", "unknown"))
                cost_table.add_row("Response time", f"{response_time:.2f}s")
                
                self.console.print(Panel(
                    cost_table,
                    title="💰 Cost Information",
                    style="blue"
                ))
        else:
            # Error response
            error_content = response.get("content", "Unknown error")
            self.console.print(Panel(
                error_content,
                title="❌ Error",
                style="red"
            ))
    
    async def run_interactive_mode(self):
        """
        Run interactive mode

        Main interactive loop for handling user questions
        """
        self.running = True
        
        # Display welcome information
        welcome_text = Text()
        welcome_text.append("🤖 Teaching System V1\n", style="bold blue")
        welcome_text.append("Supports Chinese and English questions with automatic routing\n", style="white")
        welcome_text.append("Type 'quit' or 'exit' to exit the system", style="yellow")
        
        self.console.print(Panel(welcome_text, title="Welcome", style="green"))
        
        try:
            while self.running:
                # Get user input
                question = self.console.input("\n[bold cyan]Please enter your question (type 'quit' to exit): [/bold cyan]")
                
                # Check exit commands
                if question.lower() in ['quit', 'exit', '退出', 'q']:
                    break
                
                if not question.strip():
                    self.console.print("Please enter a valid question", style="yellow")
                    continue
                
                # Show processing status
                with self.console.status("[bold green]Processing..."):
                    response = await self.ask_question(question)
                
                # Print response
                self.print_response(response)
                
        except KeyboardInterrupt:
            self.console.print("\n\nReceived interrupt signal, exiting...", style="yellow")
        except Exception as e:
            self.console.print(f"\n\n❌ Runtime error: {e}", style="red")
            logger.error(f"Runtime error: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """
        Shutdown system

        Gracefully shutdown all system components
        """
        self.running = False
        
        self.console.print("\n🔄 Shutting down system...", style="yellow")
        
        try:
            # Print final statistics
            if self.cost_monitor:
                self.cost_monitor.print_summary()
                self.cost_monitor.stop()
            
            # Close consumers
            if self.consumer_manager:
                self.consumer_manager.stop_all()
            
            # Close producer
            if self.producer:
                self.producer.close()
            
            # Close Kafka client
            if self.kafka_client:
                self.kafka_client.close_all()
            
            self.console.print("✅ System shutdown safely", style="green")
            self.console.print("Goodbye! Thank you for using the Teaching System!", style="blue")
            
        except Exception as e:
            self.console.print(f"⚠️  Error during shutdown: {e}", style="yellow")


async def main():
    """
    Main function

    Entry point for the application
    """
    cli = TeachingSystemCLI()
    
    # Setup signal handling
    def signal_handler(signum, frame):
        asyncio.create_task(cli.shutdown())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize system
        if not await cli.initialize():
            sys.exit(1)
        
        # Start system
        await cli.start_system()
        
        # Run interactive mode
        await cli.run_interactive_mode()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
