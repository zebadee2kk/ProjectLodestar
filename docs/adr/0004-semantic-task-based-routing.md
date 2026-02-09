# ADR-0004: Semantic Task-Based Routing

**Status:** Accepted
**Date:** 2026-02-09
**Deciders:** Lodestar Team

## Context

Lodestar v1.0 uses a `simple-shuffle` routing strategy in LiteLLM, meaning
users must manually select models via `--model` flags or `/model` commands.
This works, but has drawbacks:

- Users must know which model is best for each task type
- Easy to accidentally use expensive models for simple tasks
- No automatic cost optimization based on task complexity
- No fallback if a model is unavailable

v2.0 needs intelligent routing that automatically selects the cheapest
capable model for each task, while allowing manual overrides and
graceful fallback when providers fail.

## Decision

Implement a **two-layer routing system**:

### Layer 1: Keyword-Based Task Classification

Classify incoming prompts into task types using keyword matching:

| Task Type        | Keywords                                       | Default Model     |
|------------------|------------------------------------------------|-------------------|
| code_generation  | create, build, implement, add, write, generate | gpt-3.5-turbo     |
| code_review      | review, check, audit, inspect, quality         | claude-sonnet     |
| bug_fix          | fix, bug, error, broken, crash, debug          | gpt-3.5-turbo     |
| architecture     | architect, design, structure, pattern, system   | claude-sonnet     |
| documentation    | document, readme, comment, docstring, explain  | gpt-3.5-turbo     |
| refactor         | refactor, clean, simplify, reorganize          | gpt-3.5-turbo     |
| general          | (fallback)                                     | gpt-3.5-turbo     |

This keeps 90%+ of requests on FREE models, routing to paid models
only for tasks that genuinely benefit from stronger reasoning.

### Layer 2: Tag-Based Rules Engine

For advanced users, a priority-ordered rules engine allows explicit
tag-to-model mappings that override keyword classification:

```python
engine.add_rule(RoutingRule(
    name="critical_to_opus",
    tags=["critical", "production"],
    model="claude-opus",
    priority=100,
))
```

Higher-priority rules are evaluated first. This enables per-project
or per-team customization without changing the core classification.

### Fallback Chains

Every model has a configurable fallback chain for graceful degradation:

```yaml
fallback_chains:
  claude-sonnet:
    - gpt-4o-mini
    - gpt-3.5-turbo
  gpt-3.5-turbo:
    - local-llama
```

If the primary model fails (timeout, rate limit, API error), the
system tries the next model in the chain automatically.

### Manual Override

Users can always force a specific model via `task_override` parameter
or Aider's existing `--model` flag. The router never prevents
explicit model selection.

## Consequences

### Positive
- 90%+ of requests auto-routed to FREE models (cost savings preserved)
- Complex tasks (architecture, review) automatically get stronger models
- Graceful degradation prevents workflow interruption
- Fully configurable without code changes
- Tag-based rules enable per-project customization
- Manual override always available

### Negative
- Keyword classification is heuristic — not 100% accurate
- Misclassification could route simple tasks to expensive models (or vice versa)
- Additional latency (~1ms) for classification step
- Users must learn task types to write effective routing rules

### Neutral
- Can be upgraded to LLM-based classification in future (semantic embedding)
- Rules engine adds configuration complexity for advanced users
- Fallback chains require maintaining model preference lists

## Alternatives Considered

1. **LiteLLM semantic auto-router (embedding-based)** — Uses embeddings to
   classify prompts. More accurate but requires an embedding model to be
   running and adds ~100ms latency per request. Will consider for v2.1
   as an optional upgrade to keyword matching.

2. **User self-selection only** — Current v1 approach. Simple but defeats
   the cost-optimization goal since users forget to switch back to free models.

3. **Cost-based routing** — Always use cheapest model, escalate if response
   quality is poor. Complex to implement (requires quality scoring) and
   would cause poor UX with frequent re-tries.

## Implementation Notes

**Module:** `modules/routing/`
- `router.py` — SemanticRouter class (keyword classification + routing)
- `rules.py` — RulesEngine class (tag-based priority rules)
- `config.yaml` — Default routing rules and fallback chains

**Integration point:** SemanticRouter sits between Aider/user and
LiteLLM. It receives the prompt, classifies the task, selects the
model, then passes through to LiteLLM's existing proxy.

**Testing:** 33 tests covering classification accuracy, routing logic,
fallback chains, rules engine priority, and edge cases.

**Future enhancement:** Replace keyword matching with LiteLLM's
semantic router (embedding-based) for higher accuracy. The
SemanticRouter class is designed to make this a drop-in replacement.
