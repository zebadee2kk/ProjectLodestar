# ADR-0009: Response Caching Strategy

Date: 2026-02-09
Status: Proposed

## Context
Developers often run the same prompt multiple times during testing (e.g., `lodestar route "test"`), or ask similar coding questions. Each call costs money and takes time (1-5s).

## Decision
We will implement a **Local Response Cache**.

### Strategy
-   **Storage**: File-based SQLite database (`.lodestar/cache.db`) or simple JSON for MVP. *Decision: SQLite for concurrency/reliability.*
-   **Key**: SHA256 hash of `(model, system_prompt, user_prompt, temperature)`.
-   **TTL**: Default 24 hours.
-   **Eviction**: LRU (Least Recently Used) if size > 100MB.

### Implementation
-   `CacheManager`: Handles get/set operations.
-   Integration: Inside `LodestarProxy.handle_request`, before calling `litellm`.

## Consequences
-   **Pros**: Instant responses for repeated queries; Zero cost for repeats.
-   **Cons**: Disk usage (minor); Potential for stale answers if external world changes (unlikely for coding tasks).
