# Phase 4 Key Learnings

> **See also:** [Phase 1 Key Learnings](../phase-1/phase-1-key-learnings.md) for DOT vs COLON syntax, [Phase 2 Key Learnings](../phase-2/phase-2-key-learnings.md) for serpent parsing, [Phase 3 Key Learnings](../phase-3/phase-3-key-learnings.md) for model selection

---

## Conversation History Architecture

### What we changed
The agent now maintains conversation history across multiple `chat()` calls instead of starting fresh each time.

### Implementation
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

### Benefits
- LLM remembers context from previous messages
- Can refer back to earlier questions
- More natural conversation flow

### Potential issue
- Long conversations may exceed context window (32768 tokens)
- Consider adding history trimming in future if needed

---

## Debug Mode Integration

### Approach
Added `debug` flag directly to `FactorioAgent` instead of using a subclass.

### Why this is better than subclassing
- Simpler to toggle at runtime (`/debug` command)
- No need to swap agent instances
- Debug output happens where the tool is executed

### Implementation
```python
class FactorioAgent:
    def __init__(self, ...):
        self.debug = False

    def _execute_tool(self, name: str, args: dict) -> str:
        if self.debug:
            print(f"  [TOOL] {name}({args})")
        # ... execute tool ...
        if self.debug:
            print(f"  [RESULT] {result}")
```

---

## Text Wrapping for Terminal

### Problem
Long LLM responses become hard to read in narrow terminal windows.

### Solution
Use `textwrap.fill()` with proper indentation for continuation lines:

```python
def format_response(text: str, width: int = 70, prefix: str = "Assistant> "):
    # First line gets prefix, subsequent lines get matching indentation
    wrapped = textwrap.fill(
        para,
        width=width,
        initial_indent=prefix,
        subsequent_indent=" " * len(prefix),
    )
```

### Result
```
Assistant> This is a long response that wraps nicely to the next
           line with proper indentation matching the prefix.
```

---

## RCON Reconnection Strategy

### Problem
If Factorio disconnects mid-session, the chat should try to recover.

### Solution
Added `reconnect()` method to FactorioTools:
- Max 3 attempts
- 2 second delay between attempts
- Returns True/False for success

### When to trigger
Detect connection-related errors by checking error message content:
```python
error_str = str(e).lower()
if "connection" in error_str or "rcon" in error_str or "socket" in error_str:
    tools.reconnect()
```

---

## Session Command Pattern

### Design
Commands start with `/` prefix and are handled before LLM call.

### Implementation
```python
if user_input.startswith("/"):
    cmd = user_input.lower()
    if cmd in ["/quit", "/exit"]:
        break
    elif cmd == "/help":
        print(HELP_TEXT)
    # ... more commands ...
    continue  # Skip LLM call
```

### Available commands
| Command | Action |
|---------|--------|
| `/help` | Show command list |
| `/tools` | List available Factorio tools |
| `/model` | Show model info |
| `/clear` | Clear conversation history |
| `/debug` | Toggle debug mode |
| `/quit` | Exit chat |

---

## Checklist for Interactive CLI Tools

- [ ] Clean startup with connection status?
- [ ] Thinking indicator during slow operations?
- [ ] Error messages without stack traces?
- [ ] Graceful exit on Ctrl+C?
- [ ] Reconnection handling?
- [ ] Session commands for control?
- [ ] Debug mode for troubleshooting?
- [ ] Response formatting for readability?
