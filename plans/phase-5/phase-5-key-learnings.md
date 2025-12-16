# Phase 5 Key Learnings

> **See also:** [Phase 1](../phase-1/phase-1-key-learnings.md) (DOT vs COLON), [Phase 2](../phase-2/phase-2-key-learnings.md) (serpent parsing), [Phase 3](../phase-3/phase-3-key-learnings.md) (model selection), [Phase 4](../phase-4/phase-4-key-learnings.md) (interactive chat)

---

## System Prompt Engineering Makes a Huge Difference

### The Problem
The model was:
- Only calling one tool when multiple were needed
- Printing tool calls as text (`find_nearby_resources[ARGS]{"radius": 10}`) instead of using the tool calling API
- Not knowing which tool to use for what purpose

### The Solution
Added detailed, categorized tool documentation directly in the system prompt:

```python
SYSTEM_PROMPT = """You are a Factorio assistant. You MUST use tools to interact with the game - never print tool names as text.

## Available Tools

**Information:**
- get_player_position() - Get your current x,y coordinates
- get_player_inventory() - List items you're carrying
...

**Scanning nearby:**
- find_nearby_entities(radius=20) - Find buildings, chests, machines, belts near you
- find_nearby_resources(radius=50) - Find ore patches (iron, copper, coal, stone)
...
"""
```

### Result
- Model now calls multiple relevant tools in one request
- Better tool selection (uses `find_nearby_entities` for buildings, `find_nearby_resources` for ores)
- More comprehensive answers

---

## Separate Tools for Different Entity Types

### The Problem
When asked "what's around me?", the model only searched for resources OR used `count_entities` which searches the entire map.

### The Solution
Created two separate scanning tools:

| Tool | Purpose | Excludes |
|------|---------|----------|
| `find_nearby_entities(radius)` | Buildings, chests, machines, belts, poles | Resources, trees, fish, character |
| `find_nearby_resources(radius)` | Ore patches (iron, copper, coal, stone) | Everything else |

### Why Two Tools?
- Resources are numerous (thousands of ore tiles) - need aggregation
- Buildings are sparse but important - need individual positions
- Different use cases: "what can I loot?" vs "where are ores?"

---

## Entity Search: Name vs Type

### The Problem
`count_entities("wooden-chest")` returned 0, even though there were 2 wooden chests nearby.

### Root Cause
Factorio's `find_entities_filtered` has two parameters:
- `name` - specific entity name (e.g., "wooden-chest", "iron-ore")
- `type` - category (e.g., "container", "resource", "tree")

We were only searching by `type`, but "wooden-chest" is a `name`.

### The Fix
Try name first, fall back to type:

```python
def count_entities(self, entity_type: str) -> int:
    # Try by name first (e.g., "wooden-chest", "iron-ore")
    lua_name = f'#game.surfaces[1].find_entities_filtered{{name="{entity_type}"}}'
    result = self._rcon.query_lua(lua_name)
    count = int(result) if result else 0

    if count > 0:
        return count

    # If no results, try by type (e.g., "tree", "container")
    lua_type = f'#game.surfaces[1].find_entities_filtered{{type="{entity_type}"}}'
    result = self._rcon.query_lua(lua_type)
    return int(result) if result else 0
```

---

## Fallback Parser for Text Tool Calls

### The Problem
Some models (especially smaller ones) occasionally output tool calls as text:
```
find_nearby_resources[ARGS]{"radius": 10}
```
Instead of using the proper tool calling API.

### The Solution
Added fallback detection in the agent:

```python
def _parse_text_tool_call(self, content: str) -> dict | None:
    import re
    match = re.search(r'(\w+)\[ARGS\](\{[^}]*\})', content)
    if match:
        func_name = match.group(1)
        args_str = match.group(2)
        try:
            args = json.loads(args_str)
            return {"function": {"name": func_name, "arguments": args}}
        except json.JSONDecodeError:
            pass
    return None
```

### Important
When the fallback triggers, replace the message with a proper structure so conversation history stays clean:

```python
if parsed:
    tool_calls = [parsed]
    message = {
        "role": "assistant",
        "content": "",
        "tool_calls": [parsed]
    }
```

---

## Token Counting: Use Ollama's Actual Counts

### The Problem
We were estimating token counts, but user wanted exact numbers.

### The Solution
Ollama returns actual token counts in the response:
- `prompt_eval_count` - tokens in the prompt
- `eval_count` - tokens generated

```python
if debug:
    prompt_tokens = data.get("prompt_eval_count", 0)
    output_tokens = data.get("eval_count", 0)
    print(f"  [OLLAMA] tokens: {prompt_tokens} prompt + {output_tokens} output = {prompt_tokens + output_tokens} total")
```

---

## Before vs After Comparison

### Before (poor system prompt)
```
You> Where am I and what's around?
  [TOOL] get_player_position({})
Assistant> You're at X: -4.6, Y: 14.3. Want me to check something?

You> Look around with radius 10
Assistant> find_nearby_resources[ARGS]{"radius": 10}  ← PRINTED AS TEXT!
```

### After (detailed system prompt + separate tools)
```
You> Where am I and what's around?
  [TOOL] get_player_position({})
  [TOOL] find_nearby_entities({'radius': 20})
  [TOOL] find_nearby_resources({'radius': 50})
Assistant> You're at X: -4.6, Y: 14.3.

           Nearby:
           - 2 wooden chests at (-3.5, 14.5)
           - Spaceship wreckage at (-5.0, -6.0)
           - Iron ore patches to the north

           What would you like to do?
```

---

## Model Selection: Ministral-3 vs Devstral

### The Problem
The larger model (devstral-small-2:24b) performed WORSE than the smaller model (ministral-3:14b) for tool calling. It would check position but then return empty responses without completing the action.

### Root Cause
**Different optimization targets:**

| Model | Focus | Function Calling |
|-------|-------|------------------|
| **Ministral-3** | General-purpose agentic tasks | **Native function calling** + JSON output |
| **Devstral Small 2** | Software engineering/coding | Mistral format (less robust) |

Devstral is built ON Ministral-3's architecture but optimized for code editing and codebase exploration - NOT general tool calling.

### Recommendation
For agentic tasks with function calling, use **ministral-3**:

```yaml
# Best quality (~16GB VRAM)
model: ministral-3:14b-instruct-2512-q8_0

# Good balance (~8GB VRAM)
model: ministral-3:14b-instruct-2512-q4_K_M
```

**Avoid** devstral for general tool calling - it's specialized for coding tasks.

---

## Checklist for LLM Tool Integration

- [x] System prompt has categorized tool documentation?
- [x] Tool descriptions are clear about what they include/exclude?
- [x] Fallback parser for text-based tool calls?
- [x] Separate tools for different entity categories?
- [x] Entity search tries both name and type?
- [x] Actual token counts (not estimates)?
- [x] Empty response handling (no hardcoded fallback)?
- [x] Model has NATIVE function calling support? (ministral-3 recommended)

---

## mine_resource Implementation

### The Problem
`entity.mine()` API doesn't work on resource entities (ore patches). Factorio designed ore patches to be mined by mining drills, not programmatically via Lua.

### The Solution
Direct manipulation via Lua - bypass the `mine()` API entirely:

```lua
-- Instead of: r.mine{inventory=inv, force=p.force}  ← DOESN'T WORK

-- Do this:
r.amount = r.amount - to_mine
inv.insert({name=name, count=to_mine})
if r.amount <= 0 then r.destroy() end
```

### Additional Bugs Found

| Bug | Cause | Fix |
|-----|-------|-----|
| Command fails silently | Lua `--` comments eat code after `.replace('\n', ' ')` | Remove all `--` comments |
| "amount must be > 0" error | Setting `r.amount = 0` is invalid | Destroy entity before amount reaches 0 |
| Mines wrong resource | Function mines first resource found | Added `resource_type` parameter |

### Final Implementation

```python
def mine_resource(self, count: int = 10, resource_type: str = None) -> dict:
    """Mine resources within 30 tiles. Use count=-1 for entire field."""
```

**Features:**
- 30 tile radius (mines entire nearby field)
- `count=-1` mines ALL resources of that type
- `resource_type` parameter to specify what to mine (coal, iron-ore, etc.)
- Returns: `{status, resource, mined, remaining_in_field, field_depleted}`

### Key Insight
Factorio Lua via RCON allows direct world manipulation that bypasses normal game mechanics. This is powerful but requires careful handling of edge cases.

---

## find_nearby_resources Fix

### The Problem
Function returned samples from individual tiles instead of totals. User saw "3 coal deposits: 5, 89, 177 coal" when standing in a field with 300k+ coal.

### Root Cause
Old code grouped by 10x10 chunks and only reported one sample per chunk, limited to 20 results.

### The Fix
Aggregate totals per resource type:

```lua
local totals = {}
for _, r in pairs(resources) do
    if not totals[r.name] then
        totals[r.name] = {total=0, tiles=0}
    end
    totals[r.name].total = totals[r.name].total + r.amount
    totals[r.name].tiles = totals[r.name].tiles + 1
end
```

### New Output
```json
{
    "name": "coal",
    "total_amount": 314541,
    "tile_count": 314,
    "center_x": -113.0,
    "center_y": 37.5
}
```

Now the LLM correctly reports "Er zijn 314.541 eenheden kolen in de buurt".

---

## prompt_toolkit for Enhanced Input

### The Problem
Users wanted arrow key history (↑/↓) for navigating previous inputs. Cross-platform solutions are messy:
- `readline` - Unix only
- `pyreadline3` - Windows only, hacky

### The Solution
Use `prompt_toolkit` - industry standard used by IPython, AWS CLI, pgcli, and many others.

```python
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

session = PromptSession(
    history=FileHistory('.factorio_chat_history'),
    auto_suggest=AutoSuggestFromHistory(),
)
user_input = session.prompt("You> ")
```

### Custom Completer Gotcha

**Problem:** Using `WordCompleter` triggers completions on EVERY word (annoying when typing natural text).

**Solution:** Create custom `Completer` that only triggers when input starts with `/`:

```python
class CommandCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.lstrip()
        if not text.startswith('/'):
            return  # Only complete commands, not regular text
        for cmd in COMMANDS:
            if cmd.startswith(text.lower()):
                yield Completion(cmd, start_position=-len(text))
```

### Auto-suggest Styling

Auto-suggest text was invisible until explicit styling was added:

```python
style = PTStyle.from_dict({
    'prompt': 'cyan',
    'auto-suggest': 'fg:ansigray italic',  # Make it visible!
})
```

### History File Management

**Requirement:** Limit history file size to prevent unbounded growth.

**Implementation:** Trim at startup, not during session:
- During session: let it grow (don't interrupt user)
- At startup: trim to `max_prompt_history` entries
- Configurable in `config.yaml` (default: 500)

```python
def trim_history_file(history_file: Path, max_entries: int) -> None:
    if max_entries <= 0 or not history_file.exists():
        return
    with open(history_file, "r") as f:
        lines = f.readlines()
    if len(lines) > max_entries:
        lines = lines[-max_entries:]  # Keep last N
        with open(history_file, "w") as f:
            f.writelines(lines)
```

### Important Clarification

This is **INPUT recall** only (typing convenience), NOT LLM conversation memory:
- ↑/↓ recalls what YOU typed
- Auto-suggest shows completions from YOUR history
- The LLM does NOT remember previous sessions
- Config comment must make this clear to avoid confusion
