"""
Unit tests for Kafka client functionality
"""
import unittest
from unittest.mock import Mock, patch
from datetime import datetime
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.core.kafka_client import KafkaClient, json_serializer


class TestKafkaClient(unittest.TestCase):
    """Test cases for KafkaClient class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.kafka_client = KafkaClient()
    
    def tearDown(self):
        """Clean up after tests"""
        self.kafka_client.close_all()
    
    def test_json_serializer_datetime(self):
        """Test JSON serializer with datetime objects"""
        test_datetime = datetime(2024, 1, 1, 12, 0, 0)
        result = json_serializer(test_datetime)
        self.assertEqual(result, "2024-01-01T12:00:00")
    
    def test_json_serializer_invalid_type(self):
        """Test JSON serializer with invalid type"""
        with self.assertRaises(TypeError):
            json_serializer(object())
    
    @patch('src.core.kafka_client.KafkaProducer')
    def test_create_producer_success(self, mock_producer_class):
        """Test successful producer creation"""
        mock_producer = Mock()
        mock_producer_class.return_value = mock_producer
        
        producer = self.kafka_client.create_producer()
        
        self.assertIsNotNone(producer)
        self.assertEqual(self.kafka_client.producer, mock_producer)
        mock_producer_class.assert_called_once()
    
    @patch('src.core.kafka_client.KafkaProducer')
    def test_create_producer_failure(self, mock_producer_class):
        """Test producer creation failure"""
        mock_producer_class.side_effect = Exception("Connection failed")
        
        with self.assertRaises(Exception):
            self.kafka_client.create_producer()
    
    @patch('src.core.kafka_client.KafkaConsumer')
    def test_create_consumer_success(self, mock_consumer_class):
        """Test successful consumer creation"""
        mock_consumer = Mock()
        mock_consumer_class.return_value = mock_consumer
        
        topics = ["test_topic"]
        group_id = "test_group"
        
        consumer = self.kafka_client.create_consumer(topics, group_id)
        
        self.assertIsNotNone(consumer)
        self.assertIn(group_id, self.kafka_client.consumers)
        mock_consumer_class.assert_called_once()
    
    @patch('src.core.kafka_client.KafkaConsumer')
    def test_create_consumer_failure(self, mock_consumer_class):
        """Test consumer creation failure"""
        mock_consumer_class.side_effect = Exception("Connection failed")
        
        with self.assertRaises(Exception):
            self.kafka_client.create_consumer(["test_topic"], "test_group")
    
    @patch('src.core.kafka_client.KafkaProducer')
    def test_send_message_success(self, mock_producer_class):
        """Test successful message sending"""
        mock_producer = Mock()
        mock_future = Mock()
        mock_producer.send.return_value = mock_future
        mock_producer_class.return_value = mock_producer
        
        message = {"test": "data"}
        topic = "test_topic"
        key = "test_key"
        
        result = self.kafka_client.send_message(topic, message, key)
        
        mock_producer.send.assert_called_once_with(topic, value=message, key=key)
        mock_producer.flush.assert_called_once()
        self.assertEqual(result, mock_future)
    
    @patch('src.core.kafka_client.KafkaProducer')
    def test_send_message_failure(self, mock_producer_class):
        """Test message sending failure"""
        mock_producer = Mock()
        mock_producer.send.side_effect = Exception("Send failed")
        mock_producer_class.return_value = mock_producer
        
        with self.assertRaises(Exception):
            self.kafka_client.send_message("test_topic", {"test": "data"})
    
    def test_close_producer(self):
        """Test producer closing"""
        mock_producer = Mock()
        self.kafka_client.producer = mock_producer
        
        self.kafka_client.close_producer()
        
        mock_producer.close.assert_called_once()
        self.assertIsNone(self.kafka_client.producer)
    
    def test_close_consumer(self):
        """Test consumer closing"""
        mock_consumer = Mock()
        group_id = "test_group"
        self.kafka_client.consumers[group_id] = mock_consumer
        
        self.kafka_client.close_consumer(group_id)
        
        mock_consumer.close.assert_called_once()
        self.assertNotIn(group_id, self.kafka_client.consumers)
    
    def test_close_all(self):
        """Test closing all connections"""
        mock_producer = Mock()
        mock_consumer = Mock()
        
        self.kafka_client.producer = mock_producer
        self.kafka_client.consumers["test_group"] = mock_consumer
        
        self.kafka_client.close_all()
        
        mock_producer.close.assert_called_once()
        mock_consumer.close.assert_called_once()
        self.assertIsNone(self.kafka_client.producer)
        self.assertEqual(len(self.kafka_client.consumers), 0)
    
    @patch('src.core.kafka_client.KafkaProducer')
    def test_health_check_success(self, mock_producer_class):
        """Test successful health check"""
        mock_producer = Mock()
        mock_future = Mock()
        mock_future.get.return_value = None
        mock_producer.send.return_value = mock_future
        mock_producer_class.return_value = mock_producer
        
        result = self.kafka_client.health_check()
        
        self.assertTrue(result)
        mock_producer.send.assert_called_once()
        mock_future.get.assert_called_once_with(timeout=5)
    
    @patch('src.core.kafka_client.KafkaProducer')
    def test_health_check_failure(self, mock_producer_class):
        """Test health check failure"""
        mock_producer_class.side_effect = Exception("Connection failed")
        
        result = self.kafka_client.health_check()
        
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
