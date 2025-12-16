# Phase 6 Key Learnings - Test 2 (Nemotron without Thinking)

## Test Setup
- Model: `nemotron-3-nano:30b-a3b-q4_K_M`
- Thinking: disabled (`think: false`)
- Parameters: temp=0.6, top_p=0.95, num_ctx=8192
- Game state injection: enabled

## What Worked Well

### Performance
- **Much faster** than with thinking enabled
- Response times comparable to Ministral 14B
- Good balance between speed and quality

### Tool Calling
- Native Ollama tool calling works perfectly
- No fallback parser needed
- Model correctly uses injected position instead of calling get_player_position()

### Position Injection (6.7)
- `[GAME STATE: x=... y=... tick=...]` works excellently
- LLM uses injected coordinates directly for "where am I?" questions
- No unnecessary tool calls for position queries
- Solves the "stale position" problem from test 1

### Session Configuration (6.9)
- User can enable thinking per-session if needed
- Context size adjustable without editing config
- Good UX with clear prompts

## Model Comparison

| Aspect | Ministral 14B | Nemotron Q4 (no think) | Nemotron Q4 (think) |
|--------|--------------|------------------------|---------------------|
| Speed | Fast | Fast | Slower |
| Quality | Good | Better | Best |
| Tool calling | Native | Native | Native |
| VRAM | ~14GB | ~8GB active | ~8GB active |
| Best for | Low VRAM | Balanced | Complex reasoning |

## Changes Made

### Config Changes
- `think: false` as default for Nemotron models
- User can enable thinking per-session via startup menu

### Tool Definition Updates
- `get_player_position`: Description notes position is auto-injected
- `get_tick`: Description notes tick is auto-injected
- Reduces unnecessary tool calls

### System Prompt Updates
- Added "Current Game State" section explaining injection
- Explicitly states: "For simple questions like 'where am I?' -> use injected position directly"
- Removed old rule about "ALWAYS call get_player_position() FIRST"

## Efficiency Gains

| Before (test 1) | After (test 2) |
|----------------|----------------|
| "Where am I?" = 1 tool call | "Where am I?" = 0 tool calls |
| Position check before placement = 1 tool call | Position from injection = 0 tool calls |
| LLM guesses stale position | LLM always has fresh position |

## Recommendations

1. **Default to Nemotron Q4 without thinking** for most users
   - Faster than thinking mode
   - Better quality than Ministral 14B
   - Lower VRAM usage

2. **Enable thinking** only when:
   - Complex multi-step reasoning needed
   - User wants more thorough analysis
   - Speed is not critical

3. **Future auto-injection candidates**:
   - Inventory count (total items)
   - Nearby threat indicator
   - Current crafting status

## Conclusion

Phase 6 is complete. Nemotron-3-Nano is a viable alternative to Ministral-3:
- Better tool calling quality
- MoE architecture = efficient VRAM usage
- Thinking mode available for complex tasks
- Position injection eliminates unnecessary tool calls
