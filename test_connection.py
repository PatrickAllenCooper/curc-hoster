#!/usr/bin/env python3
"""
Quick connection test for CURC vLLM server
Author: Patrick Cooper

Run this after:
1. Your CURC job is running
2. SSH tunnel is established

Usage:
    python test_connection.py
"""

import httpx
import sys

def test_connection(base_url="http://localhost:8000"):
    """Test connection to vLLM server"""
    
    print("=" * 60)
    print("CURC vLLM Connection Test")
    print("=" * 60)
    print(f"\nTesting connection to: {base_url}")
    
    try:
        # Test health endpoint (vLLM returns 200 with empty body)
        print("\n1. Testing health endpoint...")
        response = httpx.get(f"{base_url}/health", timeout=5.0)
        response.raise_for_status()
        body = response.text.strip()
        print(f"   ✓ Health check: HTTP {response.status_code} {body or '(ok)'}")
        
        # Test models endpoint
        print("\n2. Testing models endpoint...")
        response = httpx.get(f"{base_url}/v1/models", timeout=5.0)
        response.raise_for_status()
        models = response.json()
        print(f"   ✓ Available models: {len(models.get('data', []))}")
        for model in models.get('data', []):
            print(f"     - {model.get('id', 'unknown')}")
        
        print("\n" + "=" * 60)
        print("SUCCESS! Server is ready to use.")
        print("=" * 60)
        print("\nNext steps:")
        print("  python examples/basic_chat.py")
        print("  python examples/interactive_chat.py")
        return True
        
    except httpx.ConnectError:
        print("\n✗ Connection failed!")
        print("\nPossible issues:")
        print("  1. SSH tunnel not established")
        print("  2. CURC job not running yet")
        print("  3. Wrong port number")
        print("\nTo check:")
        print("  - Is your SSH tunnel running?")
        print("  - Check CURC job status: squeue -u $USER")
        return False
        
    except httpx.TimeoutException:
        print("\n✗ Connection timeout!")
        print("\nServer might be starting up. Wait 30 seconds and try again.")
        return False
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
