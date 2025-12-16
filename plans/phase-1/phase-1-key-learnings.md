# Phase 1 Key Learnings

## Critical: DOT vs COLON Syntax

**#1 cause of failed RCON commands!**

Lua has two syntax forms:
- **COLON (`:`)** - adds implicit `self` as first argument
- **DOT (`.`)** - no implicit arguments

**For RCON: ALWAYS use DOT syntax**

```lua
-- WRONG - colon adds 'self', breaks API call
game.forces["player"]:get_item_production_statistics(surface)

-- CORRECT - dot syntax for RCON
game.forces["player"].get_item_production_statistics(surface)
```

## API Documentation

Factorio Lua API docs location:
```
D:\factorio_llm\api_archive\files\runtime-api.json
```

### Common Mistakes

1. **Assuming API structure** - Always check if something is a property or method
2. **Parameter types** - Pass objects, not strings (e.g., `game.surfaces["nauvis"]` not `"nauvis"`)
3. **Entity types vs names** - Types are categories (`"tree"`), names are specific (`"iron-ore"`)

## Checklist for New API Calls

1. Look up the class in `runtime-api.json`
2. Check if it's a property or method
3. Check parameter and return types
4. Test with minimal example first
