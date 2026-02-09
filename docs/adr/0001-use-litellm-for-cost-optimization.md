# ADR-0001: Use LiteLLM for Cost Optimization

**Status:** Accepted
**Date:** 2026-02-08
**Deciders:** Lodestar Team

## Context

We need an AI-assisted development environment that:
- Minimizes API costs while maintaining capability
- Provides flexibility to use multiple LLM providers
- Avoids vendor lock-in
- Allows seamless switching between free and paid models

Direct use of Claude API would result in high costs (~$9/month) and usage limits that interrupt workflow.

## Decision

We will use LiteLLM as a routing layer between our coding agent (Aider) and LLM providers.

**Implementation:**
- LiteLLM runs locally on port 4000
- Routes `gpt-3.5-turbo` requests -> Ollama (FREE)
- Routes `claude-*` requests -> Anthropic API (PAID)
- Provides unified OpenAI-compatible API
- Tracks costs and usage

## Consequences

### Positive
- 80-90% cost reduction by defaulting to free local models
- Unlimited usage on local models (no rate limits)
- Easy to add new providers without code changes
- Centralized cost tracking and logging
- Fallback capabilities if one provider fails

### Negative
- Additional component to manage (LiteLLM router)
- Slightly increased latency (routing overhead ~50ms)
- Requires Ollama server to be accessible on network
- Local models may have lower quality than Claude for complex tasks

### Neutral
- OpenAI-compatible API means easy integration with any tool
- Configuration in YAML is straightforward
- Can switch strategies without changing applications

## Implementation Notes

**Configuration file:** `config/litellm_config.yaml`

**Startup script:** `scripts/start-router.sh`

**Model mapping:**
- `gpt-3.5-turbo` -> ollama/deepseek-coder:6.7b (FREE)
- `local-llama` -> ollama/llama3.1:8b (FREE)
- `claude-sonnet` -> anthropic/claude-sonnet-4 (PAID)
- `claude-opus` -> anthropic/claude-opus-4 (EXPENSIVE)

**Future considerations:**
- Add semantic routing based on prompt complexity
- Implement automatic cost prediction
- Add fallback chains for resilience
