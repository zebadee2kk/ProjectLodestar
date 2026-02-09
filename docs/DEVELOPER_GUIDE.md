# Developer Onboarding Guide

**Project**: Lodestar  
**Last Updated**: 2026-02-09  
**For**: Human Developers & AI Agents

---

## 🎯 Quick Start (5 Minutes)

### 1. Clone and Setup
```bash
git clone https://github.com/zebadee2kk/ProjectLodestar.git
cd ProjectLodestar

# Checkout develop branch
git checkout develop
git pull origin develop

# Install dependencies
pip install -r requirements.txt  # or use pyproject.toml
pip install -e .  # Install in editable mode
```

### 2. Run Tests
```bash
# Run all tests
pytest modules/tests/ -v

# Should see: 41 passed ✅
```

### 3. Create Your Branch
```bash
# For AI agents
git checkout -b ai/<agent-name>/<feature-name>

# For humans
git checkout -b human/<your-name>/<feature-name>
```

### 4. Start Working!
- Check `docs/TASK_ALLOCATION.md` for your workstream
- Read relevant code in `modules/`
- Make changes, test, commit, push

---

## 📚 Essential Documentation

### Must Read (Priority Order)

1. **`README.md`** - Project overview, features, quick start
2. **`docs/BRANCHING_STRATEGY.md`** - How to use Git
3. **`docs/TASK_ALLOCATION.md`** - What to work on
4. **`docs/VERSIONING.md`** - Version strategy
5. **`CHANGELOG.md`** - What's changed
6. **`ROADMAP.md`** - Future plans

### Reference Docs

7. **`docs/ARCHITECTURE.md`** - System design
8. **`docs/CONTRIBUTING.md`** - Contribution guidelines
9. **`docs/SETUP.md`** - Detailed setup
10. **`docs/WORKFLOW.md`** - Day-to-day usage
11. **`docs/adr/`** - Architecture decisions

---

## 📁 Project Structure

```
ProjectLodestar/
├── 📄 README.md                    # Project overview
├── 📄 CHANGELOG.md                 # Version history
├── 📄 ROADMAP.md                   # Future plans
├── 📄 LICENSE                      # MIT License
├── 📄 pyproject.toml               # Python project config
├── 📄 .gitignore                   # Git ignore rules
│
├── 📂 modules/                     # Main codebase
│   ├── 📄 __init__.py              # Package init
│   ├── 📄 base.py                  # Base classes (EventBus, Plugin)
│   ├── 📄 cli.py                   # CLI entry point
│   │
│   ├── 📂 routing/                 # Routing module
│   │   ├── 📄 router.py            # Semantic router
│   │   ├── 📄 proxy.py             # LodestarProxy (main integration)
│   │   ├── 📄 fallback.py          # Fallback executor
│   │   ├── 📄 rules.py             # Routing rules engine
│   │   ├── 📄 cache.py             # Response cache manager
│   │   └── 📄 config.yaml          # Routing configuration
│   │
│   ├── 📂 costs/                   # Cost tracking module
│   │   ├── 📄 tracker.py           # Cost tracker
│   │   ├── 📄 storage.py           # SQLite storage
│   │   ├── 📄 reporter.py          # CLI reporter
│   │   ├── 📄 dashboard.py         # TUI dashboard
│   │   └── 📄 config.yaml          # Cost configuration
│   │
│   ├── 📂 diff/                    # Visual diff module
│   │   ├── 📄 preview.py           # Diff parser/renderer
│   │   ├── 📄 annotator.py         # AI annotation
│   │   └── 📄 config.yaml          # Diff configuration
│   │
│   ├── 📂 agent/                   # Self-healing agent
│   │   └── 📄 executor.py          # Command executor
│   │
│   ├── 📂 health/                  # Health monitoring
│   │   └── 📄 checker.py           # Health checker
│   │
│   └── 📂 tests/                   # Test suite
│       ├── 📄 test_base.py         # Base class tests
│       ├── 📄 test_cli.py          # CLI tests
│       ├── 📄 test_cache.py        # Cache tests
│       ├── 📄 test_agent.py        # Agent tests
│       ├── 📄 test_dashboard.py    # Dashboard tests
│       ├── 📄 test_diff.py         # Diff tests
│       └── 📄 test_health.py       # Health tests
│
├── 📂 config/                      # Configuration files
│   └── 📄 modules.yaml             # Module enable/disable
│
├── 📂 scripts/                     # Utility scripts
│   ├── 📄 start-router.sh          # Start LiteLLM router
│   ├── 📄 status.sh                # Check router status
│   ├── 📄 quick-start.sh           # Quick start script
│   ├── 📄 test-lodestar.sh         # Test Lodestar modules
│   ├── 📄 test-providers-simple.sh # Test providers
│   ├── 📄 test-all-providers.sh    # Comprehensive provider test
│   ├── 📄 test-models.sh           # Test specific models
│   └── 📄 adr-new.sh               # Create new ADR
│
└── 📂 docs/                        # Documentation
    ├── 📄 ARCHITECTURE.md          # System architecture
    ├── 📄 SETUP.md                 # Setup guide
    ├── 📄 WORKFLOW.md              # Usage workflow
    ├── 📄 CONTRIBUTING.md          # Contribution guide
    ├── 📄 SECURITY.md              # Security practices
    ├── 📄 QuickRef.md              # Quick reference
    ├── 📄 BRANCHING_STRATEGY.md    # Git branching
    ├── 📄 TASK_ALLOCATION.md       # Work distribution
    ├── 📄 VERSIONING.md            # Version strategy
    ├── 📄 SETUP_COMPLETE.md        # Setup status
    ├── 📄 PROJECT_STATUS_*.md      # Status snapshots
    ├── 📄 V2_GEMINI_HANDOVER.md    # Gemini handover
    │
    └── 📂 adr/                     # Architecture Decision Records
        ├── 📄 0001-use-litellm-for-cost-optimization.md
        ├── 📄 0002-use-whole-edit-format-for-small-local-models.md
        ├── 📄 0003-multi-provider-routing-fully-operational.md
        ├── 📄 0004-semantic-task-based-routing.md
        ├── 📄 0005-cost-storage-architecture.md
        ├── 📄 0006-ai-visual-diff.md
        ├── 📄 0007-cost-dashboard.md
        ├── 📄 0008-self-healing-agent.md
        └── 📄 0009-response-caching.md
```

---

## 🗺️ File Ownership Map

### Workstream 1: Performance Optimization (Gemini)
**Files to modify**:
- `modules/routing/router.py` - Add warm-up logic
- `modules/routing/proxy.py` - Add connection pooling
- `modules/routing/cache.py` - Enhance caching
- **New**: `modules/routing/warmup.py` - Model warm-up
- **New**: `modules/routing/connection_pool.py` - Connection pool
- **Tests**: `modules/tests/test_warmup.py`, `test_pool.py`

**Scripts to create**:
- `scripts/warmup-models.sh` - Warm-up script

**Docs to update**:
- `docs/adr/0010-model-warmup.md` - New ADR
- `CHANGELOG.md` - Add features

### Workstream 2: Monitoring & Analytics (Claude)
**Files to modify**:
- `modules/health/checker.py` - Add GPU monitoring
- `modules/costs/tracker.py` - Add recommendations
- `modules/costs/dashboard.py` - Add provider status
- **New**: `modules/health/gpu_monitor.py` - GPU metrics
- **New**: `modules/costs/recommender.py` - Model recommendations
- **New**: `modules/health/provider_monitor.py` - Provider monitoring
- **Tests**: `modules/tests/test_gpu_monitor.py`, etc.

**Scripts to create**:
- `scripts/monitor-gpu.sh` - GPU monitoring script

**Docs to update**:
- `docs/adr/0011-gpu-monitoring.md` - New ADR
- `CHANGELOG.md` - Add features

### Workstream 3: User Experience (Richard)
**Files to modify**:
- `modules/cli.py` - Add interactive mode
- **New**: `modules/web/` - Entire web UI directory
  - `modules/web/server.py` - Flask/FastAPI server
  - `modules/web/templates/` - HTML templates
  - `modules/web/static/` - CSS/JS assets
- **Tests**: `modules/tests/test_web.py`

**Scripts to create**:
- `scripts/start-web-ui.sh` - Start web server

**Docs to update**:
- `docs/WEB_UI.md` - New doc
- `README.md` - Add web UI section
- `CHANGELOG.md` - Add features

### Workstream 4: Multi-Project (Gemini)
**Files to modify**:
- `modules/routing/proxy.py` - Add project context
- `modules/costs/tracker.py` - Add project tagging
- `modules/costs/storage.py` - Add project field
- **New**: `modules/projects/` - Entire directory
  - `modules/projects/config.py` - Project config
  - `modules/projects/manager.py` - Project manager
  - `modules/projects/templates/` - Project templates
- **Tests**: `modules/tests/test_projects.py`

**Docs to update**:
- `docs/adr/0012-multi-project.md` - New ADR
- `docs/MULTI_PROJECT.md` - New guide
- `CHANGELOG.md` - Add features

### Workstream 5: Testing & Quality (Claude)
**Files to modify**:
- All test files - Improve coverage
- **New**: `modules/tests/integration/` - Integration tests
- **New**: `modules/tests/benchmarks/` - Benchmarks
- `pyproject.toml` - Update coverage config

**Scripts to create**:
- `scripts/run-integration-tests.sh`
- `scripts/run-benchmarks.sh`
- `scripts/coverage-report.sh`

**Docs to update**:
- `docs/TESTING.md` - New guide
- `CHANGELOG.md` - Add improvements

### Workstream 6: DevOps (Richard)
**Files to create**:
- `Dockerfile` - Docker image
- `docker-compose.yml` - Docker Compose
- `.github/workflows/` - CI/CD pipelines
  - `ci.yml` - Continuous integration
  - `release.yml` - Release automation
- `deploy/` - Deployment scripts
- `monitoring/` - Monitoring configs

**Scripts to create**:
- `scripts/docker-build.sh`
- `scripts/deploy.sh`
- `scripts/rollback.sh`

**Docs to update**:
- `docs/DEPLOYMENT.md` - New guide
- `docs/DOCKER.md` - Docker guide
- `README.md` - Add deployment section

### Workstream 7: Documentation (Richard)
**Files to update**:
- `README.md` - Keep current
- `ROADMAP.md` - Update progress
- `CHANGELOG.md` - Maintain history
- **New**: `docs/API.md` - API reference
- **New**: `docs/TUTORIALS.md` - Tutorials
- **New**: `.github/ISSUE_TEMPLATE/` - Issue templates
- **New**: `CODE_OF_CONDUCT.md` - Code of conduct

**Docs to create**:
- `docs/FAQ.md` - Frequently asked questions
- `docs/TROUBLESHOOTING.md` - Common issues

---

## 🔧 Key Scripts Reference

### Development Scripts

#### `scripts/start-router.sh`
**Purpose**: Start LiteLLM router  
**Usage**: `./scripts/start-router.sh`  
**When**: Before testing with real LLM

#### `scripts/status.sh`
**Purpose**: Check router status  
**Usage**: `./scripts/status.sh`  
**When**: Verify router is running

#### `scripts/test-lodestar.sh`
**Purpose**: Test Lodestar modules  
**Usage**: `./scripts/test-lodestar.sh`  
**When**: After making changes

#### `scripts/quick-start.sh`
**Purpose**: Quick setup and start  
**Usage**: `./scripts/quick-start.sh`  
**When**: First time setup

#### `scripts/adr-new.sh`
**Purpose**: Create new ADR  
**Usage**: `./scripts/adr-new.sh "Decision Title"`  
**When**: Making architectural decision

### Testing Scripts

#### `pytest modules/tests/ -v`
**Purpose**: Run all unit tests  
**When**: Before every commit

#### `pytest modules/tests/ --cov=modules`
**Purpose**: Run tests with coverage  
**When**: Checking test coverage

#### `scripts/test-providers-simple.sh`
**Purpose**: Test provider connectivity  
**When**: Verifying provider setup

---

## 🎓 Common Tasks

### Task: Add a New CLI Command

**Files to modify**:
1. `modules/cli.py` - Add command function and parser
2. `modules/tests/test_cli.py` - Add tests
3. `CHANGELOG.md` - Document addition

**Steps**:
```python
# 1. Add command function in cli.py
def cmd_mycommand(proxy: LodestarProxy, args: argparse.Namespace) -> None:
    """My new command."""
    print("Hello from my command!")

# 2. Add parser in build_parser()
mycommand_parser = subparsers.add_parser("mycommand", help="My command")
mycommand_parser.add_argument("--option", help="An option")

# 3. Add to commands dict in main()
commands = {
    # ... existing commands
    "mycommand": cmd_mycommand,
}

# 4. Add test
def test_mycommand_runs(self):
    main(["mycommand"])
    # Assert expected behavior
```

### Task: Add a New Module

**Files to create**:
1. `modules/mymodule/` - New directory
2. `modules/mymodule/__init__.py` - Package init
3. `modules/mymodule/myfeature.py` - Feature implementation
4. `modules/mymodule/config.yaml` - Configuration
5. `modules/tests/test_mymodule.py` - Tests
6. `docs/adr/00XX-mymodule.md` - ADR

**Steps**:
```bash
# 1. Create directory structure
mkdir -p modules/mymodule
touch modules/mymodule/__init__.py
touch modules/mymodule/myfeature.py
touch modules/mymodule/config.yaml

# 2. Implement feature (see base.py for plugin pattern)
# 3. Add tests
# 4. Create ADR
./scripts/adr-new.sh "My Module Decision"

# 5. Update CHANGELOG
# 6. Commit and push
```

### Task: Fix a Bug

**Process**:
```bash
# 1. Create hotfix branch (if critical)
git checkout main
git checkout -b hotfix/123-bug-description

# OR create feature branch (if not critical)
git checkout develop
git checkout -b ai/gemini/fix-bug-description

# 2. Fix the bug
# ... edit files ...

# 3. Add test for regression
# ... add test ...

# 4. Run tests
pytest modules/tests/ -v

# 5. Commit
git add .
git commit -m "fix(scope): description of fix

Fixes #123"

# 6. Push and create PR
git push origin <branch-name>
```

### Task: Update Documentation

**Files to update**:
- `README.md` - For user-facing changes
- `docs/ARCHITECTURE.md` - For design changes
- `CHANGELOG.md` - For all changes
- `docs/adr/` - For decisions

**Process**:
```bash
# 1. Update relevant docs
# 2. Check for broken links
# 3. Verify examples work
# 4. Commit
git add docs/
git commit -m "docs: update XYZ documentation"
```

---

## 🧪 Testing Guide

### Running Tests

```bash
# All tests
pytest modules/tests/ -v

# Specific test file
pytest modules/tests/test_cache.py -v

# Specific test
pytest modules/tests/test_cache.py::TestCacheManager::test_set_get -v

# With coverage
pytest modules/tests/ --cov=modules --cov-report=html

# Integration tests (when available)
pytest modules/tests/integration/ -v
```

### Writing Tests

**Template**:
```python
import pytest
from modules.mymodule import MyFeature

class TestMyFeature:
    @pytest.fixture
    def feature(self):
        """Create feature instance for testing."""
        return MyFeature(config={"enabled": True})
    
    def test_basic_functionality(self, feature):
        """Test basic feature works."""
        result = feature.do_something()
        assert result == expected_value
    
    def test_error_handling(self, feature):
        """Test error handling."""
        with pytest.raises(ValueError):
            feature.do_invalid_thing()
```

---

## 🔍 Debugging Tips

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Use Debugger
```python
import pdb; pdb.set_trace()  # Set breakpoint
```

### Check Module Health
```bash
lodestar status
```

### View Cache Stats
```bash
lodestar cache
```

### Test Routing
```bash
lodestar route "your test prompt"
```

---

## 📊 Code Style Guide

### Python
- Follow PEP 8
- Use type hints
- Write docstrings
- Max line length: 100 characters

### Commits
- Format: `type(scope): description`
- Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`
- Reference issues: `Fixes #123`

### Documentation
- Use Markdown
- Include code examples
- Keep concise
- Update TOC if needed

---

## 🚨 Common Pitfalls

### ❌ Don't
- Commit directly to `main` or `develop`
- Skip tests
- Use hardcoded paths
- Ignore lint errors
- Leave TODO comments without issues

### ✅ Do
- Work in feature branches
- Run tests before pushing
- Use configuration files
- Fix lint errors
- Create issues for TODOs

---

## 📞 Getting Help

### Documentation
1. Check this guide first
2. Read relevant docs in `docs/`
3. Check ADRs for decisions
4. Read code comments

### Community
1. GitHub Discussions - Questions
2. GitHub Issues - Bugs/Features
3. Project maintainer - Escalations

---

## ✅ Onboarding Checklist

- [ ] Read README.md
- [ ] Read BRANCHING_STRATEGY.md
- [ ] Read TASK_ALLOCATION.md
- [ ] Clone repository
- [ ] Checkout `develop` branch
- [ ] Install dependencies
- [ ] Run tests (41 should pass)
- [ ] Create your feature branch
- [ ] Read code in your workstream
- [ ] Make first commit
- [ ] Push and create PR

---

**Welcome to Project Lodestar! Happy coding! 🚀**
