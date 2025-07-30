"""
Unit tests for data models
"""
import unittest
from datetime import datetime
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.core.models import (
    Message, Response, CostInfo, SystemStatus,
    LanguageType, AgentType
)


class TestModels(unittest.TestCase):
    """Test cases for data models"""
    
    def test_language_type_enum(self):
        """Test LanguageType enum values"""
        self.assertEqual(LanguageType.CHINESE, "chinese")
        self.assertEqual(LanguageType.ENGLISH, "english")
        self.assertEqual(LanguageType.AUTO, "auto")
    
    def test_agent_type_enum(self):
        """Test AgentType enum values"""
        self.assertEqual(AgentType.CHINESE_TEACHER, "chinese_teacher")
        self.assertEqual(AgentType.ENGLISH_TEACHER, "english_teacher")
    
    def test_message_model(self):
        """Test Message model creation and validation"""
        message = Message(
            message_id="test-123",
            user_id="user-456",
            content="Hello world",
            language=LanguageType.ENGLISH,
            timestamp=datetime.now()
        )
        
        self.assertEqual(message.message_id, "test-123")
        self.assertEqual(message.user_id, "user-456")
        self.assertEqual(message.content, "Hello world")
        self.assertEqual(message.language, LanguageType.ENGLISH)
        self.assertIsInstance(message.timestamp, datetime)
    
    def test_message_dict_conversion(self):
        """Test Message model dict conversion"""
        message = Message(
            message_id="test-123",
            user_id="user-456",
            content="Hello world",
            language=LanguageType.ENGLISH,
            timestamp=datetime.now()
        )
        
        message_dict = message.dict()
        self.assertEqual(message_dict["message_id"], "test-123")
        self.assertEqual(message_dict["language"], "english")  # enum value
    
    def test_cost_info_model(self):
        """Test CostInfo model creation"""
        cost_info = CostInfo(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost_usd=0.001,
            model_name="test-model"
        )
        
        self.assertEqual(cost_info.input_tokens, 100)
        self.assertEqual(cost_info.output_tokens, 50)
        self.assertEqual(cost_info.total_tokens, 150)
        self.assertEqual(cost_info.cost_usd, 0.001)
        self.assertEqual(cost_info.model_name, "test-model")
    
    def test_response_model(self):
        """Test Response model creation"""
        cost_info = CostInfo(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost_usd=0.001,
            model_name="test-model"
        )
        
        response = Response(
            message_id="test-123",
            success=True,
            content="Test response",
            agent_type=AgentType.ENGLISH_TEACHER,
            cost_info=cost_info,
            response_time=1.5,
            timestamp=datetime.now()
        )
        
        self.assertEqual(response.message_id, "test-123")
        self.assertTrue(response.success)
        self.assertEqual(response.content, "Test response")
        self.assertEqual(response.agent_type, AgentType.ENGLISH_TEACHER)
        self.assertEqual(response.response_time, 1.5)
        self.assertIsInstance(response.cost_info, CostInfo)
    
    def test_response_dict_conversion(self):
        """Test Response model dict conversion"""
        cost_info = CostInfo(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost_usd=0.001,
            model_name="test-model"
        )
        
        response = Response(
            message_id="test-123",
            success=True,
            content="Test response",
            agent_type=AgentType.ENGLISH_TEACHER,
            cost_info=cost_info,
            response_time=1.5,
            timestamp=datetime.now()
        )
        
        response_dict = response.dict()
        self.assertEqual(response_dict["agent_type"], "english_teacher")  # enum value
        self.assertIsInstance(response_dict["cost_info"], dict)
    
    def test_system_status_model(self):
        """Test SystemStatus model creation"""
        status = SystemStatus(
            kafka_connected=True,
            active_consumers=["chinese_teacher", "english_teacher"],
            total_messages_processed=100,
            total_cost=0.05,
            uptime_seconds=3600
        )
        
        self.assertTrue(status.kafka_connected)
        self.assertEqual(len(status.active_consumers), 2)
        self.assertEqual(status.total_messages_processed, 100)
        self.assertEqual(status.total_cost, 0.05)
        self.assertEqual(status.uptime_seconds, 3600)
    
    def test_message_validation_error(self):
        """Test Message model validation errors"""
        with self.assertRaises(ValueError):
            # Missing required field
            Message(
                user_id="user-456",
                content="Hello world",
                language=LanguageType.ENGLISH,
                timestamp=datetime.now()
            )


if __name__ == '__main__':
    unittest.main()
