# Security Guidelines for Lodestar

## API Keys

**Never commit API keys to git!**

Keys are stored in:
- `~/.bashrc` - Environment variables (not in repo)
- `.lodestar/router.log` - Router logs (excluded via .gitignore)

## Protected Files

The following are excluded from git:
- `.lodestar/` - Contains logs with API keys
- `.aider*` - Aider session data
- `*.key` - Any key files
- `.env` - Environment files

## If Keys Are Leaked

1. **Revoke immediately** at provider console
2. **Generate new keys**
3. **Update ~/.bashrc** with new keys
4. **Restart router**: `pkill litellm && ./scripts/start-router.sh`

## Key Rotation

Rotate API keys quarterly:
- Anthropic: https://console.anthropic.com/settings/keys
- OpenAI: https://platform.openai.com/api-keys
- xAI: https://console.x.ai/
- Google AI: https://aistudio.google.com/apikey
