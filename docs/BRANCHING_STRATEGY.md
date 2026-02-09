# 🌿 Lodestar Branching Strategy

This document defines the branching strategy for Project Lodestar to ensure safe collaboration between human developers and AI agents.

## 1. Core Branches

| Branch | Purpose | Protection |
|--------|---------|------------|
| `main` | Production-ready code. Deployed to production. | **Protected**. PR required. |
| `dev`  | Integration branch for approved features. | **Protected**. PR required. |

## 2. Branch Naming Conventions

All branches must follow this format: `<type>/<description>-<id>`

### Types

-   **Human-led branches:**
    -   `feat/` - New features (e.g., `feat/web-ui`)
    -   `fix/` - Bug fixes (e.g., `fix/router-timeout`)
    -   `docs/` - Documentation updates

-   **AI-led branches (Strict Separation):**
    -   `ai/claude/<description>` - Work led by Claude
    -   `ai/gemini/<description>` - Work led by Gemini
    -   `ai/model/<description>` - Generic AI work

### Examples
-   `ai/claude/refactor-routing-logic`
-   `ai/gemini/health-monitoring-module`
-   `feat/add-user-login`

## 3. Workflow Rules

1.  **Isolation**: AI agents must **ALWAYS** create a new branch for their task. Never push directly to `main` or `dev`.
2.  **Sync**: Before starting, rebase on the latest `main` to ensure up-to-date code.
3.  **Handoffs**: If an AI needs to hand off work to another AI, the new AI should checkout the existing branch (e.g., `ai/claude/feature`) and continue working there, OR create a sub-branch `ai/gemini/feature-refinement`.
4.  **PRs**: All work merges to `main` via Pull Request. Code review (by human or another AI) is required.

## 4. Conflict Resolution

-   If `ai/claude` and `ai/gemini` touch the same files, the **Human Owner** decides priority.
-   Prefer modular development (new files/folders) over modifying existing core files to minimize conflicts.
