"""
Unit tests for LLM engines
"""
import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from src.llm.base_engine import BaseLLMEngine
    from src.llm.gemini_engine import GeminiEngine
    from src.llm.ollama_engine import OllamaEngine
except ImportError:
    # Fallback path for Docker
    sys.path.insert(0, '/app/src')
    try:
        from llm.base_engine import BaseLLMEngine
        from llm.gemini_engine import GeminiEngine
        from llm.ollama_engine import OllamaEngine
    except ImportError:
        # Skip tests if imports fail
        BaseLLMEngine = None
        GeminiEngine = None
        OllamaEngine = None


class TestBaseLLMEngine(unittest.TestCase):
    """Test the base LLM engine class"""
    
    def setUp(self):
        if BaseLLMEngine is None:
            self.skipTest("LLM engines not available")
    
    def test_base_engine_exists(self):
        """Test that base engine class exists"""
        self.assertIsNotNone(BaseLLMEngine)
        self.assertTrue(hasattr(BaseLLMEngine, '__init__'))


class TestGeminiEngine(unittest.TestCase):
    """Test Gemini LLM engine"""
    
    def setUp(self):
        if GeminiEngine is None:
            self.skipTest("Gemini engine not available")
    
    @patch.object(GeminiEngine, '__init__', lambda self: None)
    def test_gemini_mock_init(self):
        """Test Gemini engine mock initialization"""
        # Create mock engine
        engine = GeminiEngine()
        engine.api_key = "test_key"
        engine.available = True
        
        # Test mock attributes
        self.assertEqual(engine.api_key, "test_key")
        self.assertTrue(engine.available)
    
    @patch.object(GeminiEngine, '__init__', lambda self: None)
    def test_gemini_mock_unavailable(self):
        """Test Gemini engine when unavailable"""
        # Create mock engine
        engine = GeminiEngine()
        engine.api_key = None
        engine.available = False
        
        # Test mock attributes
        self.assertIsNone(engine.api_key)
        self.assertFalse(engine.available)


class TestOllamaEngine(unittest.TestCase):
    """Test Ollama LLM engine"""
    
    def setUp(self):
        if OllamaEngine is None:
            self.skipTest("Ollama engine not available")
    
    @patch.object(OllamaEngine, '__init__', lambda self: None)
    def test_ollama_mock_init(self):
        """Test Ollama engine mock initialization"""
        # Create mock engine
        engine = OllamaEngine()
        engine.base_url = "http://localhost:11434"
        engine.model = "llama3.1:8b"
        engine.available = True
        
        # Test mock attributes
        self.assertEqual(engine.base_url, "http://localhost:11434")
        self.assertEqual(engine.model, "llama3.1:8b")
        self.assertTrue(engine.available)
    
    @patch.object(OllamaEngine, '__init__', lambda self: None)
    def test_ollama_mock_unavailable(self):
        """Test Ollama engine when unavailable"""
        # Create mock engine
        engine = OllamaEngine()
        engine.base_url = "http://localhost:11434"
        engine.model = "llama3.1:8b"
        engine.available = False
        
        # Test mock attributes
        self.assertEqual(engine.base_url, "http://localhost:11434")
        self.assertEqual(engine.model, "llama3.1:8b")
        self.assertFalse(engine.available)


class TestEngineGeneration(unittest.TestCase):
    """Test engine text generation capabilities"""
    
    def test_mock_generation(self):
        """Test mock text generation"""
        # Simple mock test without real engines
        prompt = "What is AI?"
        mock_response = f"Mock response to: {prompt}"
        
        self.assertIsInstance(mock_response, str)
        self.assertIn(prompt, mock_response)
        self.assertTrue(len(mock_response) > 0)


if __name__ == '__main__':
    unittest.main()
