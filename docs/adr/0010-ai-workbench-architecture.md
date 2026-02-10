# ADR 0010: AI Workbench Architecture

Status: Proposed
Date: 2026-02-10

## Context

Current AI tools are often stateless or have limited context windows. Developers need a persistent project "brain" that maintains state across sessions, organizes project knowledge, and routes tasks intelligently based on this persistent context. `ProjectLodestar` currently excels at routing but lacks a persistent state and a unified way to manage project-wide knowledge.

## Decision

We will implement the **AI Workbench** as a core feature of ProjectLodestar. The Workbench will be composed of four sub-modules:

1.  **Memory Module (`modules/memory`)**:
    -   Integrates with a vector database (e.g., Qdrant).
    -   Stores embeddings of chat history, task decisions, and project milestones.
    -   Provides retrieval-augmented generation (RAG) capabilities.

2.  **Context Module (`modules/context`)**:
    -   Manages persistent session state.
    -   Handles context assembly (merging short-term chat context with long-term memory retrieval).
    -   Allows "pausing" and "resuming" work sessions.

3.  **Knowledge Module (`modules/knowledge`)**:
    -   Responsible for indexing the repository (code and documentation).
    -   Automatically keep embeddings up-to-date with git changes.
    -   Provides semantic search across the codebase.

4.  **Workbench Orchestrator (`modules/workbench`)**:
    -   The main entry point for persistent AI work.
    -   Works alongside `LodestarProxy` to leverage semantic routing while maintaining state.
    -   Exposes a CLI interface for workbench operations (e.g., `lodestar workbench search`, `lodestar workbench status`).

## Consequences

-   **Complexity**: Increased complexity in the modular system.
-   **Dependencies**: Requires a vector database (default to a local Qdrant instance via Docker or local binary).
-   **Resource Usage**: Indexing and vector search will consume additional CPU/RAM.
-   **Enhanced Capabilities**: Enables true "project brain" functionality, allowing the AI to "remember" previous decisions and understand the whole codebase semantically.

## Implementation Details

-   Modules will follow the `LodestarPlugin` base class.
-   Communication between modules will use the `EventBus`.
-   Configuration will be integrated into `config/modules.yaml`.
-   Persistence will use SQLite for metadata and Qdrant for vector embeddings.
