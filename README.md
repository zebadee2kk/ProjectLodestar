![Status](https://img.shields.io/badge/status-operational-brightgreen)
![Models](https://img.shields.io/badge/models-8%20providers-blue)
![Cost](https://img.shields.io/badge/cost-90%25%20savings-success)
![License](https://img.shields.io/badge/license-MIT-blue)

# 🌟 Lodestar

**AI-powered development environment with intelligent cost optimization**

Lodestar is a production-ready AI coding stack that routes between 8 LLM providers, defaulting to FREE local models while seamlessly escalating to premium APIs only when needed. Achieve 90%+ cost savings compared to using Claude/ChatGPT exclusively.

---

## ✨ Key Features

- **💰 90% Cost Savings** - Default to FREE Ollama models (DeepSeek, Llama)
- **🔄 8 LLM Providers** - Claude, OpenAI, Grok, Gemini + FREE models
- **🤖 Smart Routing** - Automatic provider selection via LiteLLM
- **📝 Never Lose Context** - Git auto-commits preserve all changes
- **🎯 Zero Configuration** - Works out of the box with sensible defaults
- **🧪 Automated Testing** - Verify all providers in 60 seconds
- **🔐 Secure** - API keys in environment, logs excluded from git

---

## 🚀 Quick Start

### Prerequisites

- Debian/Ubuntu Linux VM (2 CPU, 4GB RAM minimum)
- Ollama server with GPU (separate VM recommended)
- Python 3.11+
- Git

### Installation
```bash
# Clone repository
git clone git@github.com:zebadee2kk/ProjectLodestar.git
cd ProjectLodestar

# Install dependencies
pip install --break-system-packages aider-chat litellm

# Configure API keys (optional - FREE models work without these)
nano ~/.bashrc
# Add:
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export XAI_API_KEY="xai-..."
export GEMINI_API_KEY="..."

source ~/.bashrc

# Start router
./scripts/start-router.sh

# Test everything
./scripts/test-providers-simple.sh
```

### First Use
```bash
# Navigate to your project
cd ~/your-project

# Start coding with FREE AI
aider file.py

# Need more power? Switch to Claude
aider --model claude-sonnet file.py

# Switch models mid-session
/model gpt-4o-mini
/model gpt-3.5-turbo  # Back to FREE
```

---

## 📊 Provider Overview

| Tier | Provider | Model Alias | Cost | Status |
|------|----------|-------------|------|--------|
| 1 | **DeepSeek** | `gpt-3.5-turbo` | **FREE** | ✅ Working |
| 1 | **Llama 3.1** | `local-llama` | **FREE** | ✅ Working |
| 2 | Claude Sonnet | `claude-sonnet` | $3/$15 per M | 💳 Needs Credits |
| 2 | Claude Opus | `claude-opus` | $15/$75 per M | 💳 Needs Credits |
| 3 | GPT-4o Mini | `gpt-4o-mini` | $0.15/$0.60 per M | 💳 Needs Credits |
| 3 | GPT-4o | `gpt-4o` | $2.50/$10 per M | 💳 Needs Credits |
| 4 | Grok Beta | `grok-beta` | $5/$15 per M | 💳 Needs Credits |
| 5 | Gemini | `gemini-pro` | $0.08/$0.30 per M | ⚙️ Config Needed |

---

## 🏗️ Architecture
```
┌─────────────────┐
│  Aider (CLI)    │  ← Your coding interface
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LiteLLM Router │  ← Smart routing layer (localhost:4000)
│  (OpenAI API)   │
└────────┬────────┘
         │
    ┌────┴─────────────────────────┐
    │                               │
    ▼                               ▼
┌──────────────┐           ┌──────────────┐
│ FREE Models  │           │ PAID APIs    │
│              │           │              │
│ • DeepSeek   │           │ • Claude     │
│ • Llama 3.1  │           │ • OpenAI     │
│   (T600 GPU) │           │ • Grok       │
│              │           │ • Gemini     │
└──────────────┘           └──────────────┘
```

**Flow:**
1. Aider sends requests to LiteLLM router (OpenAI-compatible)
2. Router routes to appropriate backend based on model alias
3. FREE models handle 90% of requests
4. Premium APIs only used when explicitly requested

---

## 📚 Documentation

- **[Branching Strategy](docs/BRANCHING_STRATEGY.md)** - Git Flow and collaboration (NEW)
- **[Task Allocation](docs/TASK_ALLOCATION.md)** - Workstreams and assignments (NEW)
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - File map and onboarding (NEW)
- **[Versioning](docs/VERSIONING.md)** - Release strategy (NEW)
- **[Architecture](docs/ARCHITECTURE.md)** - System design and components
- **[Setup Guide](docs/SETUP.md)** - Detailed installation instructions
- **[Workflow](docs/WORKFLOW.md)** - Day-to-day usage patterns
- **[Quick Reference](docs/QuickRef.md)** - Daily commands cheat sheet
- **[Security](docs/SECURITY.md)** - API key management best practices
- **[Contributing](docs/CONTRIBUTING.md)** - Contribution guidelines
- **[ADRs](docs/adr/)** - Architecture decision records
- **[Roadmap](ROADMAP.md)** - Future enhancements (v2.1+)

---

## 🔧 Useful Commands
```bash
# Start/Stop Router
./scripts/start-router.sh
./scripts/stop-router.sh

# Check Status
./scripts/status.sh

# Test All Providers
./scripts/test-providers-simple.sh
./scripts/test-all-providers.sh

# v2.0 Features
lodestar status              # Check health
lodestar costs --dashboard   # Real-time cost TUI
lodestar diff                # Visual AI diff
lodestar run "python app.py" # Self-healing execution

# Test Infrastructure
./scripts/test-lodestar.sh

# Create ADR
./scripts/adr-new.sh "Decision Title"
```

---

## 💰 Cost Comparison

**Before Lodestar (Pure Claude):**
- ~100 requests/day × 30 days = 3,000 requests/month
- Average ~1,000 tokens per request
- Cost: ~$9-15/month
- Usage limits block work

**With Lodestar (90% FREE, 10% Claude):**
- 2,700 requests via FREE DeepSeek (unlimited)
- 300 requests via Claude (complex tasks)
- Cost: ~$0.90-1.50/month
- **Savings: 90%+ with unlimited usage**

---

## 🎯 Use Cases

**Perfect For:**
- Solo developers seeking cost-effective AI coding
- Projects with budget constraints
- Learning AI-assisted development
- Long coding sessions (4-8 hours)
- Experimentation without usage anxiety

**When to Upgrade to Paid:**
- Complex architecture decisions
- Critical bug fixes requiring deep reasoning
- Code reviews of large PRs
- Documentation generation for complex systems

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Submit a pull request

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for details.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

Built with:
- [Aider](https://aider.chat/) - AI pair programming
- [LiteLLM](https://litellm.ai/) - Universal LLM proxy
- [Ollama](https://ollama.ai/) - Local LLM runtime
- [DeepSeek Coder](https://github.com/deepseek-ai/DeepSeek-Coder) - FREE coding model

---

## 📬 Contact

- **GitHub Issues:** Bug reports and feature requests
- **Discussions:** Questions and community chat
- **Project:** https://github.com/zebadee2kk/ProjectLodestar

---

**Status:** v1.0.0 - Production Ready ✅  
**Last Updated:** February 2026

✨ SSH authentication configured
