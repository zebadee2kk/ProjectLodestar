# ProjectLodestar v2 Architecture Principles

## Core Design Philosophy

**"Modular, Observable, Maintainable"**

Every design decision should optimize for these three goals.

---

## 1. Modular Architecture

### Plugin System

All features are plugins that can be:
- Loaded dynamically
- Configured independently
- Disabled without code changes
- Removed without breaking core

**Anti-pattern:** Monolithic code that couples features together

**Good pattern:**
````python
# Core loads modules dynamically
from modules import load_modules

enabled_modules = load_modules(config)
for module in enabled_modules:
    module.start()
````

### Module Independence

Each module must:
- Have its own configuration
- Manage its own state
- Handle its own errors
- Provide its own tests
- Document its own API

**Dependency Rule:** Modules can depend on core, but not on each other.

---

## 2. Observable Systems

### Logging Levels
````python
DEBUG   # Development details
INFO    # Important events (startup, config changes)
WARNING # Degraded but functional
ERROR   # Something failed but recoverable
CRITICAL # System is broken
````

### Metrics to Track

**Performance:**
- Response time (p50, p95, p99)
- Request rate (per model)
- Error rate (%)
- Queue depth

**Business:**
- Token usage (per model)
- Cost (per model, per day)
- Model switches
- Session duration

**System:**
- CPU usage
- Memory usage
- Disk space
- Network latency

### Health Checks

Every module provides:
````python
def health_check() -> Dict[str, Any]:
    return {
        'status': 'healthy|degraded|down',
        'latency_ms': 123,
        'last_error': None,
        'uptime_seconds': 3600
    }
````

---

## 3. Data Management

### Storage Strategy

**Hot Data** (frequent access):
- In-memory cache
- Redis (if multi-process)
- Fast retrieval (<10ms)

**Warm Data** (daily access):
- SQLite database
- Indexed properly
- Reasonable retrieval (<100ms)

**Cold Data** (archival):
- JSON files
- Compressed
- Slow retrieval OK (>1s)

### Database Design

**Principles:**
- Normalize to 3NF
- Index foreign keys
- Use constraints
- No NULL where avoidable

**Example Schema:**
````sql
CREATE TABLE usage_logs (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    model TEXT NOT NULL,
    tokens_in INTEGER NOT NULL,
    tokens_out INTEGER NOT NULL,
    cost_usd REAL NOT NULL,
    duration_ms INTEGER,
    session_id TEXT,
    INDEX idx_timestamp (timestamp),
    INDEX idx_model (model),
    INDEX idx_session (session_id)
);
````

---

## 4. Error Handling

### Error Hierarchy
````
LodestarError (base)
├── ConfigurationError
├── ModuleError
│   ├── UsageTrackerError
│   ├── LearningModuleError
│   └── HealthMonitorError
├── StorageError
└── NetworkError
````

### Recovery Strategy

1. **Graceful Degradation**
   - Module fails → Disable module, continue
   - DB fails → Log to file, continue
   - Network fails → Retry with backoff

2. **User Communication**
   - Log technical details
   - Show user-friendly message
   - Suggest fix when possible

3. **Automatic Recovery**
   - Retry transient errors
   - Circuit breaker for repeated failures
   - Auto-restart failed modules

---

## 5. Configuration Management

### Layered Configuration
````
1. Defaults (in code)
2. Global config (config/lodestar.yaml)
3. Module config (config/modules/*.yaml)
4. Environment variables
5. CLI arguments
````

Higher layers override lower layers.

### Configuration Schema

**Use pydantic for validation:**
````python
from pydantic import BaseModel, Field

class UsageTrackerConfig(BaseModel):
    enabled: bool = True
    database_path: str = Field(..., description="Path to SQLite DB")
    retention_days: int = Field(90, ge=1, le=365)
    batch_size: int = Field(100, ge=1)
````

**Benefits:**
- Type checking
- Validation
- Documentation
- Defaults

---

## 6. Testing Strategy

### Test Pyramid
````
        E2E (10%)
       /        \
    Integration (20%)
   /              \
  Unit Tests (70%)
````

**Unit Tests:** Fast, isolated, test logic
**Integration Tests:** Test module interactions
**E2E Tests:** Test full workflows

### Test Organization
````
tests/
├── unit/
│   ├── test_usage_tracker.py
│   ├── test_learning_module.py
│   └── test_health_monitor.py
├── integration/
│   ├── test_tracker_with_db.py
│   └── test_module_loading.py
└── e2e/
    ├── test_full_workflow.py
    └── test_module_enable_disable.py
````

### Fixtures

**Use pytest fixtures for common setups:**
````python
@pytest.fixture
def temp_database():
    """Provide temporary test database."""
    db_path = "/tmp/test.db"
    # Setup
    yield db_path
    # Teardown
    os.remove(db_path)
````

---

## 7. Performance Optimization

### Caching Strategy

**What to cache:**
- Model responses (30 min TTL)
- Configuration (reload on change)
- Database queries (short TTL)

**What NOT to cache:**
- Usage statistics (must be real-time)
- Error states
- Security-sensitive data

### Async Operations

**Use async for:**
- Database writes
- API calls
- File I/O
- Logging

**Don't use async for:**
- CPU-bound work
- Simple calculations
- Synchronous APIs

### Batching

**Batch these operations:**
````python
# Bad: One insert per request
for request in requests:
    db.insert(request)

# Good: Batch insert
db.insert_many(requests)
````

---

## 8. Security Principles

### Least Privilege

- Modules get minimum permissions needed
- Database users get minimum grants
- File permissions as restrictive as possible

### Defense in Depth

- Input validation
- Output encoding
- Parameterized queries
- Rate limiting
- Audit logging

### Secrets Management

**Never:**
- Hardcode secrets
- Log secrets
- Commit secrets
- Share secrets

**Always:**
- Environment variables
- Encrypted at rest
- Rotated regularly
- Access controlled

---

## 9. Extensibility

### Plugin Interface
````python
class LodestarPlugin(ABC):
    """Base class for all plugins."""
    
    @abstractmethod
    def start(self) -> None:
        """Start the plugin."""
        
    @abstractmethod
    def stop(self) -> None:
        """Stop the plugin."""
        
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Check plugin health."""
````

### Event System
````python
from typing import Callable, List

class EventBus:
    """Publish-subscribe event system."""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        
    def subscribe(self, event: str, callback: Callable):
        """Subscribe to an event."""
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(callback)
        
    def publish(self, event: str, data: Any):
        """Publish an event."""
        for callback in self._subscribers.get(event, []):
            callback(data)
````

**Usage:**
````python
# Module A publishes
event_bus.publish('request_completed', {
    'model': 'claude-sonnet',
    'tokens': 150,
    'cost': 0.003
})

# Module B subscribes
def track_usage(data):
    db.insert(data)
    
event_bus.subscribe('request_completed', track_usage)
````

---

## 10. Documentation Standards

### Code Documentation

**Every module needs:**
- README.md (overview, usage)
- CHANGELOG.md (version history)
- API.md (if has public API)

**Every class needs:**
- Docstring with purpose
- Attributes documented
- Example usage

**Every function needs:**
- Docstring with purpose
- Parameters documented (with types)
- Return value documented
- Exceptions documented

### ADR Documentation

**When to write ADR:**
- Significant architectural decision
- Technology choice
- Design pattern choice
- Breaking change

**ADR Template:**
````markdown
# ADR-XXXX: Title

Date: YYYY-MM-DD
Status: Proposed|Accepted|Deprecated

## Context
What's the situation?

## Decision
What did we decide?

## Consequences
What are the trade-offs?

## Alternatives Considered
What else did we think about?
````

---

## Checklist for New Features

Before implementing:
- [ ] ADR written
- [ ] Module structure created
- [ ] Configuration schema defined
- [ ] Tests outlined

During implementation:
- [ ] Type hints added
- [ ] Docstrings written
- [ ] Error handling added
- [ ] Logging added

Before merging:
- [ ] Tests passing (80%+ coverage)
- [ ] Linting passing
- [ ] Documentation updated
- [ ] Module can be disabled
- [ ] Performance benchmarked

---

**These principles are living documents. Update them as we learn.**
