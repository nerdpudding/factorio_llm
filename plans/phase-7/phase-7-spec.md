# Phase 7: Ollama Cloud Model Support

## Goal

Enable users without powerful local GPUs to use the project by supporting Ollama's cloud-hosted models, while also providing access to larger, more capable models.

## Why

- Not everyone has 16GB+ VRAM for local inference
- Cloud models offer access to much larger models (120B, 480B, 671B, 1T parameters)
- Same Ollama interface - minimal code changes needed
- Ollama cloud preview offers free tier with limits

## Trade-offs

**Pros:**
- No local GPU required
- Access to state-of-the-art large models
- Same API, same tools, same experience

**Cons:**
- No longer fully local/private (data goes to Ollama servers)
- Requires internet connection
- Free tier has usage limits (paid option available)
- Potential latency compared to local inference

---

## Scope

**In scope:**
- Add cloud model profiles to `example_config.yaml`
- Add deployment mode selection menu in chat.py
- Support all three deployment modes (see below)
- Document setup process for each mode
- Update README with clear comparison table

**Out of scope:**
- Per-model custom prompting/tuning (separate task)
- Cost tracking/monitoring
- Rate limit handling (let Ollama handle errors)

---

## Three Deployment Modes

| Mode | Ollama Instance | Inference | Requirements |
|------|-----------------|-----------|--------------|
| **A: Fully Local** | Local (docker/app) | Local GPU | Ollama installed, GPU with VRAM |
| **B: Local + Cloud** | Local (docker/app) | Cloud | Ollama installed, `ollama signin` |
| **C: Fully Cloud** | Cloud (ollama.com) | Cloud | API key (no local Ollama needed) |

### Mode A: Fully Local (Current Default)
- Ollama runs locally (docker, desktop app, or CLI)
- Models run on your GPU
- No internet needed after model download
- Full privacy - nothing leaves your machine

### Mode B: Local Instance + Cloud Inference
- Ollama runs locally but routes to cloud for inference
- Best of both worlds: local control, cloud power
- Requires: `ollama signin` (one-time)
- Can mix local and cloud models seamlessly

### Mode C: Fully Cloud
- No local Ollama installation needed
- Everything runs on ollama.com
- Requires: API key from ollama.com
- Config: `ollama_url: https://ollama.com/api`

### Implementation

**Menu Flow in chat.py:**
```
============================================================
FACTORIO CHAT
============================================================

How do you want to run inference?
----------------------------------------
  1. Local GPU (requires Ollama + GPU with VRAM)
     More info: https://github.com/ollama/ollama

  2. Ollama Cloud (cloud inference)
     More info: https://ollama.com/cloud

Enter choice [1-2]: 2

Cloud setup:
----------------------------------------
  a. Local Ollama + Cloud models (ollama signin required)
     Your Ollama routes requests to cloud

  b. Fully Cloud (API key required)
     No local Ollama needed, direct to ollama.com

Enter choice [a-b]:
```

**Code Changes:**
- Mode A: `ollama_url = localhost:11434`, show local models
- Mode B: `ollama_url = localhost:11434`, show cloud models, user must `ollama signin`
- Mode C: `ollama_url = https://ollama.com/api`, need API key, show cloud models only

**Config Changes:**
```yaml
# For Mode C (Fully Cloud), uncomment and set:
# ollama_url: https://ollama.com
# ollama_api_key: your_api_key_here  # Or set OLLAMA_API_KEY env var
```

---

## Two Ways to Access Ollama Cloud

There are two different methods to use Ollama cloud models:

### Option A: Device Mode (Recommended)

Your local Ollama installation acts as a proxy to cloud models.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  FACTORIO LLM   │────▶│  LOCAL OLLAMA   │────▶│  OLLAMA CLOUD   │
│  (Python)       │     │  (your docker/  │     │  (ollama.com)   │
│  localhost:11434│     │   desktop app)  │     │  runs the model │
└─────────────────┘     │  Signed in!     │     └─────────────────┘
                        └─────────────────┘
```

**Setup:**
1. `ollama signin` (one-time, authenticates your device)
2. `ollama pull gpt-oss:120b-cloud` (pull cloud models)
3. Use normally - code still talks to `localhost:11434`

**Pros:**
- No code changes needed
- Seamless switching between local and cloud models
- Single signin, device key managed automatically

**Cons:**
- Requires local Ollama installation

### Option B: Direct Cloud API

Bypass local Ollama entirely, talk directly to ollama.com.

```
┌─────────────────┐                          ┌─────────────────┐
│  FACTORIO LLM   │─────────────────────────▶│  OLLAMA CLOUD   │
│  (Python)       │      OLLAMA_API_KEY      │  (ollama.com)   │
│  ollama.com/api │◀─────────────────────────│  runs the model │
└─────────────────┘                          └─────────────────┘
```

**Setup:**
1. Create API key on ollama.com account settings
2. Set environment variable: `OLLAMA_API_KEY=your_key`
3. Change config: `ollama_url: https://ollama.com/api`

**Pros:**
- No local Ollama installation needed
- Can run on machines without Ollama

**Cons:**
- Requires code/config change (different URL)
- Must manage API key
- Cannot use local models (cloud only)

### Our Approach

**We implement Option A (Device Mode)** because:
- Zero code changes - same `localhost:11434` endpoint
- Users can seamlessly mix local and cloud models
- Simpler setup (just `ollama signin` once)

Option B could be added later for users who want cloud-only without local Ollama.

---

## Prerequisites

### User Setup (One-time)

1. **Ollama v0.12+** - Update local Ollama installation
2. **Ollama Account** - Create account at https://ollama.com (free or pro)
3. **Sign In** - Run `ollama signin` in terminal (this registers your device)
4. **Pull Cloud Models** - Pull desired cloud models before use

The local Ollama client handles authentication and routing automatically. No code changes needed in our Python app - it still talks to `localhost:11434`.

---

## Cloud Models to Support

### Tier 1: Direct Cloud Equivalents of Local Models

| Model | Command | Notes |
|-------|---------|-------|
| Nemotron-3-Nano 30B | `ollama pull nemotron-3-nano:30b-cloud` | Cloud version of our default local model |
| Ministral-3 14B | `ollama pull ministral-3:14b-cloud` | Cloud version of our proven tool caller |

### Tier 2: Large Open-Source Models

| Model | Command | Notes |
|-------|---------|-------|
| Mistral Large 3 | `ollama pull mistral-large-3:675b-cloud` | Mistral's top-tier MoE model |
| GPT-OSS 20B | `ollama pull gpt-oss:20b-cloud` | OpenAI's smaller open-weight model |
| GPT-OSS 120B | `ollama pull gpt-oss:120b-cloud` | OpenAI's larger open-weight model |
| DeepSeek V3.2 | `ollama pull deepseek-v3.2:cloud` | DeepSeek's latest flagship |

### Tier 3: Specialized Models

| Model | Command | Notes |
|-------|---------|-------|
| Kimi K2 1T | `ollama pull kimi-k2:1t-cloud` | Moonshot's massive MoE (non-thinking) |
| Kimi K2 Thinking | `ollama pull kimi-k2-thinking:cloud` | Moonshot's thinking model |
| Qwen3 Next | `ollama pull qwen3-next:cloud` | Qwen's latest efficient model |

---

## Implementation

### 7.1: Update example_config.yaml

Add cloud model profiles with sensible defaults:

```yaml
# Cloud Models (require Ollama account + signin)
# --------------------------------------------------
# These models run on Ollama's cloud, not locally.
# Setup: ollama signin, then ollama pull <model>

nemotron-cloud:
  name: nemotron-3-nano:30b-cloud
  temperature: 0.6
  top_p: 0.95
  num_ctx: 8192
  num_predict: 1024
  think: false

ministral-cloud:
  name: ministral-3:14b-cloud
  temperature: 0.15
  top_p: 0.9
  num_ctx: 16384
  num_predict: 1024
  think: false

mistral-large-cloud:
  name: mistral-large-3:675b-cloud
  temperature: 0.3
  top_p: 0.9
  num_ctx: 32768
  num_predict: 2048
  think: false

gpt-oss-small-cloud:
  name: gpt-oss:20b-cloud
  temperature: 0.3
  top_p: 0.9
  num_ctx: 16384
  num_predict: 1024
  think: false

gpt-oss-large-cloud:
  name: gpt-oss:120b-cloud
  temperature: 0.3
  top_p: 0.9
  num_ctx: 32768
  num_predict: 2048
  think: false

deepseek-cloud:
  name: deepseek-v3.2:cloud
  temperature: 0.3
  top_p: 0.9
  num_ctx: 32768
  num_predict: 2048
  think: false

kimi-cloud:
  name: kimi-k2:1t-cloud
  temperature: 0.3
  top_p: 0.9
  num_ctx: 32768
  num_predict: 2048
  think: false

kimi-thinking-cloud:
  name: kimi-k2-thinking:cloud
  temperature: 0.3
  top_p: 0.9
  num_ctx: 32768
  num_predict: 2048
  think: true  # This is a thinking model

qwen-next-cloud:
  name: qwen3-next:cloud
  temperature: 0.3
  top_p: 0.9
  num_ctx: 32768
  num_predict: 2048
  think: false
```

### 7.2: Update README

Add cloud setup section in Quick Start or Prerequisites.

### 7.3: Test Cloud Models

- [ ] Test basic chat with cloud model
- [ ] Test tool calling works
- [ ] Test `/switch` between local and cloud models
- [ ] Document any issues or limitations

---

## Tasks

| Task | Status | Notes |
|------|--------|-------|
| 7.1 Add cloud models to example_config.yaml | ✅ DONE | 9 cloud models added |
| 7.2 Add deployment mode menu to chat.py | ✅ DONE | Three-mode menu with model filtering |
| 7.3 Add API key support for Mode C | ✅ DONE | Config field + env var fallback + header auth |
| 7.4 Update README with deployment modes table | ✅ DONE | Clear comparison table + cloud models list |
| 7.5 Test Mode B (local+cloud) basic chat | ✅ DONE | Fast, thinking mode works well |
| 7.6 Test Mode C (fully cloud) basic chat | ✅ DONE | Works perfectly with API key |
| 7.7 Test tool calling with cloud models | ✅ DONE | Verified with Mode B |
| 7.8 Document optimal parameters per model | ⬜ LATER | Separate task (Phase 8+) |

---

## Success Criteria

- [x] Deployment mode menu appears at startup
- [x] Mode A (local) works as before
- [x] Mode B (local+cloud) works after `ollama signin`
- [x] Mode C (fully cloud) works with API key
- [x] Tool calling works with cloud models
- [x] README has clear comparison table of all modes
- [x] Config supports API key (field + env var)

**Phase 7 COMPLETE** ✅

---

## User Documentation (Draft)

### Setting Up Cloud Models

1. **Update Ollama** to v0.12 or later
   ```cmd
   # Check version
   ollama --version
   ```

2. **Create Ollama Account** at https://ollama.com (free tier available)

3. **Sign In** from terminal
   ```cmd
   ollama signin
   ```
   Follow the prompts to authenticate.

4. **Pull Cloud Models** you want to use
   ```cmd
   # Example: pull the cloud version of our default model
   ollama pull nemotron-3-nano:30b-cloud

   # Or a larger model
   ollama pull gpt-oss:120b-cloud
   ```

5. **Add to config.yaml** (copy from example_config.yaml)

6. **Run chat.py** - cloud models appear in the menu!

### Signing Out

To disconnect from Ollama cloud:
```cmd
ollama signout
```

### Privacy Note

Cloud models process requests on Ollama's servers. According to Ollama: "Ollama's cloud does not retain your data to ensure privacy and security." However, if you require fully local processing, use the non-cloud models.

---

## References

- Ollama Cloud Docs: https://docs.ollama.com/cloud
- Ollama Cloud Blog: https://ollama.com/blog/cloud-models
- Cloud Model Library: https://ollama.com/search?c=cloud
- Ollama Pricing: https://ollama.com/cloud (free tier + pro options)
