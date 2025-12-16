"""
Phase 2 Tools Test Script.

Run with Factorio open in Host Game mode:
    conda activate factorio
    cd D:\factorio_llm
    python tests/test_phase2.py

Tests all Phase 2 tools for LLM control.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.factorio_tools import FactorioTools


def main():
    print("=" * 60)
    print("PHASE 2 TOOLS TEST")
    print("=" * 60)

    with FactorioTools() as tools:
        # ---------------------------------------------------------------------
        # Player & Position
        # ---------------------------------------------------------------------
        print("\n[1/10] Testing get_player_position()...")
        try:
            pos = tools.get_player_position()
            print(f"OK: Player at x={pos.x:.1f}, y={pos.y:.1f}")
        except Exception as e:
            print(f"FAIL: {e}")

        print("\n[2/10] Testing find_nearby_resources()...")
        try:
            resources = tools.find_nearby_resources(radius=100)
            print(f"OK: Found {len(resources)} resource patches")
            for r in resources[:5]:
                print(f"    - {r.name}: {r.amount} at ({r.position_x:.0f}, {r.position_y:.0f})")
        except Exception as e:
            print(f"FAIL: {e}")

        # ---------------------------------------------------------------------
        # Inventory & Crafting
        # ---------------------------------------------------------------------
        print("\n[3/10] Testing get_player_inventory()...")
        try:
            inventory = tools.get_player_inventory()
            print(f"OK: {len(inventory)} item types in inventory")
            for item in inventory[:5]:
                print(f"    - {item.name}: {item.count}")
        except Exception as e:
            print(f"FAIL: {e}")

        print("\n[4/10] Testing get_entity_inventory()...")
        try:
            # Try at player position - might find a chest nearby
            pos = tools.get_player_position()
            inv = tools.get_entity_inventory(pos.x, pos.y)
            if inv:
                print(f"OK: Found entity inventory with {len(inv)} items")
            else:
                print("OK: No entity with inventory at player position (expected)")
        except Exception as e:
            print(f"FAIL: {e}")

        print("\n[5/10] Testing craft_item()...")
        try:
            # Try to craft 1 wooden chest (needs wood)
            result = tools.craft_item("wooden-chest", 1)
            if result:
                print("OK: Crafting started")
            else:
                print("OK: Couldn't craft (missing materials or no recipe - expected)")
        except Exception as e:
            print(f"FAIL: {e}")

        # ---------------------------------------------------------------------
        # Entity Actions
        # ---------------------------------------------------------------------
        print("\n[6/10] Testing place_entity()...")
        try:
            pos = tools.get_player_position()
            # Try to place a wooden chest 3 tiles to the right
            result = tools.place_entity("wooden-chest", pos.x + 3, pos.y)
            if result:
                print(f"OK: Placed wooden-chest at ({pos.x + 3:.1f}, {pos.y:.1f})")
            else:
                print("OK: Couldn't place (blocked or out of range - expected)")
        except Exception as e:
            print(f"FAIL: {e}")

        print("\n[7/10] Testing remove_entity()...")
        try:
            pos = tools.get_player_position()
            # Try to remove the chest we just placed
            result = tools.remove_entity(pos.x + 3, pos.y)
            if result:
                print("OK: Removed entity")
            else:
                print("OK: No entity to remove (expected if placement failed)")
        except Exception as e:
            print(f"FAIL: {e}")

        # ---------------------------------------------------------------------
        # Factory Analysis
        # ---------------------------------------------------------------------
        print("\n[8/10] Testing get_assemblers()...")
        try:
            assemblers = tools.get_assemblers(limit=10)
            print(f"OK: Found {len(assemblers)} assembling machines")
            for a in assemblers[:3]:
                recipe = a['recipe'] or 'none'
                print(f"    - {a['name']} making {recipe} at ({a['x']:.0f}, {a['y']:.0f})")
        except Exception as e:
            print(f"FAIL: {e}")

        print("\n[9/10] Testing get_power_stats()...")
        try:
            power = tools.get_power_stats()
            print(f"OK: Power stats:")
            print(f"    Production: {power['production_mw']:.2f} MW")
            print(f"    Consumption: {power['consumption_mw']:.2f} MW")
            print(f"    Satisfaction: {power['satisfaction']:.0%}")
        except Exception as e:
            print(f"FAIL: {e}")

        print("\n[10/10] Testing get_research_status()...")
        try:
            research = tools.get_research_status()
            current = research['current_research'] or 'none'
            print(f"OK: Research status:")
            print(f"    Current: {current}")
            print(f"    Progress: {research['progress']:.0%}")
            if research['research_queue']:
                print(f"    Queue: {', '.join(research['research_queue'])}")
        except Exception as e:
            print(f"FAIL: {e}")

    print("\n" + "=" * 60)
    print("PHASE 2 TESTS COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
