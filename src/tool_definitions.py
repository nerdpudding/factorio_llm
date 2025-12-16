"""
Tool definitions for Ollama function calling.

Defines Factorio tools as JSON schema for the LLM.
Tools are organized by phase: Phase 1 (basic queries), Phase 2 (player actions).
"""

FACTORIO_TOOLS = [
    # =========================================================================
    # Phase 1: Basic Queries
    # =========================================================================
    {
        "type": "function",
        "function": {
            "name": "get_tick",
            "description": "Get the current game tick (time unit in Factorio). 60 ticks = 1 second. NOTE: Tick is auto-injected in [GAME STATE], so this tool is rarely needed.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_game_info",
            "description": "Get basic game information including tick, surface name, player count, and Factorio version.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "count_entities",
            "description": "Count entities of a specific type on the map. Use entity types like 'tree', 'iron-ore', 'copper-ore', 'coal', 'stone', 'assembling-machine', 'transport-belt', etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_type": {
                        "type": "string",
                        "description": "The entity type to count (e.g., 'tree', 'iron-ore', 'assembling-machine')"
                    }
                },
                "required": ["entity_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_production_stats",
            "description": "Get production statistics for a specific item. Shows how many have been produced (input) and consumed (output).",
            "parameters": {
                "type": "object",
                "properties": {
                    "item": {
                        "type": "string",
                        "description": "The item name (e.g., 'iron-plate', 'copper-plate', 'iron-gear-wheel')"
                    }
                },
                "required": ["item"]
            }
        }
    },

    # =========================================================================
    # Phase 2: Player & Position
    # =========================================================================
    {
        "type": "function",
        "function": {
            "name": "get_player_position",
            "description": "Get the player's current x,y position. NOTE: Position is auto-injected in [GAME STATE] at start of each message, so this tool is rarely needed. Use injected coordinates directly for placement.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_nearby_entities",
            "description": "Find ALL entities near the player: buildings, chests, machines, belts, inserters, poles, etc. Does NOT include resources/ores or trees. Use this to scan what's around you.",
            "parameters": {
                "type": "object",
                "properties": {
                    "radius": {
                        "type": "number",
                        "description": "Search radius in tiles around the player (default: 20)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_nearby_resources",
            "description": "Find ore patches near player. Returns TOTAL amount per resource type (summed across all tiles), plus tile count and center position. Example: coal with total_amount=50000 means 50k ore available.",
            "parameters": {
                "type": "object",
                "properties": {
                    "radius": {
                        "type": "number",
                        "description": "Search radius in tiles around the player (default: 50)"
                    }
                },
                "required": []
            }
        }
    },

    # =========================================================================
    # Phase 2: Inventory & Crafting
    # =========================================================================
    {
        "type": "function",
        "function": {
            "name": "get_player_inventory",
            "description": "Get all items in the player's main inventory with their counts.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_entity_inventory",
            "description": "Get the inventory contents of an entity (chest, machine) at a specific position.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {
                        "type": "number",
                        "description": "X coordinate of the entity"
                    },
                    "y": {
                        "type": "number",
                        "description": "Y coordinate of the entity"
                    }
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "craft_item",
            "description": "Craft items by hand (manual crafting). Player must have required materials. Returns true if crafting started.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {
                        "type": "string",
                        "description": "Name of item to craft (e.g., 'iron-gear-wheel', 'electronic-circuit', 'transport-belt')"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of items to craft (default: 1)"
                    }
                },
                "required": ["item_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mine_resource",
            "description": "Mine resources near player (30 tile radius). Instantly mines ore and adds to inventory. Specify resource_type to mine a specific ore (coal, iron-ore, copper-ore, stone, uranium-ore).",
            "parameters": {
                "type": "object",
                "properties": {
                    "count": {
                        "type": "integer",
                        "description": "Number of ore to mine (default: 10). Use -1 to mine the ENTIRE field at once."
                    },
                    "resource_type": {
                        "type": "string",
                        "description": "Specific resource to mine: coal, iron-ore, copper-ore, stone, uranium-ore. If omitted, mines first resource found."
                    }
                },
                "required": []
            }
        }
    },

    # =========================================================================
    # Phase 2: Entity Actions
    # =========================================================================
    {
        "type": "function",
        "function": {
            "name": "place_entity",
            "description": "Place a building/entity at a position. Must be within ~10 tiles of player. Fails if position is blocked. Player needs the item in inventory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Entity name (e.g., 'wooden-chest', 'iron-chest', 'transport-belt', 'assembling-machine-1', 'inserter')"
                    },
                    "x": {
                        "type": "number",
                        "description": "X coordinate to place at"
                    },
                    "y": {
                        "type": "number",
                        "description": "Y coordinate to place at"
                    }
                },
                "required": ["name", "x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remove_entity",
            "description": "Remove/destroy an entity at a position. Does not return items to inventory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {
                        "type": "number",
                        "description": "X coordinate of the entity"
                    },
                    "y": {
                        "type": "number",
                        "description": "Y coordinate of the entity"
                    }
                },
                "required": ["x", "y"]
            }
        }
    },

    # =========================================================================
    # Phase 2: Factory Analysis
    # =========================================================================
    {
        "type": "function",
        "function": {
            "name": "get_assemblers",
            "description": "Get list of assembling machines and their current recipes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of assemblers to return (default: 20)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_power_stats",
            "description": "Get electricity production and consumption statistics in MW. Also shows satisfaction (1.0 = 100% power satisfied).",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_research_status",
            "description": "Get current research progress, including current technology being researched and progress percentage.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
]


def get_tool_names() -> list[str]:
    """Get list of all tool names."""
    return [t["function"]["name"] for t in FACTORIO_TOOLS]


def get_tool_by_name(name: str) -> dict | None:
    """Get a tool definition by name."""
    for tool in FACTORIO_TOOLS:
        if tool["function"]["name"] == name:
            return tool
    return None
