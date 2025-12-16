# Phase 3: Ollama LLM Integration

## Goal
Connect Factorio tools (14 total: 4 Phase 1 + 10 Phase 2) to a local LLM (Ollama) for natural language control of Factorio.

## Context

Ollama is already running in Docker:
- **Ollama API:** http://localhost:11434
- **Open WebUI:** http://localhost:3000 (optional, for testing)

### Available Models

| Model | Size | Notes |
|-------|------|-------|
| `devstral-small-2:24b-instruct-2512-q4_K_M` | 15 GB | Larger, smarter |
| `devstral-small-2:24b-instruct-2512-q8_0` | 25 GB | Same but higher precision |
| `ministral-3:14b-instruct-2512-q4_K_M` | 9 GB | Smaller, faster |
| `ministral-3:14b-instruct-2512-q8_0` | 15 GB | Same but higher precision |

### Tool Calling Format (Mistral)

Both models use Mistral format:
- Tools injected as: `[AVAILABLE_TOOLS]{{ $.Tools }}[/AVAILABLE_TOOLS]`
- Model responds with: `[TOOL_CALLS]FunctionName[ARGS]{"arg": "value"}[/TOOL_CALLS]`
- Results back as: `[TOOL_RESULTS]result[/TOOL_RESULTS]`

**Note:** Ollama's `/api/chat` endpoint handles this format automatically. No manual tag parsing needed - just use the `tools` parameter in the API call.

**Temperature is already set to 0.15 in modelfiles** - optimal for tool calling.

---

## Design Decisions

| Question | Decision | Rationale |
|----------|----------|-----------|
| Streaming? | No for v1 | Tool calling + streaming is complex. Local model has low latency anyway. |
| Conversation history? | No limit for v1 | 32k context is enough for normal sessions. |
| Max iterations? | Yes, max 5 | Prevents infinite loops. |

---

## Architecture Principles

**SOLID + KISS:**

- **Single Responsibility:** `OllamaClient` only talks to Ollama. `FactorioAgent` only orchestrates.
- **Open/Closed:** Tools as separate definitions, easy to add new ones.
- **Dependency Injection:** Config, clients, tools as parameters - not hardcoded.
- **Config class:** One object that loads everything, no scattered yaml reads.

```python
# Good - dependencies injected
class FactorioAgent:
    def __init__(self, llm_client: OllamaClient, tools: FactorioTools, config: Config):
        ...
```

Flexible for later: sliding window, other LLM backends, more tools.

---

## Deliverables

### 1. config.yaml - Central Configuration

```yaml
# Ollama settings
ollama_url: http://localhost:11434
model: devstral-small-2:24b-instruct-2512-q4_K_M

# Model parameters
temperature: 0.15
num_ctx: 32768
num_predict: 1024

# Agent settings
max_tool_iterations: 5  # Prevents infinite loops

# Factorio RCON (existing)
rcon_host: localhost
rcon_port: 27015
rcon_password: test123
```

**Requirement:** Switching models must be EASY - config change only, no code changes.

### 2. src/config.py - Config Class

```python
@dataclass
class Config:
    """Central configuration loaded from YAML."""

    # Ollama
    ollama_url: str
    model: str
    temperature: float
    num_ctx: int
    num_predict: int

    # Agent
    max_tool_iterations: int

    # RCON
    rcon_host: str
    rcon_port: int
    rcon_password: str

    @classmethod
    def from_yaml(cls, path: str = "config.yaml") -> "Config":
        """Load config from YAML file."""
```

### 3. src/llm_client.py - Ollama Wrapper

```python
class OllamaClient:
    def __init__(self, config: Config):
        """Initialize with config."""

    def chat(self, messages: list[dict], tools: list[dict] = None) -> dict:
        """
        Send chat request to Ollama.

        Args:
            messages: List of {role, content} dicts
            tools: Optional list of tool definitions

        Returns:
            Response dict with 'message' and optional 'tool_calls'
        """
```

Features:
- [x] Uses Config object (not direct yaml reads)
- [x] Configurable model (switch via config)
- [x] Configurable parameters (temperature, num_ctx, num_predict)
- [x] Tool calling via `/api/chat` endpoint
- [x] Error handling for connection issues

### 4. src/factorio_agent.py - LLM + Factorio Bridge

```python
class FactorioAgent:
    def __init__(self, config: Config, llm_client: OllamaClient, tools: FactorioTools):
        """Setup with injected dependencies."""

    def get_tool_definitions(self) -> list[dict]:
        """Return all 14 tools as Ollama tool definitions."""

    def execute_tool(self, name: str, args: dict) -> str:
        """Execute a Factorio tool and return result as string."""

    def chat(self, user_message: str) -> str:
        """
        Full conversation loop:
        1. Send user message + tools to LLM
        2. If LLM wants tool call -> execute -> send result back
        3. Repeat until LLM has final answer (max 5 iterations)
        4. Return final answer
        """
```

Features:
- [x] Registers all 14 tools as function definitions
- [x] Handles tool calls (parse, execute, return result)
- [x] Loop until LLM is done (max 5 iterations)
- [x] System prompt with Factorio context

### 5. tests/test_phase3.py - Test Script

```python
def main():
    config = Config.from_yaml()
    llm = OllamaClient(config)

    with FactorioTools() as tools:
        agent = FactorioAgent(config, llm, tools)

        # Test simple query
        print(agent.chat("How many trees are nearby?"))

        # Test action
        print(agent.chat("Place a wooden chest to my right"))

        # Test multi-step
        print(agent.chat("What resources do I have and can I craft an iron chest?"))
```

---

## Tool Definitions for Ollama

All tools must be defined as JSON schema:

```python
FACTORIO_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_player_position",
            "description": "Get the player's current x,y position in the game world",
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
            "name": "find_nearby_resources",
            "description": "Find ore patches (iron, copper, coal, stone) near the player",
            "parameters": {
                "type": "object",
                "properties": {
                    "radius": {
                        "type": "number",
                        "description": "Search radius in tiles (default 50)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "place_entity",
            "description": "Place a building or entity at the specified position. Must be within ~10 tiles of player.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Entity name (e.g., 'wooden-chest', 'transport-belt', 'assembling-machine-1')"
                    },
                    "x": {
                        "type": "number",
                        "description": "X coordinate"
                    },
                    "y": {
                        "type": "number",
                        "description": "Y coordinate"
                    }
                },
                "required": ["name", "x", "y"]
            }
        }
    }
    # ... etc for all 14 tools
]
```

---

## Example Flow

```
User: "How much iron ore is nearby?"

┌─────────────────────────────────────────────────────────────┐
│ Agent -> LLM                                                │
│ messages: [{role: "user", content: "How much iron ore..."}] │
│ tools: [all 14 tool definitions]                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ LLM -> Agent                                                │
│ tool_calls: [{                                              │
│   name: "find_nearby_resources",                            │
│   arguments: {"radius": 100}                                │
│ }]                                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Agent: Execute tool                                         │
│ result = tools.find_nearby_resources(radius=100)            │
│ -> [ResourcePatch(name="iron-ore", amount=45000, ...)]      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Agent -> LLM                                                │
│ messages: [                                                 │
│   {role: "user", content: "How much iron ore..."},          │
│   {role: "assistant", tool_calls: [...]},                   │
│   {role: "tool", content: "Found 3 patches: ..."}           │
│ ]                                                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ LLM -> User                                                 │
│ "There are 3 iron ore patches nearby with a total of        │
│  45,000 ore. The closest is at (50, -20)."                  │
└─────────────────────────────────────────────────────────────┘
```

---

## System Prompt

```
You are a Factorio assistant. You help the player by:
- Querying game state information
- Executing actions like placing or removing entities
- Giving advice on factory layout and efficiency

You have access to tools to interact with the game. Use these tools to answer questions and execute actions.

IMPORTANT - Position coordinates:
- Positive X = right/east, negative X = left/west
- Positive Y = down/south, negative Y = up/north
- "to my right" means: player_x + offset, player_y

Important limitations:
- You can only place entities within ~10 tiles of the player
- Placement fails if position is blocked (trees, rocks, water, other entities)
- For crafting, the player must have the required materials
```

---

## Success Criteria

- [x] `config.yaml` works - model switch without code changes
- [x] Simple query works: "How many trees are there?"
- [x] Action works: "Place a chest to my right"
- [x] Multi-tool works: LLM makes multiple tool calls if needed
- [x] Error handling: clear feedback on problems
- [x] Max 5 tool iterations enforced

---

## Implementation Plan

### Phase 3.1: Config Class
- [x] Create `src/config.py`
- [x] Create `config.yaml`
- [x] Test config loading

### Phase 3.2: Ollama Client
- [x] Create `src/llm_client.py`
- [x] Test connection to Ollama
- [x] Test simple chat (no tools)

### Phase 3.3: Tool Definitions
- [x] Define all 14 tools as JSON schema (complete list, not abbreviated)
- [x] Add to `src/tool_definitions.py` or in agent
- [x] Tools to define:
  - Phase 1: get_tick, get_game_info, count_entities, get_production_stats
  - Phase 2: get_player_position, find_nearby_resources, get_player_inventory, get_entity_inventory, craft_item, place_entity, remove_entity, get_assemblers, get_power_stats, get_research_status

### Phase 3.4: Factorio Agent
- [x] Create `src/factorio_agent.py`
- [x] Implement tool execution
- [x] Implement chat loop with max iterations

### Phase 3.5: Integration Testing
- [x] Create `tests/test_phase3.py`
- [x] Test with running Factorio + Ollama
- [x] Verify tool calls work end-to-end

### Phase 3.6: Documentation
- [x] Create `plans/phase-3/key-learnings.md` (document any issues encountered)
- [x] Update README.md with Phase 3 info if needed

---

## Dependencies

```
pip install pyyaml requests
```

(factorio-rcon-py already installed from Phase 1)
