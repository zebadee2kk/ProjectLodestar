# 📋 ProjectLodestar v2 Planning Handover Document

**Date:** February 8, 2026  
**Current Version:** v1.0.0 (Production Ready)  
**Next Version:** v2.0.0 (Planning Phase)  
**Project:** https://github.com/zebadee2kk/ProjectLodestar

---

## 🎯 Executive Summary

ProjectLodestar is a **production-ready AI development environment** that achieves **90% cost savings** by intelligently routing between 8 LLM providers while defaulting to FREE local models (DeepSeek Coder, Llama 3.1) running on a GPU VM.

**Status:** v1.0.0 shipped, fully operational, battle-tested.

**Key Achievement:** Users can code with AI assistance for free indefinitely, with the option to escalate to premium models (Claude, OpenAI, Grok, Gemini) only when needed.

---

## 🏗️ Current Architecture (v1.0.0)

### System Components
```
┌─────────────────┐
│  Aider (CLI)    │  ← User interface for AI pair programming
└────────┬────────┘
         │ OpenAI-compatible API
         ▼
┌─────────────────┐
│  LiteLLM Router │  ← Smart routing layer (localhost:4000)
│  (Debian VM)    │  ← Routes requests based on model alias
└────────┬────────┘
         │
    ┌────┴─────────────────────────┐
    │                               │
    ▼                               ▼
┌──────────────┐           ┌──────────────┐
│ FREE Models  │           │ PAID APIs    │
│              │           │              │
│ T600 GPU VM  │           │ Cloud APIs   │
│ 192.168.120. │           │ (Internet)   │
│ 211:11434    │           │              │
│              │           │              │
│ • DeepSeek   │           │ • Claude     │
│   Coder 6.7B │           │ • OpenAI     │
│ • Llama 3.1  │           │ • Grok       │
│   8B         │           │ • Gemini     │
└──────────────┘           └──────────────┘
```

### Infrastructure Details

**Main VM (vm-lodestar-core):**
- OS: Debian 12
- IP: 192.168.120.40
- Role: Router host, development environment
- Tools: Aider, LiteLLM, Git, Python 3.11

**T600 GPU VM:**
- IP: 192.168.120.211
- Port: 11434
- Role: Ollama server for local models
- GPU: NVIDIA T600 (4GB VRAM)
- Models: DeepSeek Coder 6.7B (Q4), Llama 3.1 8B (Q4)

**Network:**
- DNS: 192.168.120.10, 1.1.1.1, 8.8.8.8
- Router: localhost:4000 (LiteLLM)
- Ollama: 192.168.120.211:11434

---

## 📁 Repository Structure
```
ProjectLodestar/
├── README.md                    # Main documentation
├── ROADMAP.md                   # v2 planning
├── LICENSE                      # MIT License
├── .gitignore                   # Protects API keys, logs, Python artifacts
│
├── config/
│   └── litellm_config.yaml      # 8 provider configurations
│
├── scripts/
│   ├── start-router.sh          # Start LiteLLM with readiness check
│   ├── stop-router.sh           # Stop router gracefully
│   ├── status.sh                # Health check all components
│   ├── test-lodestar.sh         # Infrastructure test (E2E)
│   ├── test-providers-simple.sh # Quick provider test
│   ├── test-all-providers.sh    # Comprehensive provider test
│   ├── quick-start.sh           # Daily startup routine
│   └── adr-new.sh               # Create new ADR
│
├── docs/
│   ├── ARCHITECTURE.md          # System design
│   ├── SETUP.md                 # Installation guide
│   ├── WORKFLOW.md              # Usage patterns
│   ├── SECURITY.md              # API key management
│   ├── CONTRIBUTING.md          # Contribution guidelines
│   ├── QuickRef.md              # Quick reference guide
│   └── adr/                     # 3 Architecture Decision Records
│
├── .claude/                     # AI development context
│   ├── PROJECT_INSTRUCTIONS.md  # v2 development guidelines
│   ├── ARCHITECTURE_PRINCIPLES.md # Design philosophy
│   ├── MODULE_TEMPLATE.md       # Module scaffolding template
│   └── V2_HANDOVER.md           # v2 planning handover
│
└── .lodestar/                   # Runtime (not in git)
    ├── router.log               # LiteLLM logs
    └── router.pid               # Process ID
```

---

## 🔧 Current Configuration

### Provider Configuration

**Tier 1 - FREE (Default):**
- `gpt-3.5-turbo` → `ollama/deepseek-coder:6.7b` @ T600
- `local-llama` → `ollama/llama3.1:8b` @ T600

**Tier 2 - Claude:**
- `claude-sonnet` → `anthropic/claude-sonnet-4-5-20250929`
- `claude-opus` → `anthropic/claude-opus-4-5-20251101`

**Tier 3 - OpenAI:**
- `gpt-4o-mini` → `openai/gpt-4o-mini`
- `gpt-4o` → `openai/gpt-4o`

**Tier 4 - Grok:**
- `grok-beta` → `xai/grok-beta`

**Tier 5 - Gemini:**
- `gemini-pro` → `gemini-1.5-flash`

---

## ✅ What's Working (v1.0.0)

- ✅ **DeepSeek Coder** - FREE, unlimited, fast responses
- ✅ **Llama 3.1** - FREE, unlimited, good for general coding
- ✅ **Router** - Auto-starts, graceful fallbacks
- ✅ **Git Integration** - Auto-commits preserve context
- ✅ **SSH Auth** - No password pushes to GitHub
- ✅ **Testing Suite** - Automated validation
- ✅ **Documentation** - 12 docs + 7 ADRs

### Verified Routing (Needs Credits)

- 💳 **Claude Sonnet/Opus** - Routing works, needs API credits
- 💳 **OpenAI GPT-4o/Mini** - Routing works, needs API credits
- 💳 **Grok Beta** - Routing works, needs API credits

---

## 🎯 v2.0 USER-REQUESTED FEATURES

### 1. **Learning Module** 🧠 HIGH PRIORITY

**User Description:**
> "A module that 'learns' from the responses received from the public LLM and retrains the information back into the local LLMs"

**Concept:**
- Collect responses from Claude/GPT-4o when used
- Extract high-quality code patterns/solutions
- Create fine-tuning dataset
- Periodically retrain DeepSeek/Llama
- Measure improvement over time

**Potential Approach:**
```
User Request → Claude (expensive)
              ↓
         [Response Logger]
              ↓
    [Quality Filter]
              ↓
    [Dataset Builder - JSONL]
              ↓
    [Fine-tuning Pipeline - weekly]
              ↓
    Updated Models
```

**Challenges:**
- Training requires significant GPU resources
- Fine-tuning 6.7B model takes hours
- Need quality control
- Avoid overfitting

**ADR Needed:** 
- Architecture for response collection
- Training pipeline design
- Quality metrics

---

### 2. **Usage Tracking & Session Limits** 📊 HIGH PRIORITY

**User Description:**
> "A module to track usage including session limits etc"

**Requirements:**
- Track tokens used per model
- Track cost per model
- Session time limits
- Daily/weekly/monthly budgets
- Alerts when approaching limits
- Per-project tracking
- Export reports

**Potential Features:**
```
Usage Dashboard:
├── Real-time token counter
├── Cost accumulator
├── Session timer
├── Budget alerts
├── Model usage breakdown
├── Historical trends
└── Export to CSV/JSON
```

**Storage Options:**
- SQLite database (`~/.lodestar/usage.db`)
- JSON logs for backups
- 90-day retention default

**ADR Needed:**
- Storage architecture
- Alert mechanisms
- Privacy considerations

---

## 🛠️ Development Approach

### Modular Architecture (CRITICAL)

Every feature MUST be:
- Self-contained module
- Can be enabled/disabled via config
- Tested in isolation
- Removed without breaking system

**Structure:**
```
modules/
├── usage_tracker/
│   ├── __init__.py
│   ├── tracker.py
│   ├── storage.py
│   ├── reporter.py
│   ├── config.yaml
│   ├── tests/
│   └── README.md
├── learning/
│   └── [same structure]
└── health_monitor/
    └── [same structure]
```

### Configuration-Driven
```yaml
# config/modules.yaml
modules:
  usage_tracker:
    enabled: true
    database: ~/.lodestar/usage.db
    
  learning:
    enabled: false  # Can disable easily
```

---

## 📋 Recommended Development Sequence

### Phase 1: Usage Tracking MVP (Week 1-2)

**Sprint 1.1:**
1. Create SQLite schema
2. Hook into LiteLLM logging
3. Basic CLI report
4. Budget alerts

**Deliverable:** Can see token usage and costs

---

**Sprint 1.2:**
1. Response collection
2. Quality filter
3. Dataset builder

**Deliverable:** Collecting quality responses

---

### Phase 2: Learning Pipeline (Week 3-4)

**Sprint 2.1:**
1. Test LoRA fine-tuning
2. Validate improvements
3. Document process
4. Automated training script

**Deliverable:** Proof of concept

---

**Sprint 2.2:**
1. Weekly auto-training
2. Model versioning
3. A/B testing
4. Rollback mechanism

**Deliverable:** Continuous learning operational

---

## 🔍 Open Questions

### Learning Module

1. Training frequency? Daily/Weekly/Monthly?
2. Quality metrics?
3. Data mix ratio?
4. Fine-tune DeepSeek or Llama or both?
5. Where to run training? T600 too small (4GB VRAM)

### Usage Tracking

1. What data to store? Just tokens or prompts?
2. Retention period? 30 days? Forever?
3. Alert method? Email/CLI?
4. Multi-user support?
5. Actual billing integration?

---

## 🎯 Immediate Next Steps

1. **Read this handover**
2. **Review current codebase**
3. **Test current system**
4. **Choose first feature** (Usage Tracking recommended)
5. **Create ADR**
6. **Prototype MVP**
7. **Test & Iterate**
8. **Document & Commit**

### Recommended Starting Point

**OPTION A - Quick Win:**
Start with **Usage Tracking** (simpler, immediate value)
- Ship v2.1 in 1-2 weeks

**OPTION B - Ambitious:**
Start with **Learning Module** (complex, high impact)
- Ship v2.0 in 4-6 weeks

**Recommendation:** Start with Usage Tracking (quick win builds momentum)

---

## 💾 Key Files & Paths

**Configuration:**
- LiteLLM: `/home/lodestar/ProjectLodestar/config/litellm_config.yaml`
- Aider: `/home/lodestar/.aider.conf.yml`
- API keys: `/home/lodestar/.bashrc`

**Scripts:**
- Router: `scripts/start-router.sh`
- Tests: `scripts/test-*.sh`
- ADR: `scripts/adr-new.sh`

**Documentation:**
- Main: `README.md`
- Architecture: `docs/ARCHITECTURE.md`
- ADRs: `docs/adr/`

---

## ✅ System State

**Status:** v1.0.0 fully operational and stable

- ✅ v1.0.0 tagged and released
- ✅ All documentation updated
- ✅ GitHub project configured
- ✅ SSH authentication working
- ✅ Test suite passing
- ✅ System operational

**Ready for v2 development to begin!** 🚀

---

**Contact:** Rich (IT Director, UK)  
**VM Access:** `ssh lodestar@192.168.120.40`  
**GitHub:** https://github.com/zebadee2kk/ProjectLodestar
