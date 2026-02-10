# ProjectLodestar Roadmap

## v1.0.0 - COMPLETE (February 2026)

**Core Infrastructure:**
- [x] Multi-provider routing (8 LLMs)
- [x] FREE tier (DeepSeek + Llama on T600)
- [x] Cost optimization (90% savings)
- [x] Automated testing
- [x] Complete documentation
- [x] SSH authentication

---

## v2.0.0-beta.2 - COMPLETE (February 2026)

### Cost Analytics & Tracking
- [x] Usage dashboard (tokens, cost per project/model) (`lodestar costs --dashboard`)
- [x] Monthly cost reports
- [x] Budget alerts and limits
- [x] CostStorage SQLite persistence with query/cleanup/retention
- [x] CostTracker auto-persists to SQLite (dual-layer: in-memory + durable)
- [ ] Model recommendation engine (cheapest for task)
- **ADR:** 0005 Cost Storage Architecture

### Model Performance Optimization
- [x] Response caching (SQLite, 24-hour TTL) (`lodestar cache`)
- [ ] Model warm-up on router start
- [ ] Connection pooling for T600
- [ ] Reduce GPU model-switch latency
- **ADR:** 0009 Response Caching

### Health Monitoring
- [x] Router health endpoint (`lodestar status`)
- [x] HealthChecker pinging LiteLLM and Ollama endpoints
- [x] Automatic fallback on failure (`FallbackExecutor`)
- [ ] T600 GPU utilization monitoring
- [ ] Provider availability dashboard

### Semantic Routing & Proxy
- [x] SemanticRouter with keyword-based task classification
- [x] RulesEngine with tag-based priority rules
- [x] LodestarProxy full pipeline: classify -> cache -> route -> fallback -> cost -> event
- [x] FallbackExecutor with configurable chains
- **ADR:** 0004 Semantic Task-Based Routing

### Model Tournament
- [x] TournamentRunner side-by-side comparison (`lodestar tournament`)
- [x] Match execution, voting, draw support, leaderboard with win rates

### AI-Enhanced Diff
- [x] Visual diff with syntax highlighting (`lodestar diff`)
- [x] LLM-powered annotations via DiffAnnotator
- [x] Heuristic fallback when LLM unavailable
- **ADR:** 0006 AI Visual Diff

### Self-Healing Agent
- [x] AgentExecutor with LLM retry loop (`lodestar run`)
- [x] Automatic error fixing via proxy
- **ADR:** 0008 Self-Healing Agent

---

## v2.1.0 - IN PROGRESS (Target: Q1 2026)

### Monitoring & Analytics (Claude - Workstream 2)
- [ ] GPU utilization monitoring for T600
- [ ] Provider availability tracking
- [ ] Model recommendation engine
- [ ] Cost analytics enhancements

### Testing & Quality (Claude - Workstream 5)
- [x] 296 tests, 90% code coverage
- [ ] Integration tests with live LiteLLM router
- [ ] Performance benchmarking suite
- [ ] Security review

### Performance (Workstream 1)
- [ ] Model warm-up on router start
- [ ] Connection pooling for T600
- [ ] GPU model-switch optimization

---

## v2.x - Medium Priority

**User Experience**
- [ ] Web UI for configuration (port 8080)
- [ ] Interactive model selector
- [ ] Live token/cost counter in Aider
- [ ] Better error messages

**Multi-Project Support**
- [ ] Per-project model preferences
- [ ] Project-specific cost tracking
- [ ] Shared router across projects
- [ ] Project templates (web, CLI, ML, etc.)

**VSCode Integration**
- [ ] Lodestar VSCode extension
- [ ] Model switcher in status bar
- [ ] Inline AI completions
- [ ] Cost display per file

---

## v3.0.0 - FUTURE VISION

**Advanced Features**
- [ ] RAG support (document Q&A)
- [ ] Model fine-tuning pipeline
- [ ] Multi-model consensus (ask 3, vote)
- [ ] A/B testing framework

**Additional Models**
- [ ] Mistral models via Ollama
- [ ] Qwen2.5 Coder
- [ ] CodeLlama variants
- [ ] Local Stable Diffusion for images

**Collaboration Features**
- [ ] Team sharing (multiple users)
- [ ] Shared model preferences
- [ ] Usage quotas per user
- [ ] Admin dashboard

**DevOps**
- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] CI/CD pipeline integration
- [ ] Automated backups

---

## Decision Framework

**Prioritization Matrix:**

| Feature | Value | Effort | Priority |
|---------|-------|--------|----------|
| Cost Analytics | High | Medium | HIGH |
| Performance | High | Low | HIGH |
| Health Monitoring | High | Medium | HIGH |
| Tournament | Medium | Low | DONE |
| Web UI | Medium | High | Medium |
| Multi-Project | Medium | Medium | Medium |
| VSCode Extension | Medium | High | Medium |
| RAG Support | Low | Very High | Low |
| Docker | Low | High | Low |

---

## Release Schedule

- **v1.0.0:** Feb 8, 2026 - SHIPPED
- **v2.0.0-beta.2:** Feb 10, 2026 - SHIPPED (all core v2 features)
- **v2.1.0:** TBD - Monitoring, analytics, integration testing
- **v2.x Stable:** TBD - Web UI, multi-project

---

**Current Status:** v2.0.0-beta.2 - All core features complete, 296 tests passing
