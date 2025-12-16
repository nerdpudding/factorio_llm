# Phase 2: Action Tools for LLM Control

## Goal
Build action tools that let an LLM actually PLAY Factorio - not just read data, but interact with the game. These become function calls for Ollama.

## Deliverables

### src/factorio_tools.py - New Methods

#### Player & Position
- [x] `get_player_position()` - where is the player standing?
- [x] `find_nearby_resources(radius=50)` - ore patches near player

#### Inventory & Crafting
- [x] `get_player_inventory()` - player's inventory contents
- [x] `get_entity_inventory(x, y)` - chest/machine contents at position
- [x] `craft_item(name, count)` - manual crafting

#### Entity Actions
- [x] `place_entity(name, x, y)` - place entity at position
- [x] `remove_entity(x, y)` - remove entity at position

#### Factory Analysis
- [x] `get_assemblers()` - list all assembling machines with recipes
- [x] `get_power_stats()` - electricity production/consumption
- [x] `get_research_status()` - current research progress

### tests/test_phase2.py
- [x] Test script for manual testing with running Factorio
- [x] Each tool testable individually

## Success Criteria
- All tools work with running Factorio (Host Game mode)
- Entity placement works within ~10 tiles of player
- Collision detection prevents invalid placements
- Clear error messages for LLM to understand failures

## Technical Notes

### CRITICAL: Lua Syntax
**ALWAYS use DOT syntax (`.`) for Factorio API calls, NEVER colon (`:`)!**
Colon passes `self` as implicit first argument which breaks API calls.

### Entity Placement
- Use `surface.can_place_entity()` BEFORE `create_entity()`
- Placement radius: ~10 tiles around player (Factorio default)
- NO auto-clearing trees/rocks - too dangerous for now
- Requires `force="player"` parameter

### Inventory Access
- Player inventory: `game.connected_players[1].get_main_inventory()`
- Inventory returns Lua table - use `serpent.line()` to serialize

## Test Approach
Real game testing only - no unit tests, no mocking:
1. Start Factorio via Steam → Multiplayer → Host Game
2. Run Python test script in conda environment
3. Verify result in game OR Python output
