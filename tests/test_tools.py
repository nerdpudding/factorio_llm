"""
Tests for Factorio tools.

Run directly (no dependencies needed):
    python tests/test_tools.py

Or with pytest (optional):
    pip install pytest
    pytest tests/test_tools.py -v
"""

import sys
import os

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.rcon_wrapper import RCONWrapper, ConnectionError, CommandError
from src.factorio_tools import FactorioTools, GameInfo, ProductionStats


def test_all():
    """Run all tests - no pytest needed."""

    print("=" * 50)
    print("FACTORIO TOOLS TEST")
    print("=" * 50)
    print()

    # Test 1: Connection
    print("[1/6] Testing connection...")
    tools = FactorioTools()
    tools.connect()

    if not tools.connected:
        print("FAILED: Could not connect")
        return False
    print("OK: Connected to server")
    print()

    # Test 2: Get tick
    print("[2/6] Testing get_tick()...")
    tick = tools.get_tick()
    print(f"OK: Game tick = {tick}")
    print()

    # Test 3: Get game info
    print("[3/6] Testing get_game_info()...")
    info = tools.get_game_info()
    print(f"OK: Version = {info.version}")
    print(f"    Surface = {info.surface_name}")
    print(f"    Tick = {info.tick}")
    print(f"    Players = {info.player_count}")
    print()

    # Test 4: Count entities
    print("[4/6] Testing count_entities('tree')...")
    trees = tools.count_entities("tree")
    print(f"OK: Found {trees} trees")
    print()

    # Test 5: List entities by name (iron-ore)
    print("[5/6] Testing count_entities_by_name('iron-ore')...")
    iron_ore = tools.count_entities_by_name("iron-ore")
    print(f"OK: Found {iron_ore} iron ore patches")
    print()

    # Test 6: Production stats
    print("[6/6] Testing get_production_stats('iron-plate')...")
    stats = tools.get_production_stats("iron-plate")
    print(f"OK: Iron plates - produced: {stats.output_count}, consumed: {stats.input_count}")
    print()

    # Cleanup
    tools.disconnect()

    print("=" * 50)
    print("ALL TESTS PASSED!")
    print("=" * 50)
    return True


if __name__ == "__main__":
    try:
        success = test_all()
        sys.exit(0 if success else 1)

    except ConnectionError as e:
        print()
        print("ERROR: Could not connect to Factorio server!")
        print(f"Details: {e}")
        print()
        print("Make sure the server is running. In another terminal:")
        print()
        print('  cd /d "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Factorio\\bin\\x64"')
        print('  factorio.exe --start-server rcon-test.zip --rcon-port 27015 --rcon-password test123')
        print()
        sys.exit(1)

    except Exception as e:
        print()
        print(f"ERROR: {type(e).__name__}: {e}")
        sys.exit(1)
