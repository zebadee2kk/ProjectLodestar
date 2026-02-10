# Module Design Template

Use this template when designing any new module for ProjectLodestar v2.

---

## Module Name: [NAME]

**Version:** 1.0.0  
**Author:** ProjectLodestar Team  
**Date:** [DATE]

---

## 1. Purpose

**What problem does this solve?**

[1-2 paragraphs explaining the need]

**Who benefits?**

- User personas
- Use cases

---

## 2. Requirements

### Functional Requirements

**Must Have:**
- [ ] Requirement 1
- [ ] Requirement 2

**Should Have:**
- [ ] Requirement 3

**Nice to Have:**
- [ ] Requirement 4

### Non-Functional Requirements

**Performance:**
- Latency: < Xms
- Throughput: Y requests/sec
- Memory: < Z MB

**Reliability:**
- Uptime: 99.9%
- Data retention: X days
- Recovery time: < Y minutes

**Security:**
- Authentication: Yes/No
- Encryption: At rest/In transit
- Audit logging: Yes/No

---

## 3. Architecture

### Component Diagram
````
┌─────────────────┐
│   Module Core   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│Storage│ │Reporter│
└───────┘ └────────┘
````

### Data Flow
````
Input → Validation → Processing → Storage → Output
````

### Dependencies

**Internal:**
- Core: LiteLLM router
- Shared: Event bus, config loader

**External:**
- SQLite (storage)
- Pytest (testing)

---

## 4. API Design

### Public Interface
````python
class ModuleName:
    """Module description."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize module."""
        
    def start(self) -> None:
        """Start module operation."""
        
    def stop(self) -> None:
        """Stop module gracefully."""
        
    def process(self, data: Any) -> Result:
        """Main processing function."""
        
    def health_check(self) -> Health:
        """Check module health."""
````

### Configuration Schema
````yaml
module_name:
  enabled: true
  setting_1: value
  setting_2: value
````

---

## 5. Data Model

### Database Schema
````sql
CREATE TABLE table_name (
    id INTEGER PRIMARY KEY,
    field_1 TYPE NOT NULL,
    field_2 TYPE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_field_1 (field_1)
);
````

### Data Types
````python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DataModel:
    field_1: str
    field_2: int
    created_at: datetime
````

---

## 6. Error Handling

### Error Types
````python
class ModuleError(LodestarError):
    """Base error for this module."""

class ValidationError(ModuleError):
    """Invalid input data."""
    
class StorageError(ModuleError):
    """Database operation failed."""
````

### Recovery Strategy

**Error → Action:**
- ValidationError → Return error to user
- StorageError → Retry 3x, then alert
- NetworkError → Circuit breaker pattern

---

## 7. Testing Strategy

### Test Coverage

**Unit Tests:** (70%)
- Core logic
- Validation
- Calculations

**Integration Tests:** (20%)
- Database operations
- Module interactions

**E2E Tests:** (10%)
- Full workflows
- Enable/disable

### Test Cases
````python
def test_module_initialization():
    """Test module initializes correctly."""
    
def test_process_valid_input():
    """Test processing with valid data."""
    
def test_process_invalid_input():
    """Test error handling."""
    
def test_health_check():
    """Test health check returns status."""
````

---

## 8. Performance Considerations

### Bottlenecks

**Potential issues:**
- Database writes (solve with batching)
- Network calls (solve with caching)
- CPU-intensive work (solve with async)

### Optimization Strategy

1. Measure baseline
2. Identify bottleneck
3. Optimize
4. Measure improvement
5. Repeat

### Benchmarks

**Target metrics:**
- Response time: < 100ms p95
- Throughput: > 1000 req/sec
- Memory: < 500MB

---

## 9. Monitoring & Observability

### Metrics to Track

**Business Metrics:**
- Feature usage count
- User satisfaction (if applicable)

**Technical Metrics:**
- Request count
- Error rate
- Response time
- Resource usage

### Logging
````python
logger.info("Module started", extra={
    'module': 'module_name',
    'version': '1.0.0'
})

logger.error("Processing failed", extra={
    'error': str(e),
    'input': sanitized_input
})
````

### Alerts

**Critical:**
- Module down
- Data loss
- Security breach

**Warning:**
- High error rate (>5%)
- Slow response (>1s p95)
- Low disk space

---

## 10. Deployment

### Installation
````bash
# Install dependencies
pip install -r modules/module_name/requirements.txt

# Run database migrations
python modules/module_name/migrate.py

# Enable module
# Edit config/modules.yaml:
# module_name:
#   enabled: true
````

### Configuration
````yaml
# config/modules/module_name.yaml
module_name:
  enabled: true
  database_path: ~/.lodestar/module.db
  log_level: INFO
  feature_flags:
    experimental_feature: false
````

### Verification
````bash
# Test module
pytest modules/module_name/tests/

# Check health
./scripts/check-module-health.sh module_name
````

---

## 11. Documentation

### README.md

- [ ] Overview
- [ ] Installation
- [ ] Configuration
- [ ] Usage examples
- [ ] API reference
- [ ] Troubleshooting

### CHANGELOG.md
````markdown
# Changelog

## [1.0.0] - YYYY-MM-DD
### Added
- Initial release
- Feature X
- Feature Y

### Changed
- Improvement Z

### Fixed
- Bug #123
````

---

## 12. Future Enhancements

### v1.1 Roadmap

- [ ] Enhancement 1
- [ ] Enhancement 2

### Known Limitations

- Limitation 1 (workaround: X)
- Limitation 2 (will fix in v2.0)

---

## 13. Review Checklist

Before submitting module:

**Design:**
- [ ] ADR written and approved
- [ ] Architecture diagram created
- [ ] API designed

**Implementation:**
- [ ] Code complete
- [ ] Type hints added
- [ ] Docstrings written
- [ ] Error handling added

**Testing:**
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Coverage > 80%

**Documentation:**
- [ ] README complete
- [ ] CHANGELOG updated
- [ ] API docs generated

**Integration:**
- [ ] Module loads successfully
- [ ] Can be enabled/disabled
- [ ] No conflicts with other modules
- [ ] Performance acceptable

---

**Template Version:** 1.0.0  
**Last Updated:** 2026-02-08
