#!/usr/bin/env python3
"""
Interactive Chat Interface

Author: Patrick Cooper

Provides an interactive command-line chat interface for CURC-hosted LLM.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.client.curc_llm_client import CURCLLMClient


def main():
    """Run interactive chat interface."""
    
    # Create client
    client = CURCLLMClient(base_url="http://localhost:8000")
    
    print("CURC LLM Interactive Chat")
    print("=" * 50)
    print()
    
    # Check server health
    try:
        health = client.health_check()
        print(f"Server Status: {health}")
    except Exception as e:
        print(f"ERROR: Could not connect to server: {e}")
        print()
        print("Make sure:")
        print("  1. vLLM server is running on CURC")
        print("  2. SSH tunnel is active: ./scripts/create_tunnel.sh <JOB_ID>")
        return 1
    
    # Get available models
    try:
        models = client.get_models()
        print(f"Available models: {len(models)}")
        for model in models:
            print(f"  - {model.get('id', 'unknown')}")
    except Exception as e:
        print(f"Could not fetch models: {e}")
    
    print()
    print("Commands:")
    print("  /quit or /exit - Exit the chat")
    print("  /clear - Clear conversation history")
    print("  /help - Show this help message")
    print()
    print("=" * 50)
    print()
    
    # Conversation history
    conversation = []
    system_prompt = "You are a helpful AI assistant."
    
    # Resolve model name once up front
    model_name = client._get_default_model()

    # Chat loop
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith('/'):
                command = user_input.lower()
                
                if command in ['/quit', '/exit']:
                    print("Goodbye!")
                    break
                
                elif command == '/clear':
                    conversation = []
                    print("Conversation cleared.")
                    continue
                
                elif command == '/help':
                    print()
                    print("Commands:")
                    print("  /quit or /exit - Exit the chat")
                    print("  /clear - Clear conversation history")
                    print("  /help - Show this help message")
                    print()
                    continue
                
                else:
                    print(f"Unknown command: {command}")
                    continue
            
            # Add to conversation history
            conversation.append({"role": "user", "content": user_input})
            
            # Get response
            print("Assistant: ", end="", flush=True)
            
            # Build messages with history
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation)
            
            # Stream response
            full_response = ""
            stream = client.openai_client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=512,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_response += content
            
            print()  # Newline after response
            print()
            
            # Add assistant response to history
            conversation.append({"role": "assistant", "content": full_response})
            
        except KeyboardInterrupt:
            print()
            print()
            print("Interrupted. Type /quit to exit.")
            print()
            continue
        
        except Exception as e:
            print()
            print(f"Error: {e}")
            print()
            continue
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
