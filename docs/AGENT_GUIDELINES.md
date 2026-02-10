# AI Agent Guidelines

This project is a collaborative environment for both human developers and multiple AI agents (Claude, Gemini, Antigravity, etc.).

## 🤖 Operative Modes

### 1. Collaborative Proactivity (Default)
- Agents SHOULD be proactive in solving tasks.
- Agents MAY modify files, run tests, and verify builds without waiting for explicit approval for every single line of code, PROVIDED they are following a clear user request.
- **Safety First**: Before large-scale refactors or destructive changes, agents MUST outline their plan and wait for a "Go ahead".

### 2. Git as the Checkpoint
- Every significant change MUST be followed by a commit.
- Use descriptive commit messages following the `type(scope): description` format (e.g., `feat(routing): add connection pooling`).
- Never perform a `git push --force` or modify history unless explicitly asked.

## 🛠️ Tool Usage
- Use the `lodestar` CLI for environment management:
  - `lodestar status`: Check module health
  - `lodestar costs`: View cost reporting
  - `lodestar run "<cmd>"`: Execute commands with self-healing
- Always run `pytest modules/` after changes to ensure no regressions.

## 📝 Writing Style
- Keep changes minimal and incremental.
- Follow PEP 8 and use type hints for Python code.
- Update `CHANGELOG.md` and `ROADMAP.md` as features are completed.
- If a new architectural pattern is introduced, create a new ADR in `docs/adr/`.

## 🚨 Escalation
- If a task is ambiguous, **STOP and ASK**.
- If multiple conflicting implementations are possible, present the options to the USER.
- If you hit a technical blocker you cannot resolve after 3 attempts, inform the USER.
