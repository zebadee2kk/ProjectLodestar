# 🚀 Lodestar Quick Reference

![Status](https://img.shields.io/badge/status-operational-brightgreen)
![Models](https://img.shields.io/badge/models-8%20providers-blue)
![Cost](https://img.shields.io/badge/cost-90%25%20savings-success)

## Daily Workflow

### Start Your Day
```bash
ssh lodestar@vm-lodestar-core
cd ~/ProjectLodestar
./scripts/status.sh
```

### Start Coding (FREE Models)
```bash
cd ~/your-project
aider file.py              # Uses DeepSeek automatically
```

### Switch to Premium AI
```bash
aider --model claude-sonnet file.py       # Claude Sonnet 4.5
aider --model gpt-4o-mini file.py         # GPT-4o Mini
aider --model grok-beta file.py           # Grok
```

### Mid-Session Model Switching
```
/model claude-sonnet       # Switch to Claude
/model gpt-3.5-turbo       # Back to FREE DeepSeek
/help                      # See all Aider commands
```

---

## Model Selection Guide

| Use Case | Recommended Model | Cost |
|----------|------------------|------|
| Standard coding, bug fixes | `gpt-3.5-turbo` (DeepSeek) | **FREE** |
| Learning, experimentation | `local-llama` | **FREE** |
| Complex architecture | `claude-sonnet` | $3-15/M tokens |
| Critical production code | `claude-opus` | $15-75/M tokens |
| Quick iterations | `gpt-4o-mini` | $0.15-0.60/M |
| Creative solutions | `grok-beta` | $5-15/M |

---

# v2.0 Health & Agent Commands
lodestar status          # Detailed health dashboard
lodestar config          # Configure remote GPU / SSH
lodestar costs --dashboard # Real-time cost analytics
lodestar run "ls -la"    # Self-healing execution
lodestar run "find file" # Goal-oriented agentic cleanup
lodestar diff            # Visual AI-enhanced diff

### Git & SSH
```bash
git add .
git commit -m "feat: description"
git push origin main          # No password needed (SSH)
```

---

## Troubleshooting

### Router Not Responding
```bash
pkill -f litellm
./scripts/start-router.sh
```

### T600 Ollama Down
```bash
curl http://192.168.120.211:11434/api/tags
# If fails, check T600 VM
```

### Model Takes Too Long
```bash
# Switch to faster model
/model gpt-3.5-turbo
```

### Check Logs
```bash
tail -100 ~/ProjectLodestar/.lodestar/router.log
```

---

## Cost Tracking (Manual)

Keep a simple log:
```bash
echo "$(date): Used Claude for complex refactor - ~10k tokens" >> ~/lodestar-costs.txt
```

---

## Tips & Tricks

1. **Default to FREE** - Start every session with DeepSeek
2. **Escalate Strategically** - Switch to Claude only for hard problems
3. **Use Git Messages** - Descriptive commits help track AI contributions
4. **Test Often** - Run `./scripts/status.sh` regularly
5. **Monitor Costs** - Check API dashboards monthly

---

## Emergency Contacts

- **Router Log:** `~/ProjectLodestar/.lodestar/router.log`
- **GitHub Issues:** https://github.com/zebadee2kk/ProjectLodestar/issues
- **Documentation:** `~/ProjectLodestar/docs/`

---

**Quick Links:**
- [Full Documentation](../README.md)
- [Architecture](ARCHITECTURE.md)
- [Roadmap](../ROADMAP.md)
