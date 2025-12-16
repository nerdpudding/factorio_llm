"""
Simple test - only place a chest, don't remove it.
Run this and look in the game to see the chest appear!

    conda activate factorio
    cd D:\factorio_llm
    python tests/test_place_only.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.factorio_tools import FactorioTools


def main():
    print("=" * 60)
    print("TEST: Place chest only (no removal)")
    print("=" * 60)

    with FactorioTools() as tools:
        # Get player position
        pos = tools.get_player_position()
        print(f"\nPlayer position: x={pos.x:.1f}, y={pos.y:.1f}")

        # Place chest 3 tiles to the right
        target_x = pos.x + 3
        target_y = pos.y
        print(f"\nPlacing wooden-chest at: x={target_x:.1f}, y={target_y:.1f}")

        result = tools.place_entity("wooden-chest", target_x, target_y)

        if result:
            print("\n>>> SUCCESS! Chest placed! <<<")
            print(">>> KIJK IN DE GAME - je zou een chest moeten zien! <<<")
        else:
            print("\n>>> FAILED - kon chest niet plaatsen <<<")
            print(">>> Misschien is de plek geblokkeerd? <<<")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
