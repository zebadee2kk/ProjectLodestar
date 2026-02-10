# Lodestar Architecture

## Overview

Lodestar is an AI-assisted development environment that optimizes costs by intelligently routing requests between free local models and paid cloud APIs while maintaining context and decision history.

## System Components

### V1: External Integration Layer
```
┌─────────────────┐
│  Aider (CLI)    │  ← Developer interface
└────────┬────────┘
         ▼
┌─────────────────┐
│  LiteLLM Router │  ← Universal API gateway
└────────┬────────┘
         │
    ┌────┴─────────────────────────┐
    │                               │
    ▼                               ▼
┌──────────────┐           ┌──────────────┐
│ FREE Models  │           │ PAID APIs    │
└──────────────┘           └──────────────┘
```

### V2: Internal Intelligence Layer
The **Lodestar Modular System** (found in `modules/`) provides deep integration, monitoring, and self-healing.

```
┌─────────────────────────────────────────────────────────────┐
│                       LodestarProxy                         │
│           (Orchestrator for all sub-modules)                │
└──────┬──────────┬──────────┬──────────┬──────────┬──────────┘
       │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Semantic │ │   Cost   │ │ AI Diff  │ │ Health   │ │  Agent   │
│ Router   │ │ Tracker  │ │ Annotate │ │ Checker  │ │ Executor │
└──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘
```

| Module | Purpose | Key Feature |
|:---|:---|:---|
| **Semantic Router** | Intelligent model selection | Keyword & rule-based task classification |
| **Cost Tracker** | Financial transparency | SQLite persistence & real-time TUI dashboard |
| **AI Diff** | Code review assistance | Visual highlighting + LLM diff explanations |
| **Health Check** | Environment reliability | Provider latency & connectivity monitoring |
| **Agent Exec** | Self-healing commands | Auto-repair logic for failing terminal tasks |
| **Tournament** | Model benchmarking | Side-by-side match execution and voting |

## Data Flow

### 1. Coding Session Start
```
Developer → aider file.py
          ↓
Aider reads .aider.conf.yml
          ↓
Connects to LiteLLM (localhost:4000)
          ↓
LiteLLM loads routing config
          ↓
Ready: Using gpt-3.5-turbo (DeepSeek via Ollama)
```

### 2. Code Generation Request
```
Developer: "Add error handling to login function"
          ↓
Aider analyzes file context
          ↓
Sends prompt to LiteLLM with model: gpt-3.5-turbo
          ↓
LiteLLM routes to: ollama/deepseek-coder:6.7b @ 192.168.120.211:11434
          ↓
Ollama generates code changes
          ↓
LiteLLM returns response (cost: $0.00)
          ↓
Aider applies diff to file
          ↓
Git auto-commit with descriptive message
```

### 3. Model Escalation
```
Developer: /model claude-sonnet
          ↓
Aider switches to: claude-sonnet
          ↓
Next request routes to: anthropic/claude-sonnet-4-20250514
          ↓
Claude API processes (cost: ~$0.003 per request)
          ↓
Results returned and applied
```

## Configuration Files

### ~/.aider.conf.yml
```yaml
openai-api-base: http://localhost:4000/v1
openai-api-key: sk-1234  # Dummy, LiteLLM uses real keys
model: gpt-3.5-turbo     # Default to FREE
weak-model: local-llama   # Also FREE
auto-commits: true
map-tokens: 2048
```

**Purpose:** Configure Aider to use LiteLLM router as API endpoint

### config/litellm_config.yaml
```yaml
model_list:
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: ollama/deepseek-coder:6.7b
      api_base: http://192.168.120.211:11434
```

**Purpose:** Map model names to actual providers with routing rules

### ~/.bashrc
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export PATH="$HOME/.local/bin:$PATH"
```

**Purpose:** API credentials and tool accessibility

## Cost Optimization Strategy

### Model Selection Logic
```python
# Pseudo-code for intelligent routing

if task_complexity == "simple":
    model = "gpt-3.5-turbo"  # → Ollama (FREE)
    cost = 0.00
    
elif task_complexity == "moderate":
    model = "local-llama"  # → Ollama (FREE)
    cost = 0.00
    
elif task_complexity == "complex":
    model = "claude-sonnet"  # → Claude API (PAID)
    cost = ~0.003 per request
    
elif task_complexity == "critical":
    model = "claude-opus"  # → Claude API (EXPENSIVE)
    cost = ~0.015 per request
```

### Typical Cost Breakdown

**Traditional approach (all Claude):**
- 100 requests/day × $0.003 = $0.30/day
- Monthly: ~$9.00

**Lodestar approach (80% Ollama, 20% Claude):**
- 80 requests/day × $0.00 = $0.00
- 20 requests/day × $0.003 = $0.06/day
- Monthly: ~$1.80

**Savings: 80% cost reduction**

## Context Management

### Repository Mapping

Aider creates a "repository map" using 2048 tokens:
- Function signatures
- Class definitions
- Important comments
- File relationships

This map is sent with each request to provide context without consuming the full context window.

### Git Integration

Every change Aider makes triggers:
1. `git add <modified files>`
2. `git commit -m "AI-generated message"`
3. Commit attributed to: `Aider (aider)`

**Benefits:**
- Complete audit trail
- Easy rollback with `git reset`
- Clear history of AI vs human changes

## Decision Tracking

### ADR (Architecture Decision Records)

Format:
```markdown
# Decision Title

Status: Proposed | Accepted | Deprecated
Date: YYYY-MM-DD

## Context
Why this decision?

## Decision
What are we doing?

## Consequences
What are the tradeoffs?
```

**Storage:** `docs/adr/NNNN-decision-name.md`

**Creation:** `./scripts/adr-new.sh "Decision Title"`

## Security Considerations

### API Key Storage

- **Environment variables**: Keys in `~/.bashrc` (not in git)
- **File permissions**: Ensure `~/.bashrc` is `chmod 600`
- **Never commit**: Keys never appear in repository

### Network Security

- **LiteLLM Router**: localhost only (127.0.0.1:4000)
- **Ollama Connection**: Internal network (192.168.x.x)
- **Claude API**: HTTPS with TLS 1.3

### Code Review

All AI-generated code should be:
1. Reviewed before deployment
2. Tested thoroughly
3. Committed with descriptive messages
4. Subject to normal code review processes

## Scalability

### Single Developer
- Current setup: Perfect
- No additional infrastructure needed

### Small Team (2-5 developers)
- Shared Ollama server (T600)
- Individual LiteLLM instances
- Shared ADR repository

### Large Team (5+ developers)
- Dedicated Ollama cluster
- Centralized LiteLLM proxy
- Team-wide configuration management
- Cost allocation per developer

## Monitoring

### Router Logs

Location: `~/.lodestar/router.log`

Contains:
- Request timestamps
- Model selections
- Token counts
- Response times
- Errors and retries

### Git History
```bash
# See all AI commits
git log --author="aider" --oneline

# See today's AI work
git log --author="aider" --since="today"
```

## Troubleshooting

### Router Not Starting

**Symptom:** `curl http://localhost:4000` fails

**Solution:**
```bash
./scripts/status.sh
./scripts/start-router.sh
```

### Ollama Unreachable

**Symptom:** "Connection refused" to T600 VM

**Check:**
```bash
curl http://192.168.120.211:11434/api/tags
```

**Solution:** Verify T600 VM is running and Ollama service is active

### Claude API Errors

**Symptom:** "Invalid API key" or "Rate limit exceeded"

**Check:**
```bash
echo $ANTHROPIC_API_KEY  # Should show your key
```

**Solution:** Verify key at console.anthropic.com, check usage limits

## Future Enhancements

### Planned Features

1. **SaveContext Integration**
   - Persistent memory across sessions
   - Session pause/resume
   - Context checkpoints

2. **Enhanced Model Routing**
   - Semantic routing based on prompt content
   - Automatic complexity detection
   - Cost prediction before execution

3. **Team Collaboration**
   - Shared ADR dashboard
   - Team cost tracking
   - Collaborative decision review

4. **IDE Integration**
   - VS Code extension
   - JetBrains plugin
   - Real-time diff viewing

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Coding Agent | Aider | 0.86.1 | AI pair programming |
| API Router | LiteLLM | 1.75.0 | Multi-provider gateway |
| Local LLM | Ollama | Latest | Free model inference |
| Models | DeepSeek Coder | 6.7B | Code generation |
| Models | Llama 3.1 | 8B | General tasks |
| Version Control | Git | 2.39+ | Change tracking |
| Runtime | Python | 3.11.2 | Tool execution |
| Runtime | Node.js | 20.20.0 | MCP servers (future) |

## Performance Characteristics

### Response Times

- **Local Ollama**: 2-5 seconds (dependent on T600 GPU)
- **Claude Sonnet**: 1-3 seconds (network dependent)
- **Claude Opus**: 3-8 seconds (larger model)

### Context Limits

- **Aider Repository Map**: 2,048 tokens
- **DeepSeek Coder**: 16K context window
- **Claude Sonnet**: 200K context window

### Throughput

- **Ollama**: Unlimited (local resource only)
- **Claude Pro**: Rate limited by subscription tier
- **Typical usage**: 50-100 requests per 4-hour session

## License

MIT License - See LICENSE file for details

## Contributing

This project is open source. Contributions welcome via pull requests.

Repository: https://github.com/zebadee2kk/ProjectLodestar
