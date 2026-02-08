# Lodestar Setup Guide

Complete installation guide for setting up Lodestar on a fresh Debian/Ubuntu system.

## Prerequisites

- Debian 12 (Bookworm) or Ubuntu 22.04+
- Python 3.11+
- Node.js 18+
- Git 2.39+
- Access to a machine running Ollama
- Claude API key (optional, for premium models)

## Installation Steps

### 1. System Preparation
```bash
# Update package lists
sudo apt update

# Install prerequisites
sudo apt install -y curl git python3-pip wget ca-certificates gnupg

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
sudo apt install -y nodejs

# Verify installations
python3 --version  # Should be 3.11+
node --version     # Should be 20.x
npm --version      # Should be 10.x
git --version      # Should be 2.39+
```

### 2. Configure User Environment
```bash
# Add Python tools to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Configure Git
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
git config --global init.defaultBranch main
```

### 3. Install Core Tools
```bash
# Install Aider (AI coding agent)
pip3 install aider-chat --break-system-packages

# Install LiteLLM (API router)
pip3 install 'litellm[proxy]' --break-system-packages

# Verify installations
aider --version    # Should show 0.86.1+
litellm --version  # Should show 1.75.0+
```

### 4. Clone Lodestar Repository
```bash
cd ~
git clone https://github.com/zebadee2kk/ProjectLodestar.git
cd ProjectLodestar
```

### 5. Configure API Keys
```bash
# Add Claude API key
nano ~/.bashrc
```

Add this line at the end:
```bash
export ANTHROPIC_API_KEY="sk-ant-your-actual-key-here"
```

Get your API key from: https://console.anthropic.com/settings/keys

Save and reload:
```bash
source ~/.bashrc
echo $ANTHROPIC_API_KEY  # Verify it's set
```

### 6. Configure LiteLLM Router

The repository includes a pre-configured `config/litellm_config.yaml`.

**Edit if needed:**
```bash
nano config/litellm_config.yaml
```

Update the Ollama IP address if your T600 VM has a different IP:
```yaml
api_base: http://YOUR_T600_IP:11434
```

### 7. Configure Aider
```bash
nano ~/.aider.conf.yml
```

Paste:
```yaml
openai-api-base: http://localhost:4000/v1
openai-api-key: sk-1234
model: gpt-3.5-turbo
weak-model: local-llama
auto-commits: true
dirty-commits: true
attribute-author: true
attribute-committer: true
map-tokens: 2048
edit-format: diff
```

### 8. Verify Ollama Connection
```bash
# Test connection to your T600 VM
curl http://YOUR_T600_IP:11434/api/tags

# Should return JSON with available models
```

If this fails:
- Verify T600 VM is running
- Check firewall rules allow port 11434
- Confirm Ollama service is active: `systemctl status ollama`

### 9. Start LiteLLM Router
```bash
cd ~/ProjectLodestar
./scripts/start-router.sh
```

You should see:
```
✅ Router started on http://localhost:4000
```

### 10. Verify Installation
```bash
./scripts/status.sh
```

Expected output:
```
=== LiteLLM Router Status ===
✅ Router is running

=== Ollama Status (T600 VM) ===
✅ T600 Ollama is reachable
Models: deepseek-coder:6.7b, llama3.1:8b

=== Tools ===
Aider: 0.86.1
LiteLLM: 1.75.0
Git: 2.39.5
```

### 11. Test with a Sample Project
```bash
# Create test project
mkdir ~/test-lodestar
cd ~/test-lodestar
git init
echo "# Test Project" > README.md
git add README.md
git commit -m "Initial commit"

# Start Aider with FREE model
aider README.md
```

In Aider, try:
```
> Add a hello world function in Python
```

If it works, you're all set! 🎉

## Troubleshooting

### "aider: command not found"

**Solution:**
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### "litellm: command not found"

**Solution:** Same as above, ensure PATH is set correctly.

### "Connection refused" to localhost:4000

**Solution:**
```bash
# Check if router is running
pgrep -f litellm

# If not, start it
cd ~/ProjectLodestar
./scripts/start-router.sh
```

### "Connection refused" to T600 Ollama

**Possible causes:**
1. T600 VM is not running
2. Ollama service is not active
3. Firewall blocking port 11434
4. Wrong IP address in config

**Check:**
```bash
# From your main VM
ping 192.168.120.211  # Or your T600 IP

# Try direct curl
curl http://192.168.120.211:11434/api/tags
```

### Claude API "Invalid API Key"

**Solution:**
```bash
# Verify key is set
echo $ANTHROPIC_API_KEY

# If empty, add to ~/.bashrc and source it
nano ~/.bashrc
source ~/.bashrc
```

### Aider "LLM did not conform to edit format"

**Cause:** Model returned incorrect format

**Solution:**
- Try again (models can be inconsistent)
- Switch to Claude: `/model claude-sonnet`
- File an issue if it persists with a specific model

## Post-Installation

### Daily Usage
```bash
# Start your day
cd ~/ProjectLodestar
./scripts/quick-start.sh

# Navigate to your project
cd ~/your-project

# Start coding
aider file.py
```

### Create Your First ADR
```bash
cd ~/ProjectLodestar
./scripts/adr-new.sh "Use Lodestar for AI Development"
```

### Push to Your Own GitHub
```bash
# Fork the repository or create your own
git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

## Updating

### Update Tools
```bash
# Update Aider
pip3 install --upgrade aider-chat --break-system-packages

# Update LiteLLM
pip3 install --upgrade litellm --break-system-packages
```

### Update Lodestar Scripts
```bash
cd ~/ProjectLodestar
git pull origin main
```

## Uninstallation

### Remove Tools
```bash
pip3 uninstall aider-chat litellm -y
```

### Remove Configuration
```bash
rm ~/.aider.conf.yml
rm -rf ~/.lodestar
# Remove ANTHROPIC_API_KEY line from ~/.bashrc
```

### Remove Repository
```bash
rm -rf ~/ProjectLodestar
```

## System Requirements

### Minimum

- 2 CPU cores
- 4GB RAM
- 10GB disk space
- Network access to Ollama server

### Recommended

- 4 CPU cores
- 8GB RAM
- 20GB disk space
- Gigabit network to Ollama server

### T600 VM Specifications

- GPU: NVIDIA T600 (4GB VRAM)
- Recommended models: 3B-7B parameters
- Currently running:
  - deepseek-coder:6.7b
  - llama3.1:8b

## Security Best Practices

1. **Never commit API keys to git**
   - Keep keys in `~/.bashrc` only
   - Add `*.key` to `.gitignore`

2. **Secure file permissions**
```bash
   chmod 600 ~/.bashrc
   chmod 700 ~/.lodestar
```

3. **Regular key rotation**
   - Rotate Claude API keys quarterly
   - Use separate keys for dev/prod

4. **Code review**
   - Always review AI-generated code
   - Test before deploying
   - Use feature branches

## Support

- **Documentation**: See docs/ directory
- **Issues**: https://github.com/zebadee2kk/ProjectLodestar/issues
- **Discussions**: GitHub Discussions

## Next Steps

1. Read [WORKFLOW.md](WORKFLOW.md) for daily usage
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system
3. Start coding with `aider` on your projects!
4. Document decisions with ADRs

Happy coding! 🚀
