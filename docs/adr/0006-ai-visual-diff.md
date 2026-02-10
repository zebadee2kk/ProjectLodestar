# ADR-0006: AI-Enhanced Visual Diff

Date: 2026-02-09
Status: Proposed

## Context
Standard git diffs are difficult to parse quickly. While they show *what* changed, they often lack context on *why* it changed or what the impact is. Users want a "smart" view of their changes before committing.

## Decision
We will implement an AI-Enhanced Visual Diff module (`modules/diff`) that:
1.  **Parses** git diffs into structured blocks.
2.  **Annotates** these blocks using an LLM (via `LodestarProxy`) to not just describe the edit, but explain the *intent* (e.g., "Refactored loop for performance").
3.  **Renders** the output using the `rich` library for syntax highlighting and visual separation.

## Technical Details
-   **Annotator**: `DiffAnnotator` will now take a `LodestarProxy` instance.
-   **Prompting**: We will use a specialized system prompt for the "diff-explainer" task, routed to a low-cost model (e.g., Llama 3 or GPT-4o-mini).
-   **Rendering**: `DiffPreview` will return `rich` objects (Console, Syntax, Panel).

## Consequences
-   **Pros**: Significantly improved developer experience; easier-to-catch bugs; auto-documentation of commits.
-   **Cons**: `lodestar diff` command will now wait for network/LLM latency (unless using local model).
-   **Mitigation**: Use local DeepSeek/Llama models for near-instant (and free) diff explanations.
