"""
Test Ollama client connection and simple chat.

Run with:
    conda activate factorio
    cd D:\factorio_llm
    python tests/test_ollama.py

Requires Ollama to be running!
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.llm_client import OllamaClient


def main():
    print("=" * 60)
    print("OLLAMA CLIENT TEST")
    print("=" * 60)

    # Load config
    config = Config.from_yaml()
    print(f"\nUsing model: {config.model}")
    print(f"Ollama URL: {config.ollama_url}")

    # Create client
    client = OllamaClient(config)

    # Test 1: Check availability
    print("\n[1/3] Checking Ollama availability...")
    if not client.is_available():
        print("[FAIL] Ollama is not reachable!")
        print("       Make sure Ollama is running (docker or native)")
        return 1
    print("[OK] Ollama is available")

    # Test 2: List models
    print("\n[2/3] Listing available models...")
    models = client.list_models()
    if models:
        print(f"[OK] Found {len(models)} models:")
        for m in models[:5]:
            marker = " <-- configured" if m == config.model else ""
            print(f"     - {m}{marker}")
        if len(models) > 5:
            print(f"     ... and {len(models) - 5} more")
    else:
        print("[WARN] No models found (or couldn't list)")

    # Check if configured model exists
    if config.model not in models:
        print(f"\n[WARN] Configured model '{config.model}' not found!")
        print("       You may need to pull it: ollama pull <model>")

    # Test 3: Simple chat (no tools)
    print("\n[3/3] Testing simple chat...")
    try:
        response = client.chat([
            {"role": "user", "content": "Say 'Hello Factorio!' and nothing else."}
        ])
        message = response.get("message", {})
        content = message.get("content", "")
        print(f"[OK] Response: {content[:100]}{'...' if len(content) > 100 else ''}")
    except ConnectionError as e:
        print(f"[FAIL] Connection error: {e}")
        return 1
    except RuntimeError as e:
        print(f"[FAIL] API error: {e}")
        return 1
    except Exception as e:
        print(f"[FAIL] Unexpected error: {type(e).__name__}: {e}")
        return 1

    print("\n" + "=" * 60)
    print("OLLAMA CLIENT TEST PASSED!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
