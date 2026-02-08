# Use Whole Edit Format for Small Local Models

**Status:** Accepted  
**Date:** 2026-02-08  
**Deciders:** Lodestar Team

## Context

Aider supports multiple edit formats:
- `diff` - SEARCH/REPLACE blocks (complex, requires exact matching)
- `whole` - Complete file rewrites (simpler, more forgiving)
- `udiff` - Unified diff format

Small local models (DeepSeek Coder 6.7B) struggle with the `diff` format because they:
- Forget to include filenames before edit blocks
- Make syntax errors in SEARCH/REPLACE markers
- Cannot maintain exact whitespace matching

Testing showed DeepSeek failed 100% of the time with `diff` format:
```
^^^ Bad/missing filename. The filename must be alone on the line before the opening fence
```

## Decision

Configure Aider to use `edit-format: whole` when using local models.

**Implementation:**
```yaml
# ~/.aider.conf.yml
edit-format: whole  # Works reliably with small models
```

## Consequences

### Positive
- ✅ 100% success rate with DeepSeek Coder
- ✅ Files created on first attempt
- ✅ Simpler prompts required
- ✅ More forgiving of model errors
- ✅ Proven to work in automated tests

### Negative
- ⚠️ Entire files rewritten (more tokens used)
- ⚠️ Can't make surgical edits to large files
- ⚠️ Diffs in git history show full file changes

### Neutral
- For small files (<500 lines), token difference is negligible
- Can still use `diff` format manually when using Claude
- Trade-off: reliability > efficiency for FREE models

## Implementation Notes

**Test results:**
- Before fix: 0% success rate (format errors)
- After fix: 100% success rate (automated test passing)

**When to override:**
- Use `aider --edit-format diff` when working with Claude (handles complex diffs)
- Use default `whole` format for FREE local models

**Alternative considered:**
- Training/fine-tuning local models - rejected (too complex, defeats "avoid complexity" goal)# Use Whole Edit Format for Small Local Models

**Status:** Proposed  
**Date:** 2026-02-08  
**Deciders:** Lodestar Team

## Context

What is the issue we're seeing that motivates this decision?

## Decision

What change are we proposing/making?

## Consequences

### Positive
- 

### Negative
- 

### Neutral
- 

## Implementation Notes

