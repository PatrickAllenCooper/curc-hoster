#!/usr/bin/env python3
"""
Basic Chat Example

Author: Patrick Cooper

Demonstrates simple chat interaction with CURC-hosted LLM server.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.client.curc_llm_client import CURCLLMClient


def main():
    """Run basic chat example."""
    
    # Create client (assumes SSH tunnel is active on localhost:8000)
    client = CURCLLMClient(base_url="http://localhost:8000")
    
    print("CURC LLM Basic Chat Example")
    print("=" * 50)
    print()
    
    # Check server health
    try:
        health = client.health_check()
        print(f"Server Status: {health}")
        print()
    except Exception as e:
        print(f"ERROR: Could not connect to server: {e}")
        print()
        print("Make sure:")
        print("  1. vLLM server is running on CURC")
        print("  2. SSH tunnel is active: ./scripts/create_tunnel.sh <JOB_ID>")
        print()
        return 1
    
    # Simple chat interaction
    print("Sending message to LLM...")
    print()
    
    message = "Explain quantum computing in simple terms."
    
    print(f"User: {message}")
    print()
    
    response = client.chat(
        message=message,
        system_prompt="You are a helpful AI assistant.",
        temperature=0.7,
        max_tokens=256
    )
    
    print(f"Assistant: {response}")
    print()
    print("=" * 50)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
