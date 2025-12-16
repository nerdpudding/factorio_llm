"""
Factorio Agent - connects LLM to Factorio tools.

Handles the conversation loop with tool calling.
"""

import json
from dataclasses import asdict
from typing import Any

# Try to import colorama for colored debug output
try:
    from colorama import Fore, Style
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False


def _yellow(text: str) -> str:
    return f"{Fore.YELLOW}{text}{Style.RESET_ALL}" if COLORS_AVAILABLE else text


def _dim(text: str) -> str:
    return f"{Style.DIM}{text}{Style.RESET_ALL}" if COLORS_AVAILABLE else text


def _red(text: str) -> str:
    return f"{Fore.RED}{text}{Style.RESET_ALL}" if COLORS_AVAILABLE else text


from .config import Config
from .llm_client import OllamaClient
from .factorio_tools import FactorioTools
from .tool_definitions import FACTORIO_TOOLS


SYSTEM_PROMPT = """You are a Factorio assistant. You MUST use tools to interact with the game - never print tool names as text.

## Current Game State
Each message includes [GAME STATE: x=... y=... tick=...] with the player's CURRENT position.
- For simple questions like "where am I?" → use this injected position directly, no tool call needed!
- For relative placement ("next to me", "to my right") → use the injected x,y coordinates
- Only call get_player_position() if you need to verify position mid-conversation

## Available Tools

**Information:**
- get_player_position() - Get x,y coordinates (usually not needed - use injected state!)
- get_player_inventory() - List items you're carrying
- get_game_info() - Game tick, version, player count
- get_tick() - Current game tick only

**Scanning nearby:**
- find_nearby_entities(radius=20) - Find buildings, chests, machines, belts near you
- find_nearby_resources(radius=50) - Find ore patches (iron, copper, coal, stone)
- count_entities(entity_type) - Count specific entity on entire map

**Actions:**
- place_entity(name, x, y) - Place a building (must have item in inventory)
- remove_entity(x, y) - Remove/destroy entity at position
- craft_item(item_name, count=1) - Hand-craft items
- mine_resource(count=10, resource_type="coal") - Mine specific ore within 30 tiles. Use count=-1 for entire field

**Entity inspection:**
- get_entity_inventory(x, y) - Check contents of chest/machine at position

**Factory status:**
- get_assemblers(limit=20) - List assembling machines and their recipes
- get_power_stats() - Electricity production/consumption
- get_research_status() - Current research progress
- get_production_stats(item) - How many items produced/consumed

## Coordinates
- Positive X = east/right, Negative X = west/left
- Positive Y = south/down, Negative Y = north/up
- "to my right" = x + 1, "to my left" = x - 1
- "above me" / "north" = y - 1, "below me" / "south" = y + 1
- WARNING: We CANNOT detect which way the player is facing! "behind me" or "in front of me" is ambiguous.
  Ask the user to clarify using north/south/east/west or left/right instead.

## Rules
- Use the injected [GAME STATE] for current position - it's always fresh!
- If user says "behind me" or "in front", ask them to use north/south/east/west
- Keep responses short and helpful
"""


class FactorioAgent:
    """Agent that connects LLM to Factorio tools."""

    def __init__(
        self,
        config: Config,
        llm_client: OllamaClient,
        tools: FactorioTools,
    ):
        """
        Initialize agent with dependencies.

        Args:
            config: Configuration object
            llm_client: Ollama client for LLM calls
            tools: Connected FactorioTools instance
        """
        self.config = config
        self.llm = llm_client
        self.tools = tools
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.debug = False

    def clear_history(self):
        """Clear conversation history, keeping only the system prompt."""
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def _get_game_state(self) -> str:
        """
        Get current game state via RCON (cheap, no LLM call).

        Returns state string like: [GAME STATE: x=5.8 y=-12.3 tick=54321]
        """
        try:
            pos = self.tools.get_player_position()
            tick = self.tools.get_tick()
            return f"[GAME STATE: x={pos.x:.1f} y={pos.y:.1f} tick={tick}]"
        except Exception as e:
            if self.debug:
                print(_red(f"  [WARN] Could not get game state: {e}"))
            return "[GAME STATE: unavailable]"

    def _parse_text_tool_call(self, content: str) -> dict | None:
        """
        Parse tool calls that the model printed as text instead of proper calls.

        Handles formats like:
        - function_name[ARGS]{"arg": "value"}
        - function_name[ARGS]{}

        Returns:
            Tool call dict or None if not parseable.
        """
        import re
        # Pattern: function_name[ARGS]{json}
        match = re.search(r'(\w+)\[ARGS\](\{[^}]*\})', content)
        if match:
            func_name = match.group(1)
            args_str = match.group(2)
            try:
                args = json.loads(args_str)
                return {
                    "function": {
                        "name": func_name,
                        "arguments": args
                    }
                }
            except json.JSONDecodeError:
                pass
        return None

    def _trim_history(self):
        """Trim conversation history to stay within configured limit."""
        max_msgs = self.config.max_history_messages
        current_count = len(self.messages) - 1  # Exclude system prompt

        if self.debug:
            print(_dim(f"  [HISTORY] {current_count}/{max_msgs} messages"))

        if current_count <= max_msgs:
            return

        # Calculate how many to remove
        to_remove = current_count - max_msgs

        # Keep system prompt (index 0) + most recent messages
        self.messages = [self.messages[0]] + self.messages[-(max_msgs):]

        if self.debug:
            print(_dim(f"  [HISTORY] Trimmed: removed {to_remove} oldest messages"))

    def chat(self, user_message: str) -> str:
        """
        Handle a user message with tool calling loop.

        Args:
            user_message: The user's question or command

        Returns:
            The assistant's final response
        """
        # Get current game state (cheap RCON call, always fresh)
        game_state = self._get_game_state()
        if self.debug:
            print(_dim(f"  [STATE] {game_state}"))

        # Add user message with injected game state
        enriched_message = f"{game_state}\n{user_message}"
        self.messages.append({"role": "user", "content": enriched_message})

        for iteration in range(self.config.max_tool_iterations):
            # Call LLM
            response = self.llm.chat(self.messages, tools=FACTORIO_TOOLS, debug=self.debug)
            message = response.get("message", {})

            # Check for tool calls
            tool_calls = message.get("tool_calls") or []

            # Fallback: detect tool calls printed as text (e.g., "func_name[ARGS]{...}")
            # Check ALWAYS, not just when tool_calls is empty - model may do both!
            content = message.get("content", "")
            parsed = self._parse_text_tool_call(content)
            if parsed:
                tool_calls = list(tool_calls) + [parsed]  # Add to existing calls
                # Update message with merged tool_calls and clear the text
                message = {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": tool_calls
                }
                if self.debug:
                    print(_yellow(f"  [FALLBACK] Parsed text as tool call: {parsed['function']['name']}"))

            if not tool_calls:
                # No tool calls - add response to history and return
                content = message.get("content", "")

                # Handle empty responses gracefully (6.8)
                if not content or not content.strip():
                    if self.debug:
                        print(_red("  [WARN] LLM returned empty response"))
                    content = "I didn't generate a response. Could you rephrase your question?"

                self.messages.append({"role": "assistant", "content": content})
                self._trim_history()
                return content

            # Process each tool call
            # Add assistant message with tool calls to history
            self.messages.append(message)

            for tool_call in tool_calls:
                tool_name = tool_call.get("function", {}).get("name", "")
                tool_args = tool_call.get("function", {}).get("arguments", {})

                # Execute the tool
                result = self._execute_tool(tool_name, tool_args)

                # Add tool result to messages
                self.messages.append({
                    "role": "tool",
                    "content": result,
                })

        # Max iterations reached
        fallback = "I've made several tool calls but couldn't complete the task. Please try a simpler request."
        self.messages.append({"role": "assistant", "content": fallback})
        self._trim_history()
        return fallback

    def _execute_tool(self, name: str, args: dict) -> str:
        """
        Execute a Factorio tool and return result as string.

        Args:
            name: Tool name
            args: Tool arguments

        Returns:
            String representation of the result
        """
        if self.debug:
            print(_yellow(f"  [TOOL] {name}({args})"))

        try:
            result = self._call_tool(name, args)
            formatted = self._format_result(result)

            if self.debug:
                display = formatted[:150] + "..." if len(formatted) > 150 else formatted
                print(_dim(f"  [RESULT] {display}"))

            return formatted
        except Exception as e:
            error_msg = f"Error: {type(e).__name__}: {e}"
            if self.debug:
                print(_red(f"  [ERROR] {error_msg}"))
            return error_msg

    def _call_tool(self, name: str, args: dict) -> Any:
        """Call the actual tool method."""
        # Phase 1 tools
        if name == "get_tick":
            return self.tools.get_tick()
        elif name == "get_game_info":
            return self.tools.get_game_info()
        elif name == "count_entities":
            return self.tools.count_entities(args.get("entity_type", "tree"))
        elif name == "get_production_stats":
            return self.tools.get_production_stats(args.get("item", "iron-plate"))

        # Phase 2: Player & Position
        elif name == "get_player_position":
            return self.tools.get_player_position()
        elif name == "find_nearby_entities":
            return self.tools.find_nearby_entities(radius=args.get("radius", 20))
        elif name == "find_nearby_resources":
            return self.tools.find_nearby_resources(radius=args.get("radius", 50))

        # Phase 2: Inventory & Crafting
        elif name == "get_player_inventory":
            return self.tools.get_player_inventory()
        elif name == "get_entity_inventory":
            return self.tools.get_entity_inventory(args["x"], args["y"])
        elif name == "craft_item":
            return self.tools.craft_item(args["item_name"], args.get("count", 1))
        elif name == "mine_resource":
            return self.tools.mine_resource(
                count=args.get("count", 10),
                resource_type=args.get("resource_type")
            )

        # Phase 2: Entity Actions
        elif name == "place_entity":
            return self.tools.place_entity(args["name"], args["x"], args["y"])
        elif name == "remove_entity":
            return self.tools.remove_entity(args["x"], args["y"])

        # Phase 2: Factory Analysis
        elif name == "get_assemblers":
            return self.tools.get_assemblers(limit=args.get("limit", 20))
        elif name == "get_power_stats":
            return self.tools.get_power_stats()
        elif name == "get_research_status":
            return self.tools.get_research_status()

        else:
            raise ValueError(f"Unknown tool: {name}")

    def _format_result(self, result: Any) -> str:
        """Format a tool result as a string for the LLM."""
        if result is None:
            return "No result"
        elif isinstance(result, bool):
            return "Success" if result else "Failed"
        elif isinstance(result, (int, float, str)):
            return str(result)
        elif isinstance(result, list):
            if not result:
                return "Empty list"
            # Format list items
            items = []
            for item in result:
                if hasattr(item, "__dataclass_fields__"):
                    items.append(json.dumps(asdict(item)))
                elif isinstance(item, dict):
                    items.append(json.dumps(item))
                else:
                    items.append(str(item))
            return f"[{', '.join(items)}]"
        elif isinstance(result, dict):
            return json.dumps(result)
        elif hasattr(result, "__dataclass_fields__"):
            return json.dumps(asdict(result))
        else:
            return str(result)
