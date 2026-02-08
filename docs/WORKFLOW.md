# Lodestar Daily Workflow

## Starting Your Day
```bash
cd ~/ProjectLodestar
./scripts/quick-start.sh
```

This starts the router and shows system status.

## Coding with AI

### Use FREE Local Model (Default)
```bash
cd ~/your-project
aider file.py
```

Uses DeepSeek Coder on your T600 VM (FREE, unlimited)

### Use Claude for Complex Work
```bash
aider --model claude-sonnet file.py
```

### Switch Models Mid-Session
Inside Aider:
```
/model claude-sonnet    # Switch to Claude Pro
/model gpt-3.5-turbo    # Switch back to FREE
```

## Model Costs

| Model | Cost | Use For |
|-------|------|---------|
| `gpt-3.5-turbo` | **FREE** | Routine coding, refactors, tests |
| `local-llama` | **FREE** | General tasks, documentation |
| `claude-sonnet` | **PAID** | Complex logic, architecture |
| `claude-opus` | **EXPENSIVE** | Critical decisions only |

## Recording Decisions
```bash
./scripts/adr-new.sh "Use JWT for Authentication"
```

Opens editor to document your architectural decision.

## Multi-Project Workflow
```bash
# Project 1
cd ~/project-auth
aider --model gpt-3.5-turbo

# Project 2 (different terminal)
cd ~/project-data
aider --model gpt-3.5-turbo
```

Each project maintains separate context.

## Checking Status
```bash
./scripts/status.sh
```

Shows router status, T600 connection, available models.

## Stopping for the Day
```bash
# Stop the router
kill $(cat ~/.lodestar/router.pid)

# Or just close terminals - it'll restart next session
```

## Tips

1. **Start with FREE models** - only use Claude when stuck
2. **Commit often** - Aider auto-commits, but you can `/commit` manually
3. **Document decisions** - Create ADRs for anything you'll forget
4. **Check costs** - Watch router logs in `.lodestar/router.log`
