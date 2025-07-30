"""
Unit tests for cost monitor functionality
"""
import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.monitor import CostMonitor


class TestCostMonitor(unittest.TestCase):
    """Test cases for CostMonitor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('src.monitor.KafkaClient'):
            self.monitor = CostMonitor()
    
    def tearDown(self):
        """Clean up after tests"""
        if self.monitor.running:
            self.monitor.stop()
    
    def test_monitor_initialization(self):
        """Test monitor initialization"""
        self.assertFalse(self.monitor.running)
        self.assertIsNone(self.monitor.thread)
        self.assertEqual(self.monitor.total_cost, 0.0)
        self.assertEqual(self.monitor.message_count, 0)
        self.assertEqual(len(self.monitor.cost_by_agent), 0)
        self.assertEqual(len(self.monitor.cost_by_model), 0)
    
    @patch('src.monitor.threading.Thread')
    def test_start_monitor(self, mock_thread_class):
        """Test starting the monitor"""
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread
        
        self.monitor.start()
        
        self.assertTrue(self.monitor.running)
        self.assertEqual(self.monitor.thread, mock_thread)
        mock_thread_class.assert_called_once()
        mock_thread.start.assert_called_once()
    
    def test_start_monitor_already_running(self):
        """Test starting monitor when already running"""
        self.monitor.running = True
        
        with patch('src.monitor.threading.Thread') as mock_thread_class:
            self.monitor.start()
            mock_thread_class.assert_not_called()
    
    @patch('src.monitor.threading.Thread')
    def test_stop_monitor(self, mock_thread_class):
        """Test stopping the monitor"""
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread
        
        # Start and then stop
        self.monitor.start()
        self.monitor.stop()
        
        self.assertFalse(self.monitor.running)
        mock_thread.join.assert_called_once_with(timeout=5)
        self.monitor.kafka_client.close_all.assert_called_once()
    
    def test_process_cost_info_new_agent(self):
        """Test processing cost info for new agent"""
        cost_data = {
            "agent_type": "english_teacher",
            "cost_info": {
                "cost_usd": 0.005,
                "model_name": "gemini-1.5-flash"
            }
        }
        
        self.monitor._process_cost_info(cost_data)
        
        self.assertEqual(self.monitor.total_cost, 0.005)
        self.assertEqual(self.monitor.message_count, 1)
        self.assertEqual(self.monitor.cost_by_agent["english_teacher"], 0.005)
        self.assertEqual(self.monitor.cost_by_model["gemini-1.5-flash"], 0.005)
    
    def test_process_cost_info_existing_agent(self):
        """Test processing cost info for existing agent"""
        # First cost info
        cost_data_1 = {
            "agent_type": "english_teacher",
            "cost_info": {
                "cost_usd": 0.005,
                "model_name": "gemini-1.5-flash"
            }
        }
        
        # Second cost info for same agent
        cost_data_2 = {
            "agent_type": "english_teacher",
            "cost_info": {
                "cost_usd": 0.003,
                "model_name": "gemini-1.5-flash"
            }
        }
        
        self.monitor._process_cost_info(cost_data_1)
        self.monitor._process_cost_info(cost_data_2)
        
        self.assertEqual(self.monitor.total_cost, 0.008)
        self.assertEqual(self.monitor.message_count, 2)
        self.assertEqual(self.monitor.cost_by_agent["english_teacher"], 0.008)
        self.assertEqual(self.monitor.cost_by_model["gemini-1.5-flash"], 0.008)
    
    def test_process_cost_info_multiple_agents(self):
        """Test processing cost info for multiple agents"""
        cost_data_english = {
            "agent_type": "english_teacher",
            "cost_info": {
                "cost_usd": 0.005,
                "model_name": "gemini-1.5-flash"
            }
        }
        
        cost_data_chinese = {
            "agent_type": "chinese_teacher",
            "cost_info": {
                "cost_usd": 0.007,
                "model_name": "ollama"
            }
        }
        
        self.monitor._process_cost_info(cost_data_english)
        self.monitor._process_cost_info(cost_data_chinese)
        
        self.assertEqual(self.monitor.total_cost, 0.012)
        self.assertEqual(self.monitor.message_count, 2)
        self.assertEqual(self.monitor.cost_by_agent["english_teacher"], 0.005)
        self.assertEqual(self.monitor.cost_by_agent["chinese_teacher"], 0.007)
        self.assertEqual(self.monitor.cost_by_model["gemini-1.5-flash"], 0.005)
        self.assertEqual(self.monitor.cost_by_model["ollama"], 0.007)
    
    def test_process_cost_info_missing_data(self):
        """Test processing cost info with missing data"""
        cost_data = {
            "agent_type": "unknown_agent",
            "cost_info": {}  # Missing cost_usd and model_name
        }
        
        # Should not raise exception, should use defaults
        try:
            self.monitor._process_cost_info(cost_data)
            self.assertEqual(self.monitor.total_cost, 0.0)
            self.assertEqual(self.monitor.message_count, 1)
            self.assertEqual(self.monitor.cost_by_agent["unknown_agent"], 0.0)
            self.assertEqual(self.monitor.cost_by_model["unknown"], 0.0)
        except Exception as e:
            self.fail(f"_process_cost_info raised exception with missing data: {e}")
    
    def test_get_statistics(self):
        """Test getting statistics"""
        # Add some cost data
        cost_data = {
            "agent_type": "english_teacher",
            "cost_info": {
                "cost_usd": 0.01,
                "model_name": "gemini-1.5-flash"
            }
        }
        
        self.monitor._process_cost_info(cost_data)
        self.monitor._process_cost_info(cost_data)  # Add twice
        
        stats = self.monitor.get_statistics()
        
        self.assertEqual(stats["total_cost"], 0.02)
        self.assertEqual(stats["total_messages"], 2)
        self.assertEqual(stats["average_cost_per_message"], 0.01)
        self.assertIn("english_teacher", stats["cost_by_agent"])
        self.assertIn("gemini-1.5-flash", stats["cost_by_model"])
        self.assertIn("timestamp", stats)
    
    def test_get_statistics_no_messages(self):
        """Test getting statistics with no messages"""
        stats = self.monitor.get_statistics()
        
        self.assertEqual(stats["total_cost"], 0.0)
        self.assertEqual(stats["total_messages"], 0)
        self.assertEqual(stats["average_cost_per_message"], 0.0)  # Should not divide by zero
        self.assertEqual(len(stats["cost_by_agent"]), 0)
        self.assertEqual(len(stats["cost_by_model"]), 0)
    
    def test_reset_statistics(self):
        """Test resetting statistics"""
        # Add some cost data first
        cost_data = {
            "agent_type": "english_teacher",
            "cost_info": {
                "cost_usd": 0.01,
                "model_name": "gemini-1.5-flash"
            }
        }
        
        self.monitor._process_cost_info(cost_data)
        
        # Verify data exists
        self.assertGreater(self.monitor.total_cost, 0)
        self.assertGreater(self.monitor.message_count, 0)
        
        # Reset and verify
        self.monitor.reset_statistics()
        
        self.assertEqual(self.monitor.total_cost, 0.0)
        self.assertEqual(self.monitor.message_count, 0)
        self.assertEqual(len(self.monitor.cost_by_agent), 0)
        self.assertEqual(len(self.monitor.cost_by_model), 0)
    
    @patch('builtins.print')
    def test_print_summary(self, mock_print):
        """Test printing summary"""
        # Add some test data
        cost_data_1 = {
            "agent_type": "english_teacher",
            "cost_info": {
                "cost_usd": 0.01,
                "model_name": "gemini-1.5-flash"
            }
        }
        
        cost_data_2 = {
            "agent_type": "chinese_teacher",
            "cost_info": {
                "cost_usd": 0.005,
                "model_name": "ollama"
            }
        }
        
        self.monitor._process_cost_info(cost_data_1)
        self.monitor._process_cost_info(cost_data_2)
        
        self.monitor.print_summary()
        
        # Verify print was called multiple times with expected content
        self.assertTrue(mock_print.called)
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        summary_text = ' '.join(print_calls)
        
        self.assertIn("Cost Statistics Summary", summary_text)
        self.assertIn("Total Messages: 2", summary_text)
        self.assertIn("Total Cost: $0.015000", summary_text)
        self.assertIn("english_teacher", summary_text)
        self.assertIn("chinese_teacher", summary_text)


if __name__ == '__main__':
    unittest.main()
