# Phase 5: prompt_toolkit Implementation Plan

## Why prompt_toolkit?

We need arrow key history (↑/↓) for the chat input. Instead of a hacky solution with `pyreadline3` (Windows-only) or `readline` (Unix-only), we use `prompt_toolkit` - the industry standard used by IPython, AWS CLI, and many others.

## Library Info

| Property | Value |
|----------|-------|
| Package | `prompt-toolkit` |
| Version | 3.0.52 (Aug 2025) |
| Maintainer | Jonathan Slenders |
| License | BSD-3-Clause |
| Stars | 10.1k |
| Dependencies | `wcwidth` (minimal) |

## Features We'll Implement

### 5.5a: Basic History (Must Have)
- [x] ↑/↓ arrow keys to navigate previous inputs
- [x] Persistent history file (`.factorio_chat_history`)
- [x] History survives between sessions

### 5.5b: Auto-Suggest (Nice to Have)
- [x] Gray text suggestions based on history
- [x] Press → to accept suggestion

### 5.5c: Command Completion (Nice to Have)
- [x] Tab completion for `/commands`
- [x] Shows available commands: `/help`, `/tools`, `/status`, etc.
- [x] Custom `CommandCompleter` class (only triggers on `/`, not on every word)

### 5.5d: Styled Prompt (Nice to Have)
- [x] Colored `You> ` prompt using prompt_toolkit styles
- [x] Can replace colorama for prompt (keep colorama for output)

---

## Implementation Steps

### Step 1: Add Dependency
```
# requirements.txt
prompt-toolkit>=3.0.50
```

### Step 2: Create PromptSession

Replace `input()` in main loop with prompt_toolkit:

```python
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

# Define commands for completion
COMMANDS = ['/help', '/tools', '/status', '/model', '/models',
            '/switch', '/clear', '/debug', '/quit', '/exit']

def create_prompt_session():
    """Create configured prompt session with history and completion."""
    return PromptSession(
        history=FileHistory('.factorio_chat_history'),
        auto_suggest=AutoSuggestFromHistory(),
        completer=WordCompleter(COMMANDS, ignore_case=True),
        style=Style.from_dict({
            'prompt': 'cyan',
        }),
    )
```

### Step 3: Update Main Loop

```python
# Before (current):
user_input = input(cyan("You> ")).strip()

# After (with prompt_toolkit):
session = create_prompt_session()
# In loop:
user_input = session.prompt("You> ").strip()
```

### Step 4: Handle Exceptions

prompt_toolkit raises different exceptions:
- `KeyboardInterrupt` - Ctrl+C (same as before)
- `EOFError` - Ctrl+D (same as before)

No changes needed for exception handling.

---

## File Changes

| File | Change |
|------|--------|
| `requirements.txt` | Add `prompt-toolkit>=3.0.50` |
| `src/chat.py` | Replace `input()` with `PromptSession.prompt()` |

---

## Colorama Compatibility

**No conflict!** They serve different purposes:
- `colorama`: Colors in **output** (print statements)
- `prompt_toolkit`: Enhanced **input** (user typing)

We keep colorama for:
- `green()` - Assistant responses
- `red()` - Error messages
- `yellow()` - Tool calls in debug
- `dim()` - Status messages

We use prompt_toolkit for:
- `You> ` prompt with history
- Tab completion
- Auto-suggestions

---

## Testing Plan

1. Start chat: `python src/chat.py`
2. Type a few messages
3. Press ↑ - should show previous input
4. Press ↓ - should navigate forward
5. Type `/` and press Tab - should show commands
6. Type `/he` and press Tab - should complete to `/help`
7. Exit and restart - history should persist
8. Press ↑ - should show inputs from previous session

---

## Rollback Plan

If prompt_toolkit causes issues:
1. Remove from requirements.txt
2. Revert chat.py to use `input()`
3. History feature disabled, everything else works

---

## Estimated Effort

| Task | Time |
|------|------|
| Add dependency | 1 min |
| Create prompt session | 5 min |
| Update main loop | 5 min |
| Test | 5 min |
| **Total** | ~15 min |

---

## Success Criteria

- [x] ↑/↓ navigates history
- [x] History persists between sessions
- [x] Tab completes /commands
- [x] Gray auto-suggest appears
- [x] Existing colors still work (colorama for output, prompt_toolkit for input)
- [ ] Ctrl+C still exits gracefully (needs user test)
