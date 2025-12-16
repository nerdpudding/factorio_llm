# Phase 6: Nemotron-3-Nano Model Support

## Goal
Add support for NVIDIA's Nemotron-3-Nano model as alternative to Ministral-3, with model-specific configuration.

## Why
- Nemotron-3-Nano is specifically designed for agentic tool calling
- MoE architecture: 30B total params, only 3.5B active → fast inference
- Same speed as Ministral-3 14B but potentially better tool calling
- Recent release (15 dec 2025), cutting edge

---

## Key Insight: Modelfile Comparison

### Ministral-3 (explicit)
- Tool calling tags **visible** in TEMPLATE (`[AVAILABLE_TOOLS]`, `[TOOL_CALLS]`)
- PARSER: `ministral`
- Default temperature: 0.15

### Nemotron-3-Nano (delegated)
- Tool calling via **RENDERER** and **PARSER** (invisible, Ollama handles it)
- PARSER: `nemotron-3-nano`
- Default temperature: 1.0
- Default top_p: 1.0

**Conclusion:** API interface is identical - both use Ollama's `tools` parameter. Difference is in how it's handled internally.

---

## Model Parameters

| Parameter | Ministral-3 | Nemotron-3-Nano | Reason |
|-----------|-------------|-----------------|--------|
| **temperature** | 0.15 | 1.0 | Modelfile defaults |
| **top_p** | 1.0 | 1.0 | Modelfile defaults |
| **num_ctx** | 16384 | 8192 | Save VRAM, sliding window sufficient |
| **num_predict** | 1024 | 1024 | Same |

---

## Implementation Plan

### 6.1: Config Refactoring (required)

**Current config.yaml:**
```yaml
model: ministral-3:14b-instruct-2512-q8_0
temperature: 0.15
num_ctx: 16384
num_predict: 1024
```

**New config.yaml with model profiles:**
```yaml
# Model profiles with per-model parameters
models:
  ministral:
    name: ministral-3:14b-instruct-2512-q8_0
    temperature: 0.15
    top_p: 1.0
    num_ctx: 16384
    num_predict: 1024

  nemotron-q4:
    name: nemotron-3-nano:30b-a3b-q4_K_M
    temperature: 1.0
    top_p: 1.0
    num_ctx: 8192
    num_predict: 1024

# Active model (key from models dict)
active_model: ministral

# RCON settings (unchanged)
rcon_host: localhost
rcon_port: 27015
rcon_password: test123

# Agent settings (unchanged)
max_tool_iterations: 5
max_history_messages: 20
```

### 6.2: Config Class Updates

`src/config.py` changes:
- [x] Load `models` dictionary
- [x] Select active model based on `active_model` key
- [x] Make all parameters model-specific
- [x] Backwards compatible: old config format must still work

```python
@dataclass
class Config:
    # Model (resolved from active_model)
    model: str
    temperature: float
    top_p: float
    num_ctx: int
    num_predict: int

    # Agent
    max_tool_iterations: int
    max_history_messages: int

    # RCON
    rcon_host: str
    rcon_port: int
    rcon_password: str

    # New: available models for runtime switching
    available_models: dict  # Optional
```

### 6.3: LLM Client Updates

`src/llm_client.py` changes:
- [x] Add `top_p` parameter to API calls
- [x] Verify all parameters are passed correctly

### 6.4: Test with Nemotron

**Test-first approach:**
1. Switch `active_model: nemotron-q4`
2. Start `python src/chat.py`
3. Enable `/debug`
4. Test: "Where am I?"
5. Expected: `[TOOL] get_player_position({})` in output

### 6.5: Fallback Parser (only if needed)

**DO NOT implement unless test fails!**

If Nemotron outputs tool calls as text instead of native format:
```python
def _parse_toolcall_format(self, content: str) -> dict | None:
    """Parse Nemotron <toolcall> format as fallback."""
    match = re.search(r'<toolcall>\s*(\{.*?\})\s*</toolcall>', content, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            return {"function": {"name": data.get("name"), "arguments": data.get("arguments", {})}}
        except json.JSONDecodeError:
            pass
    return None
```

### 6.6: Runtime Model Switching (optional)

New commands in `chat.py`:
```
/models           # List available models
/switch nemotron  # Switch to different model
```

---

## Files NOT to Change

These files remain unchanged:
- `tool_definitions.py` - works for both models
- `factorio_tools.py` - model-agnostic
- `SYSTEM_PROMPT` - works for both
- `rcon_wrapper.py` - no relation to LLM

---

## Test Cases

| Test | Expected Behavior |
|------|-------------------|
| `Where am I?` | `get_player_position()` |
| `What's nearby?` | `find_nearby_entities()` and/or `find_nearby_resources()` |
| `Mine 100 coal` | `mine_resource(count=100, resource_type="coal")` |
| `Place chest to my right` | `get_player_position()` + `place_entity()` |

---

## Priorities

| Prio | Task | Status |
|------|------|--------|
| 1 | Config.yaml with model profiles | [x] Done |
| 2 | Config class refactor | [x] Done |
| 3 | Add top_p to llm_client | [x] Done |
| 4 | Test with Nemotron | [ ] User test |
| 5 | Fallback parser (if needed) | [ ] Only if test fails |
| 6 | Runtime model switching | [x] Done (/models, /switch) |

---

## Success Criteria

- [ ] Ministral still works with `active_model: ministral` (user test)
- [ ] Nemotron loads with correct parameters (temp 1.0, top_p 1.0, ctx 8192) (user test)
- [ ] Tool calling works on Nemotron (user test)
- [x] Switch between models via config
- [x] Runtime switching via /models and /switch commands
- [x] No breaking changes (backwards compatible config)

---

## Risks

| Risk | Mitigation |
|------|------------|
| Tool calling format different | Fallback parser (only if needed) |
| VRAM issues | num_ctx 8192, Q4 version |
| Config backwards compatibility | Detect old vs new format |

---

## Notes

- Test-first: don't write unnecessary code
- Respect Nemotron defaults (temp 1.0, top_p 1.0)
- Keep parameters configurable for later tuning
- Current Ministral setup must keep working

---

## Post-Test Improvements (from test1_with_thinking)

### 6.7: Auto-Inject Game State

**Problem:** LLM doesn't know player moved between messages. Uses stale position from context.

**Solution:** Before each LLM call, inject current position via RCON (no tool call needed):

```python
# In factorio_agent.py, before llm.chat()
pos = self.tools.get_player_position()
tick = self.tools.get_tick()
state_prefix = f"[Current: x={pos.x:.1f}, y={pos.y:.1f}, tick={tick}]"
# Prepend to user message or inject as system message
```

**Benefits:**
- No extra LLM roundtrip
- 1 cheap RCON call
- LLM always knows current position
- Expandable (inventory count, nearby threats, etc.)

**Implementation:**
- [x] Add `_get_game_state()` method in factorio_agent.py
- [x] Inject state before user message in chat loop
- [x] Show in debug output

### 6.8: Empty Response Handling

**Problem:** LLM sometimes returns empty content with no tool_calls (seen in test line 247).

**Solution:** Detect and handle gracefully:

```python
if not content and not tool_calls:
    if self.debug:
        print(yellow("  [WARN] LLM returned empty response"))
    return "I didn't generate a response. Could you rephrase your question?"
```

**Implementation:**
- [x] Add detection in factorio_agent.py after LLM response
- [x] Return user-friendly fallback message
- [x] Log warning in debug mode

### 6.9: Enhanced Startup Menu

**Problem:** User wants to tweak think/num_ctx at startup without editing config.yaml.

**Current flow:**
```
Select model: [1-3]
→ Load model
```

**New flow:**
```
Select model: [1-3]
→ Show: "think=true, num_ctx=8192"
→ "Use defaults? [Y/n]"
→ If n: "Enable thinking? [y/N]"
→ If n: "Context size? [4096/8192/16384]"
→ Load model
```

**Implementation:**
- [x] Add `configure_session_overrides()` function in chat.py
- [x] Override config.think and config.num_ctx based on user input
- [x] Show final settings before loading

---

## Updated Priorities

| Prio | Task | Status |
|------|------|--------|
| 1 | Config.yaml with model profiles | [x] Done |
| 2 | Config class refactor | [x] Done |
| 3 | Add top_p to llm_client | [x] Done |
| 4 | Test with Nemotron | [x] Done (test1) |
| 5 | Fallback parser (if needed) | [-] Not needed |
| 6 | Runtime model switching | [x] Done (/models, /switch) |
| 7 | Auto-inject game state | [x] Done |
| 8 | Empty response handling | [x] Done |
| 9 | Enhanced startup menu | [x] Done |

---

## Updated Success Criteria

- [x] Ministral still works with `active_model: ministral`
- [x] Nemotron loads with correct parameters
- [x] Tool calling works on Nemotron (native, no fallback needed)
- [x] Switch between models via config
- [x] Runtime switching via /models and /switch commands
- [x] No breaking changes (backwards compatible config)
- [x] Position always current (auto-inject)
- [x] Empty responses handled gracefully
- [x] Session overrides for think/num_ctx
