#!/usr/bin/env python3
"""
Streaming Chat Example

Author: Patrick Cooper

Demonstrates streaming responses from CURC-hosted LLM server.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.client.curc_llm_client import CURCLLMClient


def main():
    """Run streaming chat example."""
    
    # Create client
    client = CURCLLMClient(base_url="http://localhost:8000")
    
    print("CURC LLM Streaming Chat Example")
    print("=" * 50)
    print()
    
    # Check server health
    try:
        health = client.health_check()
        print(f"Server Status: {health}")
        print()
    except Exception as e:
        print(f"ERROR: Could not connect to server: {e}")
        return 1
    
    # Streaming chat
    message = "Write a short poem about scientific discovery."
    
    print(f"User: {message}")
    print()
    print("Assistant: ", end="", flush=True)
    
    try:
        for chunk in client.chat_stream(
            message=message,
            system_prompt="You are a creative AI assistant.",
            temperature=0.8,
            max_tokens=256
        ):
            print(chunk, end="", flush=True)
        
        print()  # Newline after stream completes
        print()
        print("=" * 50)
        
    except KeyboardInterrupt:
        print()
        print("Stream interrupted by user")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
