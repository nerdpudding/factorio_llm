# Factorio LLM

A terminal-based Python app that connects an LLM to Factorio, letting you control the game via natural language.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
  - [1. Configure RCON](#1-configure-rcon-one-time)
  - [2. Python Environment](#2-python-environment-one-time)
  - [3. Start Factorio](#3-start-factorio-multiplayer-mode)
  - [4. Launch Chat](#4-launch-chat)
- [Usage](#usage)
  - [Commands](#commands)
  - [Input Features](#input-features)
  - [Supported Models](#supported-models)
- [User Guide](#user-guide)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)
- [For Developers & AI Agents](#for-developers--ai-agents)
  - [Architecture](#architecture)
  - [Key Files](#key-files)
  - [Adding New Tools](#adding-new-tools)
  - [Running Tests](#running-tests)
  - [RCON Basics](#rcon-basics)
  - [Troubleshooting](#troubleshooting)
- [Author](#author)
- [License](#license)

---

## Overview

This is a **work-in-progress, highly experimental project** exploring how LLMs can enhance gameplay.

The Python app is glue between [Ollama](https://ollama.ai) (LLM backend) and Factorio (game). You type natural language, the LLM decides which game actions to take, and the app executes them via RCON. See [Architecture](#architecture) for details.

**What you can do:**
- "How much iron am I producing?" → LLM calls `get_production_stats`
- "Place 5 chests to my right" → LLM calls `get_player_position` + `place_entity`
- Query game state, discuss strategy, get help with builds

**Why local-first?**
- **Cost-effective**: No API fees or rate limits
- **Private & secure**: All processing stays on your machine
- **Fast**: No network latency, modern gaming GPUs handle this easily

Ollama handles all LLM inference. Primary use case is local GPU, but hybrid and cloud options exist for those without capable hardware (see [Deployment Modes](#deployment-modes)).

---

## Features

- Natural language queries about game state, resources, production
- Place and remove entities via chat
- Mine resources, check inventory, craft items
- Multiple model support with runtime switching
- Debug mode to see tool calls and game state
- Input history with arrow keys, tab completion, auto-suggest

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| **Factorio** | Version 2.0.72+ (Steam) |
| **Python 3.11+** | With package manager ([Conda](https://docs.conda.io/en/latest/miniconda.html), venv, or your preference) |
| **Ollama** | Mode A & B only. [Install from GitHub](https://github.com/ollama/ollama) |
| **GPU with VRAM** | Mode A only. 16GB+ recommended for local inference |

### Deployment Modes

This project supports three deployment modes:

| Mode | Description | Requirements |
|------|-------------|--------------|
| **A: Fully Local** | Ollama + inference on your GPU | Ollama installed, GPU with 16GB+ VRAM |
| **B: Local + Cloud** | Local Ollama routes to cloud | Ollama installed, `ollama signin` |
| **C: Fully Cloud** | Everything on ollama.com | API key (no local Ollama needed) |

**Mode A (Fully Local)** - Default. Complete privacy, no internet needed after model download.

**Mode B (Local + Cloud)** - Best of both worlds. Your local Ollama acts as a proxy to cloud models. Run `ollama signin` once to authenticate, then access larger models (up to 675B+) without local GPU requirements.

**Mode C (Fully Cloud)** - No local installation needed. Set `ollama_url: https://ollama.com` and provide an API key. Get your key at [ollama.com](https://ollama.com).

### Setting Up Cloud Models (Mode B)

1. **Create Ollama account** at [ollama.com](https://ollama.com)

2. **Sign in from your Ollama instance**
   ```cmd
   # If using Docker:
   docker exec -it ollama bash
   ollama signin

   # If using Ollama directly:
   ollama signin
   ```
   This opens a URL - click it to link your device automatically.

3. **Pull cloud models** (downloads only metadata, not the full model)
   ```cmd
   ollama pull nemotron-3-nano:30b-cloud
   ollama pull ministral-3:14b-cloud
   ollama pull mistral-large-3:675b-cloud
   ollama pull gpt-oss:20b-cloud
   ollama pull gpt-oss:120b-cloud
   ollama pull deepseek-v3.2:cloud
   ollama pull kimi-k2:1t-cloud
   ollama pull kimi-k2-thinking:cloud
   ollama pull qwen3-next:cloud
   ```

4. **Verify with `ollama list`** - cloud models show `-` for size:
   ```
   NAME                          SIZE
   nemotron-3-nano:30b-cloud     -          <- Cloud model
   nemotron-3-nano:30b-a3b-q4    24 GB      <- Local model
   ```

5. **Add cloud profiles to config.yaml** - copy the cloud model sections from `example_config.yaml`

### About VRAM Requirements (Mode A only)

Local models work well on 16GB+ VRAM GPUs:
- **Nemotron-3-Nano Q4**: ~8GB (balanced, recommended)
- **Nemotron-3-Nano Q8**: ~16GB (higher quality)
- **Ministral-3 14B Q8**: ~14GB (proven tool calling)

For cloud modes (B and C), no local GPU is required. See [Ollama Cloud](https://ollama.com/cloud) for available models and pricing.

### Local Model Setup (Mode A)

The models in `config.yaml` are examples - feel free to experiment with different models and quantizations.

**Finding models:**
1. Browse [ollama.com/library](https://ollama.com/library) for available models
2. Check tags for different quantizations (e.g., [ministral-3/tags](https://ollama.com/library/ministral-3/tags))
3. Pick a version that fits your VRAM (Q4 = smaller, Q8 = more accurate)

**Pulling models:**
```cmd
# Example: smaller Ministral variant (9.1GB)
ollama pull ministral-3:14b-instruct-2512-q4_K_M

# Example: Nemotron for better tool calling (24GB)
ollama pull nemotron-3-nano:30b-a3b-q4_K_M
```

**VRAM notes:**
- Factorio uses ~2GB VRAM, leaving room for the model
- Model size ≠ total VRAM usage (add ~20% for KV cache)
- 16GB GPU can comfortably run Q4 models alongside Factorio

**Quick Ollama setup with Docker:**
```cmd
docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama -e OLLAMA_KV_CACHE_TYPE=q8_0 -e OLLAMA_KEEP_ALIVE=10m ollama/ollama
```

For more options see the [Ollama GitHub](https://github.com/ollama/ollama).

**Too complicated?** Use Mode C (fully cloud) - works great, just has rate limits on the free tier.

---

## Quick Start

### 1. Configure RCON (one-time)

Edit Factorio's config file:
```
C:\Users\<USER>\AppData\Roaming\Factorio\config\config.ini
```

Find the `[other]` section and change:
```ini
; local-rcon-socket=0.0.0.0:0
; local-rcon-password=
```

To:
```ini
local-rcon-socket=0.0.0.0:27015
local-rcon-password=yourpassword
```

Remove the `;` semicolons and set your password. See [info/config.ini](info/config.ini) for a complete example.

### 2. Python Environment (one-time)

```cmd
# Create and activate environment (example with conda)
conda create -n factorio python=3.11
conda activate factorio

# Install dependencies
cd /d D:\factorio_llm
pip install -r requirements.txt

# Create your config
copy example_config.yaml config.yaml
```

Edit `config.yaml` and set your RCON password (must match Factorio's `config.ini`).

### 3. Start Factorio (Multiplayer Mode)

**Important:** RCON only works in multiplayer sessions!

1. Start Factorio via Steam
2. Click **Multiplayer** → **Host new game** (or **Host saved game**)
3. Start playing

> **Note:** This is NOT regular Freeplay or Tutorial mode. You must host a multiplayer session, but you can play solo - see Factorio's in-game multiplayer options for details.

### 4. Launch Chat

```cmd
conda activate factorio
python src/chat.py
```

You'll see a model selection menu, then connect to your game:

```
============================================================
FACTORIO CHAT
============================================================

Select model:
  1. ministral (default)
  2. nemotron-q4
  3. nemotron-q8

Connecting to Factorio...
Connected (tick: 560000, 16 tools available)
Player position: X=-66.4, Y=-17.9

Type /help for commands, /quit to exit.
```

---

## Usage

### Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/tools` | List all available Factorio tools |
| `/status` | Show connection status and player position |
| `/model` | Show current model info |
| `/models` | List available model profiles |
| `/switch <name>` | Switch to a different model profile |
| `/clear` | Clear conversation history |
| `/debug` | Toggle debug mode (shows tool calls and results) |
| `/quit` | Exit chat |

### Input Features

Powered by [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/):

| Feature | How to use |
|---------|------------|
| **History** | ↑/↓ arrows to navigate previous inputs |
| **Tab completion** | Type `/` then Tab to complete commands |
| **Auto-suggest** | Press → to accept gray suggestion text |

History persists between sessions in `.factorio_chat_history`.

### Supported Models

**Local Models (Mode A)**

| Model | VRAM | Notes |
|-------|------|-------|
| Ministral-3 14B Q8 | ~14GB | Proven tool calling |
| Nemotron-3-Nano Q4 | ~8GB | Balanced (recommended) |
| Nemotron-3-Nano Q8 | ~16GB | Higher quality |

**Cloud Models (Modes B & C)**

| Model | Parameters | Notes |
|-------|------------|-------|
| Mistral Large 3 | 675B MoE | Mistral's flagship |
| GPT-OSS | 20B / 120B | OpenAI's open-weight models |
| DeepSeek V3.2 | - | DeepSeek's latest |
| Kimi K2 | 1T MoE | Moonshot's massive model |

Configure models in `config.yaml`. See `example_config.yaml` for all available profiles.

---

## User Guide

*Coming soon: examples, screenshots, and video demonstrations.*

### Example Conversations

```
You> Where am I?
Assistant> You are at position X: -66.4, Y: -17.9

You> What resources are nearby?
Assistant> I found several resource patches near you:
           - Copper ore: 1,840 units at (-99.5, -67.5)
           - Iron ore: 2,100 units at (-45.2, -30.1)

You> Place a wooden chest 3 tiles east
Assistant> Placed wooden-chest at (-63.4, -17.9)

You> How much iron plate am I producing per minute?
Assistant> You're producing 245 iron plates per minute.
```

---

## Project Structure

```
factorio_llm/
├── src/                      # Main source code
│   ├── chat.py               # Interactive chat entry point
│   ├── factorio_agent.py     # LLM agent with tool calling
│   ├── factorio_tools.py     # Game interaction tools (17 tools)
│   ├── tool_definitions.py   # LLM tool schemas
│   ├── llm_client.py         # Ollama API client
│   ├── rcon_wrapper.py       # Low-level RCON communication
│   └── config.py             # Configuration management
│
├── tests/                    # Test scripts
├── plans/                    # Phase specifications & learnings
├── scripts/                  # Utility scripts (log viewer, API lookup)
├── info/                     # Reference configs
│
├── config.yaml               # Your local config (git-ignored)
├── example_config.yaml       # Template config
└── requirements.txt          # Python dependencies
```

### Key Responsibilities

| File | Purpose |
|------|---------|
| `chat.py` | Entry point, user interface, command handling |
| `factorio_agent.py` | Orchestrates LLM ↔ tools interaction |
| `factorio_tools.py` | All game queries and actions |
| `tool_definitions.py` | Defines what tools the LLM can call |
| `rcon_wrapper.py` | Sends Lua commands to Factorio via RCON |

---

## Roadmap

| Phase | Goal | Status |
|-------|------|--------|
| 1 | RCON wrapper + basic queries | ✅ Complete |
| 2 | Player tools (inventory, crafting, placement) | ✅ Complete |
| 3 | Ollama LLM integration with tool calling | ✅ Complete |
| 4 | Interactive chat REPL | ✅ Complete |
| 5 | Polish (colors, history, mining, prompt_toolkit) | ✅ Complete |
| 6 | Nemotron model support + game state injection | ✅ Complete |
| 7 | Ollama cloud model support (no local GPU required) | ✅ Complete |
| 8 | Extended tools (belts, inserters, miners, pipes) | 💡 Planned |
| 9 | Multi-step automation (LLM plans and executes) | 💡 Planned |
| 10 | Game help with RAG (embed official documentation) | 💡 Idea |
| 11 | Strategy assistant (ongoing, leverage all capabilities) | 💡 Idea |

### v1.0 Milestone

**Phases 1-7 complete!** The core foundation is in place:
- RCON integration with Factorio
- 17 game interaction tools
- LLM tool calling with multiple models
- Three deployment modes (local GPU, local+cloud, fully cloud)
- Interactive chat with history and completions

Future phases (8+) extend functionality with more tools and automation.

### Future Phase Notes

**Phase 10 - Game Help:** Factorio's in-game help is already good, but an LLM could enhance it. The idea is to use RAG (Retrieval-Augmented Generation) to embed official documentation, allowing efficient search without bloating the context window. Alternative approaches that provide more deterministic results are also being considered.

**Phase 11 - Strategy Assistant:** The end goal - combine all tools, game state awareness, and LLM reasoning to help create in-game strategies based on real-time information. This will be an ongoing, evolving phase.

Each phase has detailed documentation in `plans/phase-X/`:
- `phase-X-spec.md` - Specification and requirements
- `phase-X-key-learnings.md` - Lessons learned during implementation

---

## For Developers & AI Agents

This section contains technical details for contributors and AI coding assistants.

### Architecture

```
┌─────────────────┐
│  FACTORIO       │
│  (Steam)        │
│  Multiplayer    │
│  RCON enabled   │
└────────┬────────┘
         │ RCON (port 27015)
         ▼
┌─────────────────┐     ┌─────────────────┐
│  PYTHON         │────▶│  OLLAMA         │
│  factorio_tools │     │  (local/cloud)  │
│  factorio_agent │◀────│  Tool calling   │
└─────────────────┘     └─────────────────┘
```

### Key Files

| File | Description |
|------|-------------|
| `src/factorio_tools.py` | Implement new game tools here |
| `src/tool_definitions.py` | Register tools for LLM (JSON schema) |
| `plans/` | Phase specs with learnings - read before contributing |
| `scripts/watch_log.py` | Live Factorio log viewer for debugging |

### Adding New Tools

1. Add the method to `factorio_tools.py`
2. Add the tool definition to `tool_definitions.py`
3. The agent automatically picks up new tools

Example tool pattern:
```python
# In factorio_tools.py
def my_new_tool(self, param: str) -> str:
    lua = f'/c rcon.print(serpent.line(game.something("{param}")))'
    return self._execute(lua)
```

### Running Tests

Test scripts verify RCON connectivity and tool functionality:

```cmd
python tests/test_tools.py      # Basic RCON + Phase 1 tools
python tests/test_phase2.py     # Player tools (inventory, placement)
python tests/test_ollama.py     # Ollama connection
python tests/test_phase3.py     # Full LLM integration
```

**Requirement:** Factorio must be running in multiplayer mode.

### RCON Basics

Direct RCON usage (for debugging or custom scripts):

```python
from factorio_rcon import RCONClient

client = RCONClient("localhost", 27015, "yourpassword")

# Simple command
client.send_command("/version")

# Lua command (note /c prefix)
client.send_command("/c rcon.print(game.tick)")

# Query with serpent serialization
client.send_command('/c rcon.print(serpent.line(game.player.position))')
```

### Troubleshooting

#### Lua Syntax: DOT vs COLON

When calling Factorio Lua API methods via RCON, **always use DOT (`.`) syntax**, not colon (`:`).

| Syntax | What happens | Result |
|--------|--------------|--------|
| `obj:method(arg)` | Passes `obj` as hidden first argument | ❌ Breaks API |
| `obj.method(arg)` | Only passes `arg` | ✅ Works |

```lua
-- WRONG - colon passes 'force' as first arg
game.forces["player"]:get_item_production_statistics("nauvis")
-- Error: "Invalid SurfaceIdentification"

-- CORRECT - dot syntax
game.forces["player"].get_item_production_statistics("nauvis")
-- Works!
```

#### Serpent Output Parsing

Factorio's `serpent.line()` adds **spaces around `=`** and field order is not guaranteed:

```python
# You might expect: {x=123,y=456}
# Factorio returns: {x = 123, y = 456}

# WRONG - assumes no spaces
pattern = r'x=([-\d.]+)'

# CORRECT - tolerates spaces
pattern = r'x\s*=\s*([-\d.]+)'
```

**Best practice:** Parse each field separately:
```python
name = re.search(r'name\s*=\s*"([^"]+)"', output)
count = re.search(r'count\s*=\s*(\d+)', output)
```

#### Debug Mode

Use `/debug` in chat to see tool calls and results:
```
You> /debug
Debug mode: ON

You> Where am I?
  [STATE] [GAME STATE: x=-66.4 y=-17.9 tick=560000]
  [TOOL] get_player_position({})
  [RESULT] {"x": -66.4, "y": -17.9}
```

#### Factorio Log Viewer

For deeper debugging, run the log viewer:
```cmd
python scripts/watch_log.py
```

Shows live Factorio logs with RCON messages highlighted.

---

## Author

Created by **nerdpudding** - [GitHub](https://github.com/nerdpudding)

If you find this useful, a star would be appreciated!

## License

MIT License - see [LICENSE](LICENSE) for details.

You're free to fork, modify, and use this project. Attribution appreciated.
