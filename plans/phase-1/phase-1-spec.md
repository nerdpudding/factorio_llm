# Phase 1: Core Tools Library

## Goal
Build Python tools that reliably query Factorio game state via RCON.

## Deliverables

### src/rcon_wrapper.py
- [x] `connect()` / `disconnect()`
- [x] `execute_lua(cmd)` - run command, returns raw string or None
- [x] `query_lua(cmd)` - returns parsed result (wraps in rcon.print + serpent)
- [x] Error handling (connection lost, invalid command)

### src/factorio_tools.py
- [x] `get_tick()` - current game tick
- [x] `get_game_info()` - version, surface name, tick, etc.
- [x] `count_entities(entity_type)` - count entities of type
- [x] `list_entities(entity_type, limit=10)` - positions of entities
- [x] `get_production_stats(item)` - production count for item

### tests/test_tools.py
- [x] Tests for each tool
- [x] Requires running Factorio server

## Success Criteria
- All tools return correct data from running game
- Error handling works (graceful failure on connection issues)
- Code is clean and documented

## Notes
- Keep it simple - no over-engineering
- Test with actual running server
- Document any API quirks discovered
