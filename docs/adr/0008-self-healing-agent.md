# ADR-0008: Self-Healing Agent Execution

Date: 2026-02-09
Status: Proposed

## Context
In an autonomous coding environment, tools (compilers, linters, scripts) often fail due to trivial issues like missing dependencies, syntax errors, or environmental misconfiguration. Stopping execution requires human intervention, breaking the agent's flow.

## Decision
We will implement a **Self-Healing Execution Loop** in `modules/agent/executor.py`.

### The Loop
1.  **Execute**: Run the requested command.
2.  **Monitor**: Capture exit code, stdout, and stderr.
3.  **Diagnose**: If exit code != 0, send context (Command + Error) to the LLM via `LodestarProxy`.
4.  **Prescribe**: The LLM returns a JSON corrective action (e.g., new command to run, or modification to file).
5.  **Act**: Execute the fix.
6.  **Retry**: Re-run the original command.

### Constraints
-   **Safety**: Only allow specific types of fixes (e.g., running commands) or prompt user for confirmation if risky.
-   **Budget**: Limit retries to 3 to avoid infinite cost loops.

## Consequences
-   **Pros**: Significantly higher success rate for long-running agent tasks.
-   **Cons**: Higher token costs due to error analysis calls.
