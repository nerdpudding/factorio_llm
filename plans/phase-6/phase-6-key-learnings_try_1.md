# Phase 6 Key Learnings - Test 1 (Nemotron with Thinking)

## Test Setup
- Model: `nemotron-3-nano:30b-a3b-q4_K_M`
- Thinking: enabled (`think: true`)
- Parameters: temp=0.6, top_p=0.95, num_ctx=8192

## What Worked Well

### Tool Calling
- Nemotron picks up tool calls correctly via Ollama's native `tools` parameter
- No fallback parser needed - native format works
- Multi-step tool chains work (e.g., position check → resource search)

### Thinking Mode
- `think: true` via Ollama API works
- Reasoning visible in debug output: `[OLLAMA] thinking: ...`
- Model shows better reasoning about what to do next

### Model Selection Menu
- Startup menu works correctly
- Shows available profiles with (default) and (thinking) markers
- Enter for default, number for selection

## Issues Found

### 1. Empty Response (Line 247 in test)
```
[WARN] LLM returned empty response
```
- Model sometimes returns empty content with no tool_calls
- Need to handle gracefully (retry or fallback message)
- Open item from Phase 5 (5.6: Better handling of empty responses)

### 2. Position Awareness Problem
The LLM doesn't realize player might have moved between messages.

**Example from test:**
- User at (5.8, 5.6) → asks "resources nearby?"
- User moves to (18.5, 9.7)
- User asks again "resources nearby?"
- LLM searches at OLD position (5.8, 5.6) instead of current

**User had to explicitly say:** "beetje stom dat je niet eerst gechecked hebt"

**Root cause:** LLM assumes context positions are still valid, doesn't know player can move in real-time.

### 3. Performance (Expected)
- Slower than Ministral 14B (as expected with thinking enabled)
- ~3000-4000 tokens per response with thinking
- Not unworkable, but noticeable delay

## Solutions Identified

### Solution A: Auto-inject Game State
Before each LLM call, inject current position without tool call:
```
[Game state: Player at x=-31.7, y=85.4 | tick=9500]
```

Benefits:
- No extra LLM roundtrip
- 1 RCON call (cheap)
- LLM always knows current position
- Can expand later (inventory count, nearby threats, etc.)

### Solution B: Enhanced Startup Menu
User wants to tweak parameters at startup:
1. Select model (existing)
2. Show defaults → "Use these? [Y/n]"
3. If no: "Enable thinking? [Y/n]"
4. If no: "Context size? [4096/8192/16384]"

### Solution C: Empty Response Handling
Options:
- Retry once with same prompt
- Return fallback message: "I didn't generate a response. Please try again."
- Log warning for debugging

## Implementation Priority

| Priority | Feature | Effort | Impact |
|----------|---------|--------|--------|
| 1 | Auto-inject position (B) | Medium | High - fixes position bug |
| 2 | Empty response handling | Low | Medium - better UX |
| 3 | Enhanced startup menu | Medium | Medium - convenience |

## Quotes from Test

> "maar ik ben verplaatst, beetje stom dat je niet eerst gechecked heb of ik nog wel op diezelfde positie was niet?"

> Model response: "Sorry hoor, ik had even moeten checken of je nog op dezelfde plek stond."

This confirms the LLM understands the problem but can't prevent it without help.

## Technical Notes

### Position Injection Location
In `factorio_agent.py`, before calling `llm.chat()`:
```python
# Get current game state
pos = self.tools.get_player_position()
tick = self.tools.get_tick()

# Inject as system message or prefix to user message
state_msg = f"[Current: x={pos.x:.1f}, y={pos.y:.1f}, tick={tick}]"
```

### Empty Response Detection
In `factorio_agent.py`, after getting LLM response:
```python
if not content and not tool_calls:
    # Empty response - handle gracefully
    return "I didn't generate a response. Could you rephrase your question?"
```

## Next Steps

1. Update phase-6-spec.md with new features
2. Implement auto-inject position
3. Implement empty response handling
4. Implement enhanced startup menu
5. Test again with improvements
