# Git Branching Strategy

**Project**: Lodestar  
**Version**: 2.0  
**Last Updated**: 2026-02-09

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Branch Structure](#branch-structure)
3. [Naming Conventions](#naming-conventions)
4. [Workflow](#workflow)
5. [AI Agent Guidelines](#ai-agent-guidelines)
6. [Human Developer Guidelines](#human-developer-guidelines)
7. [Merge Strategy](#merge-strategy)
8. [Release Process](#release-process)
9. [Best Practices](#best-practices)

---

## Overview

This document defines the branching strategy for Project Lodestar to enable **parallel development** by multiple developers and AI agents while minimizing merge conflicts and maintaining code quality.

### Goals
- ✅ Enable parallel work by humans and AI agents
- ✅ Minimize merge conflicts
- ✅ Maintain stable main branch
- ✅ Clear ownership and accountability
- ✅ Easy to understand and follow

### Key Principles
1. **Isolation**: Each developer/agent works in their own branch
2. **Integration**: Regular merges to integration branch
3. **Stability**: Main branch always deployable
4. **Traceability**: Clear commit history and ownership

---

## Branch Structure

```
main (protected)
├── develop (integration branch)
│   ├── human/<developer-name>/<feature-name>
│   ├── ai/gemini/<feature-name>
│   ├── ai/claude/<feature-name>
│   └── ai/<agent-name>/<feature-name>
├── release/<version>
└── hotfix/<issue-number>-<description>
```

### Branch Types

#### 1. **Main Branch** (`main`)
- **Purpose**: Production-ready code
- **Protection**: Protected, requires PR approval
- **Merge From**: `release/*` branches only
- **Lifetime**: Permanent
- **Who Can Merge**: Project maintainer only

#### 2. **Development Branch** (`develop`)
- **Purpose**: Integration branch for ongoing work
- **Protection**: Semi-protected, requires tests to pass
- **Merge From**: Feature branches
- **Merge To**: `release/*` branches
- **Lifetime**: Permanent
- **Who Can Merge**: All developers/agents after tests pass

#### 3. **Feature Branches** (`human/*`, `ai/*`)
- **Purpose**: Individual feature development
- **Protection**: None
- **Merge From**: `develop` (for updates)
- **Merge To**: `develop`
- **Lifetime**: Temporary (deleted after merge)
- **Who Can Merge**: Branch owner

#### 4. **Release Branches** (`release/*`)
- **Purpose**: Prepare for production release
- **Protection**: Protected
- **Merge From**: `develop`
- **Merge To**: `main` and `develop`
- **Lifetime**: Temporary (kept for reference)
- **Who Can Merge**: Project maintainer

#### 5. **Hotfix Branches** (`hotfix/*`)
- **Purpose**: Emergency fixes for production
- **Protection**: None
- **Merge From**: `main`
- **Merge To**: `main` and `develop`
- **Lifetime**: Temporary
- **Who Can Merge**: Any developer (urgent)

---

## Naming Conventions

### Format
```
<type>/<owner>/<feature-name>
```

### Types
- `human/` - Human developer branches
- `ai/` - AI agent branches
- `release/` - Release preparation
- `hotfix/` - Emergency fixes

### Owner
- For humans: `human/<name>/`
  - Example: `human/richard/web-ui`
- For AI agents: `ai/<agent-name>/`
  - Example: `ai/gemini/response-caching`
  - Example: `ai/claude/model-optimization`

### Feature Name
- Use kebab-case (lowercase with hyphens)
- Be descriptive but concise
- Include issue number if applicable

### Examples
```bash
# Human branches
human/richard/web-ui-dashboard
human/richard/fix-123-router-crash
human/sarah/multi-project-support

# AI agent branches
ai/gemini/response-caching
ai/gemini/gpu-optimization
ai/claude/cost-analytics
ai/claude/health-monitoring

# Release branches
release/v2.0.0
release/v2.1.0-beta.1

# Hotfix branches
hotfix/456-memory-leak
hotfix/789-auth-failure
```

---

## Workflow

### 1. Starting New Work

#### For Humans:
```bash
# Update develop
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b human/<your-name>/<feature-name>

# Work on feature
# ... make changes ...

# Commit regularly
git add .
git commit -m "feat: add feature X"
```

#### For AI Agents:
```bash
# Update develop
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b ai/<agent-name>/<feature-name>

# Work on feature
# ... make changes ...

# Commit with clear messages
git add .
git commit -m "feat(<scope>): implement feature X"
```

### 2. Keeping Branch Updated

```bash
# Regularly sync with develop to avoid conflicts
git checkout develop
git pull origin develop

git checkout <your-branch>
git merge develop

# Resolve any conflicts
# ... fix conflicts ...
git add .
git commit -m "merge: sync with develop"
```

### 3. Submitting Work

```bash
# Ensure tests pass
pytest modules/tests/ -v

# Push to remote
git push origin <your-branch>

# Create Pull Request to develop
# - Add clear description
# - Link related issues
# - Request review if needed
```

### 4. After Merge

```bash
# Delete local branch
git checkout develop
git branch -d <your-branch>

# Delete remote branch (optional, can be done via PR)
git push origin --delete <your-branch>
```

---

## AI Agent Guidelines

### Branch Ownership
- Each AI agent (Gemini, Claude, etc.) owns their branches
- Branch name format: `ai/<agent-name>/<feature-name>`
- Only the owning agent should commit to their branch

### Coordination
1. **Check existing branches** before starting work
   ```bash
   git branch -a | grep ai/
   ```

2. **Avoid duplicate work** - Check if another agent is working on similar feature

3. **Communicate** via commit messages and PR descriptions

4. **Small, focused branches** - One feature per branch

### Commit Standards
```bash
# Good commit messages
git commit -m "feat(cache): implement SQLite-based response cache"
git commit -m "fix(cli): resolve missing cmd_costs function"
git commit -m "docs(adr): add response caching decision record"
git commit -m "test(cache): add unit tests for CacheManager"

# Include scope in parentheses
# Types: feat, fix, docs, test, refactor, chore
```

### Testing Requirements
- ✅ All tests must pass before PR
- ✅ Add tests for new features
- ✅ Update existing tests if behavior changes
- ✅ Run full test suite: `pytest modules/tests/ -v`

### Documentation Requirements
- ✅ Update README.md if user-facing changes
- ✅ Create ADR for architectural decisions
- ✅ Update CHANGELOG.md
- ✅ Add docstrings to new functions/classes

---

## Human Developer Guidelines

### Branch Ownership
- Create branches under `human/<your-name>/`
- You own your branches exclusively
- Example: `human/richard/web-ui`

### Before Starting Work
1. Check ROADMAP.md for planned features
2. Check existing branches to avoid conflicts
3. Communicate with team about your plans
4. Create GitHub issue for tracking

### During Development
1. Commit frequently with clear messages
2. Sync with `develop` regularly (daily recommended)
3. Run tests before pushing
4. Update documentation as you go

### Code Review
- Request review from team members
- Address feedback promptly
- Use PR comments for discussion
- Approve others' PRs when appropriate

---

## Merge Strategy

### Feature Branch → Develop
- **Method**: Squash and merge (for clean history) OR Merge commit (to preserve history)
- **Requirements**:
  - ✅ All tests passing
  - ✅ No merge conflicts
  - ✅ Documentation updated
  - ✅ Code review approved (optional for AI agents)

### Develop → Release
- **Method**: Merge commit (preserve all history)
- **Requirements**:
  - ✅ All features complete
  - ✅ Full test suite passing
  - ✅ CHANGELOG.md updated
  - ✅ Version bumped

### Release → Main
- **Method**: Merge commit
- **Requirements**:
  - ✅ Release testing complete
  - ✅ Documentation finalized
  - ✅ Tagged with version number

### Hotfix → Main + Develop
- **Method**: Merge commit to both
- **Requirements**:
  - ✅ Critical bug fixed
  - ✅ Tests added for regression
  - ✅ Minimal changes only

---

## Release Process

### 1. Create Release Branch
```bash
git checkout develop
git pull origin develop
git checkout -b release/v2.1.0
```

### 2. Prepare Release
- Update version numbers
- Update CHANGELOG.md
- Final testing
- Documentation review

### 3. Merge to Main
```bash
git checkout main
git merge --no-ff release/v2.1.0
git tag -a v2.1.0 -m "Release version 2.1.0"
git push origin main --tags
```

### 4. Merge Back to Develop
```bash
git checkout develop
git merge --no-ff release/v2.1.0
git push origin develop
```

### 5. Cleanup
```bash
# Keep release branch for reference
# Or delete if not needed
git branch -d release/v2.1.0
```

---

## Best Practices

### ✅ DO

1. **Commit Often**
   - Small, logical commits
   - Clear commit messages
   - One concern per commit

2. **Sync Regularly**
   - Pull from `develop` daily
   - Resolve conflicts early
   - Keep branch up to date

3. **Test Before Push**
   - Run full test suite
   - Test manually if needed
   - Fix failing tests immediately

4. **Document Changes**
   - Update README for user-facing changes
   - Create ADRs for decisions
   - Add code comments for complex logic

5. **Communicate**
   - Use PR descriptions
   - Comment on related issues
   - Update project board

### ❌ DON'T

1. **Don't Commit to Main Directly**
   - Always use feature branches
   - Always create PR

2. **Don't Force Push to Shared Branches**
   - Never force push to `main` or `develop`
   - Only force push to your own feature branch if needed

3. **Don't Merge Without Testing**
   - Always run tests first
   - Check for conflicts

4. **Don't Create Huge PRs**
   - Keep PRs focused and small
   - Split large features into multiple PRs

5. **Don't Work on Same Files**
   - Coordinate with team
   - Avoid parallel edits to same code

---

## Conflict Resolution

### When Conflicts Occur

1. **Stay Calm** - Conflicts are normal

2. **Understand the Conflict**
   ```bash
   git status
   # Shows conflicted files
   ```

3. **Resolve Manually**
   - Open conflicted files
   - Look for `<<<<<<<`, `=======`, `>>>>>>>`
   - Choose correct version or merge both
   - Remove conflict markers

4. **Test After Resolution**
   ```bash
   pytest modules/tests/ -v
   ```

5. **Complete Merge**
   ```bash
   git add .
   git commit -m "merge: resolve conflicts with develop"
   ```

### Preventing Conflicts

1. **Sync frequently** with `develop`
2. **Communicate** about file ownership
3. **Small, focused branches**
4. **Modular code** - avoid touching same files

---

## Current Branch Status

### Active Branches (as of 2026-02-09)

```
main (stable, v1.0.0)
├── develop (to be created)
│   ├── ai/gemini/health-monitoring ✅ Complete
│   ├── ai/gemini/cost-dashboard ✅ Complete
│   ├── ai/gemini/visual-diff ✅ Complete
│   ├── ai/gemini/graceful-degradation ✅ Complete
│   └── ai/gemini/performance-caching 🚧 In Progress
└── claude/analyze-project-structure-82o2c (legacy)
```

### Migration Plan

1. **Create `develop` branch** from current `main`
2. **Merge all completed AI branches** to `develop`
3. **Rename existing branches** to follow new convention
4. **Update branch protection rules**
5. **Document in team wiki**

---

## Quick Reference

### Common Commands

```bash
# Create feature branch
git checkout develop
git checkout -b ai/gemini/<feature-name>

# Sync with develop
git checkout develop && git pull
git checkout <your-branch>
git merge develop

# Push and create PR
git push origin <your-branch>
# Then create PR on GitHub

# After merge, cleanup
git checkout develop
git pull
git branch -d <your-branch>
```

### Branch Naming Cheat Sheet

| Type | Format | Example |
|------|--------|---------|
| Human Feature | `human/<name>/<feature>` | `human/richard/web-ui` |
| AI Feature | `ai/<agent>/<feature>` | `ai/gemini/caching` |
| Release | `release/v<version>` | `release/v2.1.0` |
| Hotfix | `hotfix/<issue>-<desc>` | `hotfix/123-auth-fix` |

---

## Questions?

- Check this document first
- Ask in team chat
- Create GitHub Discussion
- Update this doc if needed

---

**Remember**: Good branching strategy enables parallel work without chaos! 🚀
