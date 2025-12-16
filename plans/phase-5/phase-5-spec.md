# Phase 5: Polish & Quick Wins

## Goal
Small improvements to make the chat experience smoother and more robust, without adding complexity.

## Why
- Phase 4 works, but there are easy wins left on the table
- Quick improvements with high impact, low effort
- Prepare foundation for future phases

## Scope

**In scope:**
- Quick wins (moved from Phase 4)
- Simple UX improvements
- Stability improvements
- Small tool additions if low effort

**Out of scope:**
- New complex features
- Major architectural changes
- New entity types (belts, inserters, etc. → Phase 6)

---

## Quick Wins (from Phase 4)

### 5.1: Terminal Colors
- [x] Add `colorama` to requirements.txt
- [x] Color `You>` prompt (cyan)
- [x] Color `Assistant>` response (green)
- [x] Color `[ERROR]` messages (red)
- [x] Color `[TOOL]` debug output (yellow)
- [x] Graceful fallback if colorama not available

**Estimate:** ~15 lines of code

### 5.2: History Limit
- [x] Add `max_history_messages` to config.yaml (default: 20)
- [x] Trim oldest messages when limit exceeded (keep system prompt)
- [x] Log info when trimming occurs (debug mode)

**Estimate:** ~10 lines of code

---

## Additional Improvements

### 5.3: Startup Info
- [x] Show tool count on startup (dynamically counted)
- [x] Show current player position on connect
- [x] Show game tick / time played

### 5.4: Better Error Messages
- [x] "Cannot connect to Factorio" → "Make sure Factorio is running in Host Game mode"
- [?] "Entity cannot be placed" hint — DEFERRED: LLM interprets RCON errors, needs real-world testing
- [?] "Item not found" hint — DEFERRED: LLM interprets RCON errors, needs real-world testing

### 5.5: Command Improvements
- [x] `/status` - show connection status, model, player position
- ~~`/save`~~ - niet nodig
- [x] Command/prompt history met pijltjes toetsen (↑/↓) via prompt_toolkit
- [x] Tab completion voor /commands
- [x] Auto-suggest (grijze tekst) gebaseerd op history

### 5.6: Response Improvements
- [x] Fallback parser for text-based tool calls (e.g., `func[ARGS]{...}`)
- ~~Detect when LLM doesn't use a tool but should have~~ — WON'T FIX: /debug already shows tool calls
- ~~Suggest using `/debug` when errors occur~~ — WON'T FIX: would be annoying on repeat errors
- [x] Better handling of empty responses (implemented in Phase 6)

---

## Bonus: Tool Improvements (Added During Phase 5)

### 5.7: mine_resource Tool ✅
- [x] Direct Lua manipulation (bypasses broken `entity.mine()` API)
- [x] 30 tile radius (mines entire nearby field)
- [x] `count=-1` parameter to mine entire field at once
- [x] `resource_type` parameter to specify what to mine
- [x] Proper error handling for edge cases

### 5.8: find_nearby_resources Fix ✅
- [x] Returns TOTAL amount per resource type (not individual tile samples)
- [x] Includes tile count and center position
- [x] Aggregates across entire search radius

### 5.9: find_nearby_entities Tool ✅
- [x] Separate from find_nearby_resources (different use cases)
- [x] Finds buildings, chests, machines, belts, poles
- [x] Excludes resources, trees, fish, character

### 5.10: System Prompt Engineering ✅
- [x] Detailed, categorized tool documentation in system prompt
- [x] Clear descriptions of what each tool includes/excludes
- [x] Model now calls multiple relevant tools in one request

### 5.11: prompt_toolkit Integration ✅
- [x] ↑/↓ arrow key navigation through input history
- [x] Persistent history file (`.factorio_chat_history`)
- [x] Tab completion for `/commands` only (custom `CommandCompleter`)
- [x] Auto-suggest (gray italic text) based on history
- [x] Graceful fallback if prompt_toolkit not installed
- [x] `max_prompt_history` config option (default: 500)
- [x] History file trimming at startup (keeps last N entries)
- [x] Clear documentation that this is INPUT recall only, not LLM memory

---

## Implementation Order

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| 1 | 5.1 Terminal Colors | Low | High (visual) |
| 2 | 5.2 History Limit | Low | Medium (stability) |
| 3 | 5.3 Startup Info | Low | Medium (UX) |
| 4 | 5.4 Error Messages | Medium | High (UX) |
| 5 | 5.5 Command Improvements | Medium | Medium |
| 6 | 5.6 Response Improvements | Medium | Low |

---

## Success Criteria

- [x] Terminal has colored output (if colorama installed)
- [x] Long conversations don't crash (history trimming)
- [x] Game tick shown at startup
- [x] Tool count and player position shown at startup
- [?] Error messages are helpful — DEFERRED: LLM handles most, needs testing
- [x] mine_resource tool works with direct Lua manipulation
- [x] find_nearby_resources returns proper totals
- [x] System prompt guides model to use correct tools
- [x] Prompt history with ↑/↓ arrow keys (prompt_toolkit)
- [x] Tab completion for /commands
- [x] Auto-suggest based on history

---

## Dependencies

Optional (graceful fallback if missing):
- `colorama` - terminal colors for output
- `prompt-toolkit>=3.0.50` - enhanced input (history, Tab completion, auto-suggest)

---

## Notes

- Keep changes small and focused
- Each item should be completable in < 30 minutes
- Test after each change
- Don't add features "just because" - only if they improve daily use
