"""
Validation Tests for CURC LLM Client

Author: Patrick Cooper

Tests parameter validation, error handling, and edge cases.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.client.curc_llm_client import CURCLLMClient


class TestParameterValidation:
    """Test parameter validation and edge cases."""
    
    def test_empty_message(self):
        """Test chat with empty message."""
        client = CURCLLMClient()
        
        with patch.object(client.openai_client.chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Response"))]
            mock_create.return_value = mock_response
            
            response = client.chat("")
            assert response == "Response"
    
    def test_very_long_message(self):
        """Test chat with very long message."""
        client = CURCLLMClient()
        long_message = "test " * 1000
        
        with patch.object(client.openai_client.chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Response"))]
            mock_create.return_value = mock_response
            
            response = client.chat(long_message)
            assert response == "Response"
    
    def test_special_characters_in_message(self):
        """Test chat with special characters."""
        client = CURCLLMClient()
        special_message = "Test!@#$%^&*()_+-=[]{}|;':\",./<>?\n\t\r"
        
        with patch.object(client.openai_client.chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Response"))]
            mock_create.return_value = mock_response
            
            response = client.chat(special_message)
            assert response == "Response"
    
    def test_unicode_characters(self):
        """Test chat with unicode characters."""
        client = CURCLLMClient()
        unicode_message = "Hello 世界 🌍 こんにちは Здравствуй"
        
        with patch.object(client.openai_client.chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Response"))]
            mock_create.return_value = mock_response
            
            response = client.chat(unicode_message)
            assert response == "Response"
    
    def test_extreme_temperature_values(self):
        """Test chat with boundary temperature values."""
        client = CURCLLMClient()
        
        with patch.object(client.openai_client.chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Response"))]
            mock_create.return_value = mock_response
            
            # Minimum temperature
            client.chat("Test", temperature=0.0)
            assert mock_create.call_args.kwargs['temperature'] == 0.0
            
            # Maximum temperature
            client.chat("Test", temperature=2.0)
            assert mock_create.call_args.kwargs['temperature'] == 2.0
    
    def test_zero_max_tokens(self):
        """Test chat with zero max_tokens."""
        client = CURCLLMClient()
        
        with patch.object(client.openai_client.chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content=""))]
            mock_create.return_value = mock_response
            
            response = client.chat("Test", max_tokens=0)
            assert mock_create.call_args.kwargs['max_tokens'] == 0
    
    def test_very_large_max_tokens(self):
        """Test chat with very large max_tokens."""
        client = CURCLLMClient()
        
        with patch.object(client.openai_client.chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Response"))]
            mock_create.return_value = mock_response
            
            response = client.chat("Test", max_tokens=100000)
            assert mock_create.call_args.kwargs['max_tokens'] == 100000


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @patch('src.client.curc_llm_client.httpx.Client')
    def test_network_timeout(self, mock_httpx):
        """Test handling of network timeout."""
        import httpx
        mock_httpx.return_value.get.side_effect = httpx.TimeoutException("Timeout")
        
        client = CURCLLMClient()
        
        with pytest.raises(httpx.TimeoutException):
            client.health_check()
    
    @patch('src.client.curc_llm_client.httpx.Client')
    def test_connection_error(self, mock_httpx):
        """Test handling of connection error."""
        import httpx
        mock_httpx.return_value.get.side_effect = httpx.ConnectError("Cannot connect")
        
        client = CURCLLMClient()
        
        with pytest.raises(httpx.ConnectError):
            client.health_check()
    
    @patch('src.client.curc_llm_client.httpx.Client')
    def test_http_error_response(self, mock_httpx):
        """Test handling of HTTP error responses."""
        import httpx
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Server Error", request=Mock(), response=Mock()
        )
        mock_httpx.return_value.get.return_value = mock_response
        
        client = CURCLLMClient()
        
        with pytest.raises(httpx.HTTPStatusError):
            client.health_check()
    
    def test_malformed_response(self):
        """Test handling of malformed JSON response from get_models."""
        with patch('src.client.curc_llm_client.httpx.Client') as mock_httpx:
            mock_response = Mock()
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_httpx.return_value.get.return_value = mock_response

            client = CURCLLMClient()

            with pytest.raises(ValueError):
                client.get_models()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_multiple_clients_same_server(self):
        """Test multiple client instances to same server."""
        client1 = CURCLLMClient(base_url="http://localhost:8000")
        client2 = CURCLLMClient(base_url="http://localhost:8000")
        
        assert client1.base_url == client2.base_url
        assert client1 is not client2
    
    def test_client_close_multiple_times(self):
        """Test closing client multiple times doesn't error."""
        client = CURCLLMClient()
        
        # Should not raise error
        client.close()
        client.close()
    
    def test_context_manager_with_exception(self):
        """Test context manager properly closes on exception."""
        with patch('src.client.curc_llm_client.httpx.Client') as mock_httpx:
            mock_client = Mock()
            mock_httpx.return_value = mock_client
            
            try:
                with CURCLLMClient() as client:
                    raise ValueError("Test error")
            except ValueError:
                pass
            
            # Client should still be closed
            mock_client.close.assert_called_once()
    
    def test_streaming_empty_response(self):
        """Test streaming with completely empty response."""
        client = CURCLLMClient()
        
        with patch.object(client.openai_client.chat.completions, 'create') as mock_create:
            mock_chunks = [
                Mock(choices=[Mock(delta=Mock(content=None))]),
                Mock(choices=[Mock(delta=Mock(content=None))]),
            ]
            mock_create.return_value = iter(mock_chunks)
            
            chunks = list(client.chat_stream("Test"))
            assert chunks == []
    
    def test_completion_streaming_empty_response(self):
        """Test completion streaming with completely empty response."""
        client = CURCLLMClient()
        
        with patch.object(client.openai_client.completions, 'create') as mock_create:
            mock_chunks = [
                Mock(choices=[Mock(text=None)]),
                Mock(choices=[Mock(text=None)]),
            ]
            mock_create.return_value = iter(mock_chunks)
            
            chunks = list(client.complete_stream("Test"))
            assert chunks == []
    
    def test_base_url_with_multiple_slashes(self):
        """Test base URL normalization with multiple trailing slashes."""
        client = CURCLLMClient(base_url="http://localhost:8000///")
        # Should strip all trailing slashes
        assert not client.base_url.endswith('/')
    
    def test_custom_timeout_values(self):
        """Test various timeout configurations."""
        # Very short timeout
        client1 = CURCLLMClient(timeout=0.1)
        assert client1.timeout == 0.1
        
        # Very long timeout
        client2 = CURCLLMClient(timeout=3600.0)
        assert client2.timeout == 3600.0
        
        # Zero timeout (no timeout)
        client3 = CURCLLMClient(timeout=0)
        assert client3.timeout == 0
    
    def test_custom_retry_values(self):
        """Test various retry configurations."""
        # No retries
        client1 = CURCLLMClient(max_retries=0)
        assert client1.max_retries == 0
        
        # Many retries
        client2 = CURCLLMClient(max_retries=10)
        assert client2.max_retries == 10


class TestConcurrency:
    """Test concurrent usage scenarios."""
    
    def test_multiple_requests_same_client(self):
        """Test multiple sequential requests on same client."""
        client = CURCLLMClient()
        
        with patch.object(client.openai_client.chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Response"))]
            mock_create.return_value = mock_response
            
            # Multiple requests
            for i in range(10):
                response = client.chat(f"Message {i}")
                assert response == "Response"
            
            assert mock_create.call_count == 10
    
    def test_alternating_chat_and_complete(self):
        """Test alternating between chat and completion."""
        client = CURCLLMClient()
        
        with patch.object(client.openai_client.chat.completions, 'create') as mock_chat, \
             patch.object(client.openai_client.completions, 'create') as mock_complete:
            
            mock_chat.return_value = Mock(choices=[Mock(message=Mock(content="Chat"))])
            mock_complete.return_value = Mock(choices=[Mock(text="Complete")])
            
            response1 = client.chat("Test")
            assert response1 == "Chat"
            
            response2 = client.complete("Test")
            assert response2 == "Complete"
            
            response3 = client.chat("Test")
            assert response3 == "Chat"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
