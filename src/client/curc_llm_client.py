"""
CURC LLM Client SDK

Author: Patrick Cooper

This module provides a Python client for interacting with vLLM servers
hosted on CURC infrastructure. It offers both OpenAI-compatible and
native vLLM interfaces.
"""

import os
from typing import Dict, List, Optional, Union, Iterator
import httpx
from openai import OpenAI


class CURCLLMClient:
    """
    Client for interacting with CURC-hosted LLM inference servers.
    
    Provides both OpenAI-compatible chat completions and direct completions
    with streaming support.
    
    Examples:
        Basic usage:
        >>> client = CURCLLMClient(base_url="http://localhost:8000")
        >>> response = client.chat("Hello, how are you?")
        >>> print(response)
        
        With streaming:
        >>> for chunk in client.chat_stream("Tell me a story"):
        ...     print(chunk, end="", flush=True)
        
        Custom model and parameters:
        >>> response = client.chat(
        ...     "Explain quantum computing",
        ...     model="meta-llama/Llama-3.1-70B-Instruct",
        ...     temperature=0.7,
        ...     max_tokens=512
        ... )
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 3
    ):
        """
        Initialize CURC LLM client.
        
        Args:
            base_url: Base URL of the vLLM server
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key or os.getenv("CURC_LLM_API_KEY")
        self.timeout = timeout
        self.max_retries = max_retries
        self._model_cache: Optional[str] = None
        
        # Initialize OpenAI client for chat completions
        self.openai_client = OpenAI(
            base_url=f"{self.base_url}/v1",
            api_key=self.api_key or "dummy-key",  # vLLM requires a key even if not used
            timeout=timeout,
            max_retries=max_retries
        )
        
        # Initialize httpx client for direct API calls
        self.http_client = httpx.Client(
            timeout=timeout,
            headers=self._get_headers()
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def chat(
        self,
        message: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
        **kwargs
    ) -> str:
        """
        Send a chat message and get a response.
        
        Args:
            message: User message to send
            model: Model name (if None, uses server default)
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters passed to the API
            
        Returns:
            Generated response text
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": message})
        
        response = self.openai_client.chat.completions.create(
            model=model or self._get_default_model(),
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return response.choices[0].message.content
    
    def chat_stream(
        self,
        message: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
        **kwargs
    ) -> Iterator[str]:
        """
        Send a chat message and stream the response.
        
        Args:
            message: User message to send
            model: Model name (if None, uses server default)
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters passed to the API
            
        Yields:
            Response text chunks as they arrive
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": message})
        
        stream = self.openai_client.chat.completions.create(
            model=model or self._get_default_model(),
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
        **kwargs
    ) -> str:
        """
        Generate a completion for a prompt.
        
        Args:
            prompt: Input prompt
            model: Model name (if None, uses server default)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters passed to the API
            
        Returns:
            Generated completion text
        """
        response = self.openai_client.completions.create(
            model=model or self._get_default_model(),
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        return response.choices[0].text
    
    def complete_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
        **kwargs
    ) -> Iterator[str]:
        """
        Generate a completion with streaming.
        
        Args:
            prompt: Input prompt
            model: Model name (if None, uses server default)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters passed to the API
            
        Yields:
            Completion text chunks as they arrive
        """
        stream = self.openai_client.completions.create(
            model=model or self._get_default_model(),
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )
        
        for chunk in stream:
            if chunk.choices[0].text:
                yield chunk.choices[0].text
    
    def _get_default_model(self) -> str:
        """Return the first available model name, fetching once and caching."""
        if self._model_cache:
            return self._model_cache
        response = self.http_client.get(f"{self.base_url}/v1/models")
        response.raise_for_status()
        models = response.json().get("data", [])
        if not models:
            raise RuntimeError("No models available on the server.")
        self._model_cache = models[0]["id"]
        return self._model_cache

    def health_check(self) -> Dict:
        """
        Check server health status.

        Returns:
            Health status dictionary
        """
        response = self.http_client.get(f"{self.base_url}/health")
        response.raise_for_status()
        # vLLM 0.11+ returns 200 with empty body
        text = response.text.strip()
        return {"status": "ok", "http": response.status_code, "body": text or "(empty)"}
    
    def get_models(self) -> List[Dict]:
        """
        Get list of available models.
        
        Returns:
            List of model information dictionaries
        """
        response = self.http_client.get(f"{self.base_url}/v1/models")
        response.raise_for_status()
        return response.json()["data"]
    
    def close(self):
        """Close HTTP client connections."""
        self.http_client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def create_client(
    base_url: str = "http://localhost:8000",
    api_key: Optional[str] = None,
    **kwargs
) -> CURCLLMClient:
    """
    Factory function to create a CURC LLM client.
    
    Args:
        base_url: Base URL of the vLLM server
        api_key: Optional API key for authentication
        **kwargs: Additional arguments passed to CURCLLMClient
        
    Returns:
        Configured CURCLLMClient instance
    """
    return CURCLLMClient(base_url=base_url, api_key=api_key, **kwargs)
