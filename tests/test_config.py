"""
Test config loading.

Run with:
    conda activate factorio
    cd D:\factorio_llm
    python tests/test_config.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config


def main():
    print("=" * 60)
    print("CONFIG LOADING TEST")
    print("=" * 60)

    try:
        config = Config.from_yaml()
        print("\nConfig loaded successfully!")
        print(f"\n{config}")
        print(f"\nAll values:")
        print(f"  ollama_url: {config.ollama_url}")
        print(f"  model: {config.model}")
        print(f"  temperature: {config.temperature}")
        print(f"  num_ctx: {config.num_ctx}")
        print(f"  num_predict: {config.num_predict}")
        print(f"  max_tool_iterations: {config.max_tool_iterations}")
        print(f"  rcon_host: {config.rcon_host}")
        print(f"  rcon_port: {config.rcon_port}")
        print(f"  rcon_password: {'*' * len(config.rcon_password)}")
        print("\n[OK] Config test passed!")
    except Exception as e:
        print(f"\n[FAIL] {type(e).__name__}: {e}")
        return 1

    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
