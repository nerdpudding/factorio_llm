"""
Phase 3 Integration Test - LLM + Factorio.

Run with Factorio AND Ollama running:
    conda activate factorio
    cd D:\factorio_llm
    python tests/test_phase3.py

Tests the full flow: User -> LLM -> Tool -> Factorio -> LLM -> Response
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.llm_client import OllamaClient
from src.factorio_tools import FactorioTools
from src.factorio_agent import FactorioAgent


class DebugAgent(FactorioAgent):
    """Agent with debug output for tool calls."""

    def _execute_tool(self, name: str, args: dict) -> str:
        """Execute tool with debug output."""
        print(f"  [TOOL] {name}({args})")
        result = super()._execute_tool(name, args)
        # Truncate long results
        display = result[:150] + "..." if len(result) > 150 else result
        print(f"  [RESULT] {display}")
        return result


def main():
    print("=" * 60)
    print("PHASE 3 INTEGRATION TEST")
    print("=" * 60)

    # Load config
    config = Config.from_yaml()
    print(f"\nUsing model: {config.model}")

    # Check Ollama
    print("\n[1/4] Checking Ollama...")
    llm = OllamaClient(config)
    if not llm.is_available():
        print("[FAIL] Ollama not available!")
        return 1
    print("[OK] Ollama ready")

    # Connect to Factorio
    print("\n[2/4] Connecting to Factorio...")
    try:
        tools = FactorioTools(
            host=config.rcon_host,
            port=config.rcon_port,
            password=config.rcon_password,
        )
        tools.connect()
        tick = tools.get_tick()
        print(f"[OK] Factorio connected (tick: {tick})")
    except Exception as e:
        print(f"[FAIL] Cannot connect to Factorio: {e}")
        print("       Make sure Factorio is running in Host Game mode")
        return 1

    # Create agent with debug output
    agent = DebugAgent(config, llm, tools)

    # Test queries
    print("\n[3/4] Testing queries...")
    print("-" * 40)

    queries = [
        "What is the current game tick?",
        "Where am I standing?",
        "What resources are near me?",
    ]

    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}: {query}")
        try:
            response = agent.chat(query)
            # Truncate long responses
            if len(response) > 200:
                response = response[:200] + "..."
            print(f"Response: {response}")
        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e}")

    # Test action (optional - only if user wants to see it)
    print("\n[4/4] Testing action...")
    print("-" * 40)

    # First get player position directly
    pos = tools.get_player_position()
    print(f"\nPlayer position: x={pos.x:.1f}, y={pos.y:.1f}")
    print(f"Expected chest position: x={pos.x + 3:.1f}, y={pos.y:.1f}")

    print("\nQuery: Place a wooden chest 3 tiles to my right")
    try:
        response = agent.chat("Place a wooden chest 3 tiles to my right")
        print(f"Response: {response}")
        print("\n>>> Check in game if the chest appeared! <<<")
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")

    # Cleanup
    tools.disconnect()

    print("\n" + "=" * 60)
    print("PHASE 3 TEST COMPLETE!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
