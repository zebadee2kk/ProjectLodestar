# Changelog

All notable changes to ProjectLodestar will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Model warm-up on router start
- Connection pooling for T600
- CSV/JSON export from cost storage
- LLM-powered diff annotations (upgrade from heuristic)

## [2.1.0-alpha.2] - 2026-02-10

### Added
- **Health:** Remote GPU monitoring support via SSH for distributed setups.
- **Config:** `lodestar config` command for interactive setup of local settings and credentials.
- **Config:** Git-ignored `.lodestar/config.yaml` vault for secure credential storage.
- **Docs:** Updated architecture diagrams and quick reference with v2 features.

### Fixed
- **CLI:** Corrected Rich markup tags in stability command.
- **CLI:** Fixed argument collision in `run` command using `argparse.REMAINDER`.
- **Agent:** Robust heuristic extraction of shell commands from LLM responses (prevents conversational text execution).
- **Agent:** Fixed `ModelResponse` object serialization and `strip()` bugs in executor.
- **Health:** Graceful handling of SSH failures (BatchMode) and silenced connection warnings in dashboard.

## [2.0.0-alpha.3] - 2026-02-09

### Added
- **Tournament:** `TournamentRunner` — side-by-side model comparison with
  match execution, voting, draw support, leaderboard with win rates, and
  formatted terminal output
- **Cost storage:** `query_by_model()`, `query_by_date_range()`, `cleanup()`
  retention purge, and `record_count()` on CostStorage
- **Cost persistence:** CostTracker now auto-persists to SQLite when
  `database_path` is configured — dual-layer (in-memory + durable)
- **Proxy:** `handle_request()` accepts `tokens_in`/`tokens_out` params
  for real token count forwarding from LiteLLM callbacks
- **CLI:** `lodestar tournament "prompt" model1 model2` command

### Fixed
- CostStorage date range queries now use SQLite-compatible timestamp format

### Metrics
- 182 tests, 98% code coverage (+49 tests from alpha.2)
- 6 new files, ~350 lines of new code

## [2.1.0-alpha.1] - 2026-02-09

### Added
- **Cache:** `lodestar cache` CLI commands for cache management
- **Cache:** SQLite-based response caching with 24-hour TTL
- **Cache:** Automatic cache hit/miss tracking
- **Docs:** Comprehensive branching strategy (Git Flow)
- **Docs:** Task allocation with 7 parallel workstreams
- **Docs:** Versioning strategy document
- **Docs:** Developer onboarding guide
- **Docs:** ADR-0009 for response caching architecture

### Changed
- Integrated response caching into `LodestarProxy`
- Updated CLI to include cache commands
- Established `develop` branch as integration point
- Merged all v2.0-beta.1 features into `develop`

### Fixed
- Missing `cmd_costs` function in CLI
- Cache serialization bug with RequestResult objects
- Test isolation issues with tmp_path

## [2.0.0-beta.1] - 2026-02-09

### Added
- **Health:** `lodestar status` CLI command for module health verification.
- **Costs:** `lodestar costs --dashboard` interactive TUI for real-time cost tracking using `rich`.
- **Diff:** `lodestar diff` visual diff tool with syntax highlighting and AI-powered explanations.
- **Agent:** `lodestar run <cmd>` self-healing command executor that automatically fixes errors using an LLM loop.
- **Deps:** Added `rich` dependency for TUI and formatting.

### Changed
- All modules now integrated via `LodestarProxy`.
- Unified `modules.cli` entry point.

## [2.0.0-alpha.2] - 2026-02-09

### Added
- **Proxy:** `LodestarProxy` integration layer — full pipeline from
  classification -> routing -> fallback -> cost recording -> event publish
- **Routing:** `FallbackExecutor` — automatic retry with fallback chain on
  model failure; tries each model in order until one succeeds
- **CLI:** `python -m modules.cli` with three commands:
  - `lodestar costs` — formatted cost summary report
  - `lodestar route "prompt"` — test routing decision for a prompt
  - `lodestar status` — module health check
- **Docs:** ADR-0005 Cost Storage Architecture

### Metrics
- 133 tests, 98% code coverage (+28 tests from alpha.1)
- 5 new files, ~400 lines of new code

## [2.0.0-alpha.1] - 2026-02-09

### Added
- **Module system:** `LodestarPlugin` ABC and `EventBus` pub-sub (`modules/base.py`)
- **Routing module:** `SemanticRouter` with keyword-based task classification
- **Routing module:** `RulesEngine` with tag-based priority rules
- **Routing module:** Configurable fallback chains per model
- **Cost module:** `CostTracker` with per-request cost calculation
- **Cost module:** `CostStorage` SQLite persistence backend
- **Cost module:** CLI reporter with formatted cost summaries
- **Cost module:** Budget alerts and savings-vs-baseline tracking
- **Diff module:** `DiffPreview` unified diff parser with structured blocks
- **Diff module:** `DiffAnnotator` heuristic annotation engine with confidence scores
- **Config:** `config/modules.yaml` central module enable/disable
- **Config:** Per-module `config.yaml` files with defaults
- **Tooling:** `pyproject.toml` with pytest + coverage configuration
- **Docs:** ADR-0004 Semantic Task-Based Routing

### Metrics
- 105 tests, 98% code coverage
- 30 new files, 1,937 lines of code

## [1.0.0] - 2026-02-08

### Added
- Multi-provider LLM routing via LiteLLM (8 providers)
- FREE tier: DeepSeek Coder 6.7B + Llama 3.1 8B via Ollama on T600 GPU
- PAID tier: Claude, OpenAI, Grok, Gemini routing
- Shell scripts for router management (start, stop, status)
- Automated provider testing suite
- Git auto-commit integration via Aider
- SSH authentication for GitHub
- Complete documentation (12 docs, 3 ADRs)

### Infrastructure
- Main VM: Debian 12, Python 3.11, LiteLLM 1.75.0
- T600 GPU VM: Ollama with quantized local models
- Aider 0.86.1 as coding interface
