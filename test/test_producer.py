"""
Unit tests for message producer functionality
"""
import unittest
from unittest.mock import Mock, patch
from datetime import datetime
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.producer import MessageProducer
from src.core.models import LanguageType


class TestMessageProducer(unittest.TestCase):
    """Test cases for MessageProducer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('src.producer.KafkaClient'):
            self.producer = MessageProducer()
    
    def test_detect_language_chinese_characters(self):
        """Test language detection with Chinese characters"""
        chinese_text = "你好世界"
        result = self.producer.detect_language(chinese_text)
        self.assertEqual(result, LanguageType.CHINESE)
    
    def test_detect_language_english_text(self):
        """Test language detection with English text"""
        english_text = "Hello world"
        result = self.producer.detect_language(english_text)
        self.assertEqual(result, LanguageType.ENGLISH)
    
    def test_detect_language_mixed_text_with_chinese(self):
        """Test language detection with mixed text containing Chinese"""
        mixed_text = "Hello 你好"
        result = self.producer.detect_language(mixed_text)
        self.assertEqual(result, LanguageType.CHINESE)  # Should prefer Chinese
    
    def test_detect_language_pure_english(self):
        """Test language detection with pure English"""
        english_text = "This is a test message in English."
        result = self.producer.detect_language(english_text)
        self.assertEqual(result, LanguageType.ENGLISH)
    
    @patch('src.producer.LANGDETECT_AVAILABLE', False)
    def test_detect_language_without_langdetect(self):
        """Test language detection fallback when langdetect unavailable"""
        # Test Chinese text
        chinese_text = "你好世界"
        result = self.producer.detect_language(chinese_text)
        self.assertEqual(result, LanguageType.CHINESE)
        
        # Test English text
        english_text = "Hello world"
        result = self.producer.detect_language(english_text)
        self.assertEqual(result, LanguageType.ENGLISH)
    
    def test_contains_chinese_with_chinese_chars(self):
        """Test _contains_chinese method with Chinese characters"""
        self.assertTrue(self.producer._contains_chinese("你好"))
        self.assertTrue(self.producer._contains_chinese("Hello 你好"))
        self.assertTrue(self.producer._contains_chinese("測試"))
    
    def test_contains_chinese_without_chinese_chars(self):
        """Test _contains_chinese method without Chinese characters"""
        self.assertFalse(self.producer._contains_chinese("Hello"))
        self.assertFalse(self.producer._contains_chinese("123"))
        self.assertFalse(self.producer._contains_chinese("!@#$%"))
    
    def test_route_to_topic_chinese(self):
        """Test topic routing for Chinese language"""
        topic = self.producer.route_to_topic(LanguageType.CHINESE)
        self.assertEqual(topic, "chinese_teacher")
    
    def test_route_to_topic_english(self):
        """Test topic routing for English language"""
        topic = self.producer.route_to_topic(LanguageType.ENGLISH)
        self.assertEqual(topic, "english_teacher")
    
    @patch('src.producer.uuid.uuid4')
    @patch('src.producer.datetime')
    async def test_send_message_success(self, mock_datetime, mock_uuid):
        """Test successful message sending"""
        # Setup mocks
        mock_uuid.return_value = Mock()
        mock_uuid.return_value.__str__ = Mock(return_value="test-message-id")
        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)
        
        # Mock kafka client
        self.producer.kafka_client.send_message = Mock()
        
        # Test message
        content = "Hello world"
        user_id = "test_user"
        
        result = await self.producer.send_message(content, user_id)
        
        # Verify result
        self.assertTrue(result["success"])
        self.assertEqual(result["message_id"], "test-message-id")
        self.assertEqual(result["topic"], "english_teacher")
        self.assertEqual(result["language"], LanguageType.ENGLISH)
        self.assertIsNone(result["error"])
        
        # Verify kafka client was called
        self.producer.kafka_client.send_message.assert_called_once()
    
    @patch('src.producer.uuid.uuid4')
    async def test_send_message_chinese(self, mock_uuid):
        """Test sending Chinese message"""
        # Setup mocks
        mock_uuid.return_value = Mock()
        mock_uuid.return_value.__str__ = Mock(return_value="test-message-id")
        
        # Mock kafka client
        self.producer.kafka_client.send_message = Mock()
        
        # Test Chinese message
        content = "你好世界"
        
        result = await self.producer.send_message(content)
        
        # Verify Chinese routing
        self.assertTrue(result["success"])
        self.assertEqual(result["topic"], "chinese_teacher")
        self.assertEqual(result["language"], LanguageType.CHINESE)
    
    async def test_send_message_failure(self):
        """Test message sending failure"""
        # Mock kafka client to raise exception
        self.producer.kafka_client.send_message = Mock(side_effect=Exception("Send failed"))
        
        result = await self.producer.send_message("test message")
        
        # Verify failure result
        self.assertFalse(result["success"])
        self.assertIsNone(result["message_id"])
        self.assertIsNone(result["topic"])
        self.assertIsNone(result["language"])
        self.assertEqual(result["error"], "Send failed")
    
    def test_close(self):
        """Test producer closing"""
        self.producer.kafka_client.close_producer = Mock()
        
        self.producer.close()
        
        self.producer.kafka_client.close_producer.assert_called_once()
    
    @patch('src.producer.detect', return_value='zh-cn')
    @patch('src.producer.LANGDETECT_AVAILABLE', True)
    def test_detect_language_with_langdetect_chinese(self, mock_detect):
        """Test language detection using langdetect for Chinese"""
        result = self.producer.detect_language("你好世界")
        self.assertEqual(result, LanguageType.CHINESE)
        mock_detect.assert_called_once_with("你好世界")
    
    @patch('src.producer.detect', return_value='en')
    @patch('src.producer.LANGDETECT_AVAILABLE', True)
    def test_detect_language_with_langdetect_english(self, mock_detect):
        """Test language detection using langdetect for English"""
        result = self.producer.detect_language("Hello world")
        self.assertEqual(result, LanguageType.ENGLISH)
        mock_detect.assert_called_once_with("Hello world")
    
    @patch('src.producer.detect', side_effect=Exception("Detection failed"))
    @patch('src.producer.LANGDETECT_AVAILABLE', True)
    def test_detect_language_with_langdetect_fallback(self, mock_detect):
        """Test language detection fallback when langdetect fails"""
        # Should fallback to character-based detection
        result = self.producer.detect_language("你好世界")
        self.assertEqual(result, LanguageType.CHINESE)


if __name__ == '__main__':
    unittest.main()
