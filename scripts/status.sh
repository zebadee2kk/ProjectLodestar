#!/bin/bash
# Check what's running

echo "=== LiteLLM Router Status ==="
if pgrep -f "litellm.*4000" > /dev/null; then
    echo "✅ Router is running"
    curl -s http://localhost:4000/v1/models | python3 -m json.tool 2>/dev/null | grep '"id"' || echo "Models not responding"
else
    echo "❌ Router is NOT running"
    echo "Start with: ./scripts/start-router.sh"
fi

echo ""
echo "=== Ollama Status (T600 VM) ==="
if curl -s http://192.168.120.211:11434/api/tags > /dev/null 2>&1; then
    echo "✅ T600 Ollama is reachable"
    curl -s http://192.168.120.211:11434/api/tags | python3 -c "import sys, json; print('Models:', ', '.join([m['name'] for m in json.load(sys.stdin)['models']]))" 2>/dev/null
else
    echo "❌ T600 Ollama is NOT reachable"
fi

echo ""
echo "=== Tools ==="
echo "Aider: $(aider --version 2>&1 | head -1)"
echo "LiteLLM: $(litellm --version 2>&1 | head -1)"
echo "Git: $(git --version)"
