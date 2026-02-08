![Status](https://img.shields.io/badge/status-operational-brightgreen)
![Models](https://img.shields.io/badge/models-8%20providers-blue)
![Cost](https://img.shields.io/badge/cost-90%25%20savings-success)
![License](https://img.shields.io/badge/license-MIT-blue)

# 🌟 Lodestar

**AI-powered development environment with intelligent cost optimization**# 🌟 Lodestar

**AI-powered development environment with intelligent cost optimization**

Lodestar routes your AI coding requests between free local models (Ollama) and paid cloud models (Claude), giving you:
- 💰 **90% cost reduction** (use free models first)
- 🧠 **Never lose context** (persistent session management)
- 🚀 **Unlimited coding** (no usage limits on local models)
- 📝 **Decision tracking** (ADR management)

## Quick Start
```bash
# 1. Start the system
cd ~/ProjectLodestar
./scripts/quick-start.sh

# 2. Start coding (uses FREE local model)
cd ~/your-project
aider file.py

# 3. Document important decisions
./scripts/adr-new.sh "Decision Title"
```

## Architecture
```
┌─────────────────────────────────────┐
│  Aider (AI Coding Agent)            │
└──────────┬──────────────────────────┘
           │
┌──────────▼──────────────────────────┐
│  LiteLLM Router (localhost:4000)    │
│  - Routes based on complexity       │
│  - Tracks costs                     │
│  - Provides fallbacks               │
└──┬────────────────────┬─────────────┘
   │                    │
┌──▼──────────┐  ┌─────▼─────────────┐
│ Ollama      │  │ Claude API        │
│ (T600 VM)   │  │ (Pro Sub)         │
│ FREE        │  │ PAID              │
└─────────────┘  └───────────────────┘
```

## Cost Optimization Strategy

1. **Default to FREE** - DeepSeek Coder handles 80% of coding tasks
2. **Upgrade when needed** - Use Claude for complex architecture
3. **Track spending** - Monitor usage in router logs

## Components

- **Aider**: AI pair programming in terminal
- **LiteLLM**: Multi-provider router with cost optimization  
- **Ollama**: Local LLM inference (on T600 VM)
- **ADR Tools**: Architecture decision records

## Documentation

- [Daily Workflow](docs/WORKFLOW.md) - How to use Lodestar
- [Architecture](docs/ARCHITECTURE.md) - System design
- [Setup Guide](docs/SETUP.md) - Installation instructions

## Requirements

- Python 3.9+
- Node.js 18+
- Git
- Ollama running on accessible machine
- Claude API key (optional, for premium models)

## License

MIT - see [LICENSE](LICENSE)

## Credits

Built on: [Aider](https://aider.chat) • [LiteLLM](https://litellm.ai) • [Ollama](https://ollama.ai)

✨ SSH authentication configured
