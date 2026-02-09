# ADR-0007: Cost Transparency Dashboard TUI

Date: 2026-02-09
Status: Proposed

## Context
Developers need real-time visibility into LLM costs to avoid budget overruns. A simple text summary is insufficient for monitoring trends or getting an "at-a-glance" status during long coding sessions.

## Decision
We will implement a **Terminal User Interface (TUI)** dashboard using the `rich` library.

### Design
-   **Header**: Big bold metrics (Total Cost, Projected Savings).
-   **Main View**:
    -   **Cost Table**: Top models by spend.
    -   **Usage Chart**: Bar chart of daily token usage (ascii/rich approximation).
-   **Footer**: Budget health status (Green/Yellow/Red).

### Technical Implementation
-   **Class**: `modules.costs.dashboard.CostDashboard`
-   **Updates**: Polls `CostStorage` every 1-5 seconds.
-   **Interactivity**: Read-only initially; potential for interactive date filtering later.

## Consequences
-   **Pros**: High visibility; "cool factor"; immediate feedback loop on costs.
-   **Cons**: Requires terminal with color support (standard these days).
