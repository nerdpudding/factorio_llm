# Phase 7: Key Learnings

## Overview

Phase 7 added Ollama cloud model support, enabling three deployment modes:
- **Mode A**: Fully Local (existing)
- **Mode B**: Local Ollama + Cloud Inference (new)
- **Mode C**: Fully Cloud with API key (new)

This completes the v1.0 foundation - all core functionality is now in place.

---

## Ollama Cloud Architecture

### Two Ways to Access Cloud Models

**Device Mode (Mode B)** - Local Ollama acts as proxy:
```
Python App → localhost:11434 → Ollama (signed in) → ollama.com
```
- Requires: `ollama signin` (one-time)
- Same code, same URL - Ollama handles routing
- Can mix local and cloud models seamlessly

**Direct API Mode (Mode C)** - Bypass local Ollama:
```
Python App → ollama.com/api (with Bearer token)
```
- Requires: API key from ollama.com
- No local Ollama installation needed
- Cloud models only

### URL Construction Bug

**Problem:** Initially used `OLLAMA_CLOUD_API_URL = "https://ollama.com/api"`, but the client code adds `/api/...` paths:

```python
# llm_client.py
f"{self.base_url}/api/tags"  # Becomes: ollama.com/api/api/tags ❌
```

**Solution:** Remove `/api` from the constant:
```python
OLLAMA_CLOUD_API_URL = "https://ollama.com"  # → ollama.com/api/tags ✓
```

**Lesson:** When adding new base URLs, trace through all usages to verify path construction.

---

## Bearer Token Authentication

Ollama's cloud API uses standard Bearer token auth:

```python
def _get_headers(self) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if self.config.ollama_api_key:
        headers["Authorization"] = f"Bearer {self.config.ollama_api_key}"
    return headers
```

Applied to all API calls: `chat()`, `is_available()`, `list_models()`, `unload_model()`.

**API Key Sources** (in order of precedence):
1. `config.yaml`: `ollama_api_key: your_key`
2. Environment variable: `OLLAMA_API_KEY`

---

## Dataclass Field Ordering

**Problem:** Adding optional field caused error:
```python
@dataclass
class Config:
    ollama_api_key: str | None = None  # Optional with default
    max_tool_iterations: int           # Required without default
    # TypeError: non-default argument follows default argument
```

**Solution:** Optional fields with defaults must come AFTER required fields:
```python
@dataclass
class Config:
    # Required fields first
    max_tool_iterations: int
    rcon_password: str

    # Optional fields last (must have defaults)
    ollama_api_key: str | None = None
    available_models: dict = field(default_factory=dict)
```

---

## Model Filtering by Deployment Mode

Cloud models are identified by profile key suffix `-cloud`:

```python
def filter_models_by_mode(config: Config, mode: str) -> None:
    if mode == "local":
        # Keep only non-cloud models
        config.available_models = {
            k: v for k, v in config.available_models.items()
            if not k.endswith("-cloud")
        }
    else:
        # Keep only cloud models
        config.available_models = {
            k: v for k, v in config.available_models.items()
            if k.endswith("-cloud")
        }
```

This ensures users only see relevant models for their chosen deployment mode.

---

## Menu Design

### Two-Level Selection

```
How do you want to run inference?
  1. Local GPU
  2. Ollama Cloud

[If 2 selected:]
Cloud setup:
  a. Local Ollama + Cloud models (ollama signin)
  b. Fully Cloud (API key)
```

**Why two levels?** Simpler initial choice (local vs cloud), then only show cloud sub-options if relevant.

### Validation with Helpful Errors

```python
if not api_key:
    print("[ERROR] API key required for Fully Cloud mode.")
    print("Options:")
    print("  1. Set environment variable: OLLAMA_API_KEY=your_key")
    print("  2. Add to config.yaml: ollama_api_key: your_key")
    print("Get your API key at: https://ollama.com")
    return False
```

---

## Cloud Model Performance

**Mode B observations:**
- Very fast inference (cloud GPUs)
- Thinking mode (`think: true`) now practical due to speed
- No local VRAM usage
- Latency depends on internet connection

**Mode C observations:**
- Same performance as Mode B
- Simpler setup (no local Ollama needed)
- Good for machines without Ollama installed

---

## Config Synchronization

Keep configs in sync:
- `config.yaml` - User's actual config
- `example_config.yaml` - Template with all options documented
- Comments should be identical between both

When adding new features, update both simultaneously to prevent drift.

---

## Testing Checklist for Cloud Features

1. **Mode A (Local)** - Verify still works, cloud models filtered out
2. **Mode B (Local+Cloud)** - Test after `ollama signin`, verify cloud models appear
3. **Mode C (Fully Cloud)** - Test with API key, verify connection to ollama.com
4. **Error cases** - Missing API key, invalid key, network errors
5. **Model switching** - `/switch` between cloud models works

---

## What v1.0 Includes

With Phase 7 complete, the project has:

| Feature | Status |
|---------|--------|
| RCON connection to Factorio | ✅ |
| 17 game interaction tools | ✅ |
| LLM tool calling | ✅ |
| Interactive chat with history | ✅ |
| Multiple model support | ✅ |
| Local inference (Mode A) | ✅ |
| Cloud inference (Mode B) | ✅ |
| Fully cloud (Mode C) | ✅ |
| Thinking model support | ✅ |
| Game state injection | ✅ |

**Future phases (8+)** will extend functionality:
- More tools (belts, inserters, pipes)
- Multi-step automation
- RAG for game help
- Strategy assistant

The foundation is solid - everything from here is additive.
