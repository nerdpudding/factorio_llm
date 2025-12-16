# Phase 3 Key Learnings

> **See also:** [Phase 1 Key Learnings](../phase-1/phase-1-key-learnings.md) for DOT vs COLON syntax, [Phase 2 Key Learnings](../phase-2/phase-2-key-learnings.md) for serpent parsing

---

## Model Selection: Size vs Speed Tradeoff

### What we learned
The 24B parameter model (devstral-small-2) was noticeably slower than the 14B model (ministral-3), especially on first load.

### Recommendation
- **Development/Testing:** Use `ministral-3:14b-instruct-2512-q4_K_M` (faster)
- **Production (if needed):** Consider `devstral-small-2:24b` for complex reasoning

### Config switching
Model can be changed in `config.yaml` without code changes:
```yaml
# Fast model for testing
model: ministral-3:14b-instruct-2512-q4_K_M

# Larger model for complex tasks (commented out)
# model: devstral-small-2:24b-instruct-2512-q4_K_M
```

---

## Cold Start Latency

### What happened
First request after model load takes significantly longer (~30-60 seconds) because:
1. Model needs to be loaded from disk to VRAM
2. Large models (24B = ~15GB) take time to transfer

### Solution
- Keep Ollama running with model loaded
- Use smaller model for development
- First request is always slower - subsequent requests are fast

---

## Entity Placement Grid Snapping

### What we observed
When placing entities at exact coordinates like `(-63.37, -17.87)`, the actual placement was slightly offset.

### Why
Factorio snaps entities to a grid (whole or half tiles depending on entity size). This is normal game behavior, not a bug.

### No action needed
The LLM doesn't need to know about grid snapping - Factorio handles it automatically.

---

## Tool Calling Format

### Ollama handles it
The `/api/chat` endpoint with `tools` parameter automatically handles:
- Injecting tool definitions
- Parsing tool call responses
- No manual `[TOOL_CALLS]` tag parsing needed

### Response structure
```python
response = {
    "message": {
        "role": "assistant",
        "content": "...",  # May be empty if tool call
        "tool_calls": [
            {
                "function": {
                    "name": "get_player_position",
                    "arguments": {}
                }
            }
        ]
    }
}
```

---

## Debug Pattern for Tool Calls

### Useful pattern
Create a debug subclass to see tool calls during testing:

```python
class DebugAgent(FactorioAgent):
    def _execute_tool(self, name: str, args: dict) -> str:
        print(f"[TOOL] {name}({args})")
        result = super()._execute_tool(name, args)
        print(f"[RESULT] {result[:100]}...")
        return result
```

This helps verify:
- Which tools the LLM is calling
- What arguments it's passing
- What results it's receiving

---

## Checklist for New LLM Integrations

- [ ] Config file for easy model switching?
- [ ] Cold start latency acceptable?
- [ ] Tool definitions have clear descriptions?
- [ ] Debug output available for troubleshooting?
- [ ] Max iterations limit to prevent infinite loops?
- [ ] Tool results formatted as strings for LLM?
