"""
Tests for CURC LLM Client

Author: Patrick Cooper
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.client.curc_llm_client import CURCLLMClient, create_client


class TestCURCLLMClient:
    """Test suite for CURCLLMClient."""
    
    def test_client_initialization(self):
        """Test client can be initialized with default parameters."""
        client = CURCLLMClient()
        assert client.base_url == "http://localhost:8000"
        assert client.timeout == 60.0
        assert client.max_retries == 3
    
    def test_client_initialization_custom(self):
        """Test client initialization with custom parameters."""
        client = CURCLLMClient(
            base_url="http://example.com:9000",
            api_key="test-key",
            timeout=30.0,
            max_retries=5
        )
        assert client.base_url == "http://example.com:9000"
        assert client.api_key == "test-key"
        assert client.timeout == 30.0
        assert client.max_retries == 5
    
    def test_get_headers_without_api_key(self):
        """Test header generation without API key."""
        client = CURCLLMClient()
        headers = client._get_headers()
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
        assert "Authorization" not in headers
    
    def test_get_headers_with_api_key(self):
        """Test header generation with API key."""
        client = CURCLLMClient(api_key="test-key")
        headers = client._get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-key"
    
    @patch('src.client.curc_llm_client.OpenAI')
    def test_chat_simple(self, mock_openai):
        """Test simple chat interaction."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Hello, I'm doing well!"))]
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        client = CURCLLMClient()
        response = client.chat("How are you?")
        
        assert response == "Hello, I'm doing well!"
        mock_openai.return_value.chat.completions.create.assert_called_once()
    
    @patch('src.client.curc_llm_client.OpenAI')
    def test_chat_with_system_prompt(self, mock_openai):
        """Test chat with system prompt."""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        client = CURCLLMClient()
        client.chat("Hello", system_prompt="You are a helpful assistant.")
        
        call_args = mock_openai.return_value.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[0]['content'] == 'You are a helpful assistant.'
        assert messages[1]['role'] == 'user'
    
    @patch('src.client.curc_llm_client.OpenAI')
    def test_chat_stream(self, mock_openai):
        """Test streaming chat."""
        # Mock streaming response
        mock_chunks = [
            Mock(choices=[Mock(delta=Mock(content="Hello"))]),
            Mock(choices=[Mock(delta=Mock(content=" world"))]),
            Mock(choices=[Mock(delta=Mock(content="!"))]),
        ]
        mock_openai.return_value.chat.completions.create.return_value = iter(mock_chunks)
        
        client = CURCLLMClient()
        chunks = list(client.chat_stream("Hi"))
        
        assert chunks == ["Hello", " world", "!"]
    
    @patch('src.client.curc_llm_client.OpenAI')
    def test_complete(self, mock_openai):
        """Test completion generation."""
        mock_response = Mock()
        mock_response.choices = [Mock(text="bright and full of possibilities.")]
        mock_openai.return_value.completions.create.return_value = mock_response
        
        client = CURCLLMClient()
        response = client.complete("The future is ")
        
        assert response == "bright and full of possibilities."
    
    @patch('src.client.curc_llm_client.httpx.Client')
    def test_health_check(self, mock_httpx):
        """Test health check endpoint."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "healthy"}
        mock_httpx.return_value.get.return_value = mock_response
        
        client = CURCLLMClient()
        health = client.health_check()
        
        assert health == {"status": "healthy"}
        mock_httpx.return_value.get.assert_called_with("http://localhost:8000/health")
    
    @patch('src.client.curc_llm_client.httpx.Client')
    def test_get_models(self, mock_httpx):
        """Test get models endpoint."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"id": "model1", "object": "model"},
                {"id": "model2", "object": "model"}
            ]
        }
        mock_httpx.return_value.get.return_value = mock_response
        
        client = CURCLLMClient()
        models = client.get_models()
        
        assert len(models) == 2
        assert models[0]["id"] == "model1"
    
    def test_context_manager(self):
        """Test client can be used as context manager."""
        with CURCLLMClient() as client:
            assert client is not None
    
    def test_create_client_factory(self):
        """Test factory function."""
        client = create_client(base_url="http://test:8000", api_key="key")
        assert isinstance(client, CURCLLMClient)
        assert client.base_url == "http://test:8000"
        assert client.api_key == "key"


class TestClientIntegration:
    """Integration tests (require running server)."""
    
    @pytest.mark.integration
    def test_real_health_check(self):
        """Test health check against real server."""
        client = CURCLLMClient()
        
        try:
            health = client.health_check()
            assert "status" in health or health is not None
        except Exception:
            pytest.skip("Server not available for integration test")
    
    @pytest.mark.integration
    def test_real_chat(self):
        """Test chat against real server."""
        client = CURCLLMClient()
        
        try:
            response = client.chat(
                "Say 'test successful' if you can read this.",
                max_tokens=10
            )
            assert response is not None
            assert len(response) > 0
        except Exception:
            pytest.skip("Server not available for integration test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
