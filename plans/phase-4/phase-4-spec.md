# Phase 4: Interactive Mode

## Goal
Create a usable interactive command-line chat interface to talk with Factorio in real-time.

## Why
- Current state: only fixed test scripts work
- After Phase 4: free experimentation, discover what works/fails
- Foundation for iteration based on real usage

## Scope

**In scope:**
- Command-line REPL (terminal-based)
- Clean input/output formatting
- Session commands for control
- Robust error handling
- Verify all 14 existing tools work correctly

**Out of scope:**
- Complex multi-step actions (e.g., "mine 50 coal")
- New Factorio tools
- Web interface or GUI
- Voice input

---

## Deliverables

### 1. src/chat.py - Main Entry Point

```python
"""
Interactive Factorio chat.

Usage:
    conda activate factorio
    cd D:\factorio_llm
    python src/chat.py
"""
```

Features:
- Connect to Factorio and Ollama on startup
- Input loop with prompt
- Call agent with user input
- Display formatted response
- Handle session commands (/, prefix)
- Graceful exit with Ctrl+C or /quit

### 2. Session Commands

| Command | Description |
|---------|-------------|
| `/quit` or `/exit` | Exit cleanly |
| `/clear` | Clear conversation history |
| `/help` | Show available commands |
| `/tools` | List all Factorio tools with descriptions |
| `/model` | Show current model info |
| `/debug` | Toggle debug mode (show tool calls) |

### 3. Output Formatting

**User input:**
```
You> Where am I standing?
```

**Thinking indicator:**
```
Thinking...
```

**Response:**
```
Assistant> You are at position X: -66.4, Y: -17.9
           (west of origin, north of origin)
```

**Tool calls (debug mode):**
```
  [TOOL] get_player_position({})
  [RESULT] {"x": -66.37, "y": -17.87}
```

**Errors:**
```
[ERROR] Cannot connect to Factorio. Is the game running?
```

---

## Implementation Plan

### Phase 4.1: Basic REPL
- [x] Create `src/chat.py` with main loop
- [x] Connect to Factorio on startup (with error handling)
- [x] Connect to Ollama on startup (with error handling)
- [x] Simple input → agent.chat() → print output
- [x] Exit on Ctrl+C or empty input
- [x] Test basic conversation works

### Phase 4.2: Conversation History
- [x] Modify `FactorioAgent` to support conversation history
- [x] Keep messages between chat() calls
- [x] Add `clear_history()` method to agent

### Phase 4.3: Session Commands
- [x] Detect `/` prefix commands
- [x] Implement `/quit` and `/exit`
- [x] Implement `/help` - show command list
- [x] Implement `/tools` - list tools with descriptions
- [x] Implement `/model` - show model info
- [x] Implement `/clear` - calls agent.clear_history()
- [x] Implement `/debug` - toggle debug output

### Phase 4.4: Output Formatting
- [x] Clean prompt format (`You>`, `Assistant>`)
- [x] "Thinking..." indicator during LLM call
- [x] Wrap long responses for readability
- [x] Format tool results nicely (not raw JSON)

### Phase 4.5: Error Handling & Stability
- [x] Catch all exceptions in main loop (no crashes)
- [x] Handle RCON disconnect → try reconnect (max 3 attempts, 2 sec delay)
- [x] Handle Ollama timeout → clear message
- [x] Handle Ctrl+C gracefully
- [x] Clear error messages (not stack traces in normal mode)

### Phase 4.6: Tool Verification
- [x] Review all 14 tool descriptions - clear enough?
- [x] Test each tool via interactive chat
- [x] Document tool calling issues (none found)
- [x] Improve system prompt if needed (not needed)

### Phase 4.7: Documentation
- [x] Create `plans/phase-4/key-learnings.md`
- [x] Update README.md with chat usage
- [x] Document discovered issues/improvements needed (none found)

---

## Technical Details

### Conversation History Support

Current `FactorioAgent.chat()` creates fresh messages each call. Need to:

```python
class FactorioAgent:
    def __init__(self, ...):
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def chat(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})
        # ... tool calling loop ...
        self.messages.append({"role": "assistant", "content": response})
        return response

    def clear_history(self):
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
```

### Debug Mode

```python
class ChatSession:
    def __init__(self):
        self.debug = False

    def toggle_debug(self):
        self.debug = not self.debug
        # Agent uses this to show/hide tool calls
```

### Thinking Indicator

Simple approach (no threading):
```python
print("Thinking...", end="", flush=True)
response = agent.chat(user_input)
print("\r" + " " * 20 + "\r", end="")  # Clear line
print(f"Assistant> {response}")
```

---

## Tool Descriptions Review

Current descriptions to verify are clear:

| Tool | Description | Review |
|------|-------------|--------|
| get_tick | Get current game tick | OK |
| get_game_info | Get basic game info | OK |
| count_entities | Count entities by type | OK - examples in description: 'tree', 'iron-ore', 'assembling-machine' |
| get_production_stats | Production stats for item | OK |
| get_player_position | Get player x,y position | OK |
| find_nearby_resources | Find ore patches | OK - returns: resource name, position (x,y), amount per patch |
| get_player_inventory | Get inventory contents | OK |
| get_entity_inventory | Get chest/machine contents | OK - uses x,y number coordinates |
| craft_item | Craft items by hand | OK |
| place_entity | Place building at position | OK - limitations in description: ~10 tiles range, fails if blocked |
| remove_entity | Remove entity at position | OK |
| get_assemblers | List assembling machines | OK |
| get_power_stats | Get power production/consumption | OK |
| get_research_status | Get research progress | OK |

---

## Success Criteria

- [x] Can start chat session without errors
- [x] Basic queries work ("Where am I?", "How many trees?")
- [x] Actions work ("Place a chest to my right")
- [x] Session commands work (/help, /tools, /quit, etc.)
- [x] No crashes on errors (graceful handling)
- [x] Conversation history maintained between messages
- [x] Debug mode shows tool calls when enabled
- [x] All 14 tools tested and working

---

## Example Session

```
============================================================
FACTORIO CHAT
============================================================
Connected to Factorio (tick: 560000)
Using model: ministral-3:14b-instruct-2512-q4_K_M

Type /help for commands, /quit to exit.

You> Where am I?
Thinking...
Assistant> You are at position X: -66.4, Y: -17.9 (west and north of origin).

You> What resources are nearby?
Thinking...
Assistant> I found several resource patches near you:
           - Copper ore: 1,840 units at (-99.5, -67.5)
           - Iron ore: 2,100 units at (-45.2, -30.1)
           - Coal: 890 units at (-80.0, -50.0)

You> Place a wooden chest 5 tiles to my right
Thinking...
Assistant> Done! I placed a wooden chest at (-61.4, -17.9).

You> /debug
Debug mode: ON

You> How much iron plate have I produced?
Thinking...
  [TOOL] get_production_stats({'item': 'iron-plate'})
  [RESULT] {"item": "iron-plate", "input_count": 1250, "output_count": 980}
Assistant> You have produced 1,250 iron plates and consumed 980.

You> /quit
Goodbye!
```

---

## Dependencies

No new dependencies needed. Uses existing:
- `src/config.py`
- `src/llm_client.py`
- `src/factorio_tools.py`
- `src/factorio_agent.py`
