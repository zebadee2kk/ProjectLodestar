#!/bin/bash
# Quick start for a coding session

echo "🌟 Lodestar - AI Coding Setup"
echo ""

# Check if router is running
if ! pgrep -f "litellm.*4000" > /dev/null; then
    echo "Starting LiteLLM router..."
    ./scripts/start-router.sh
    sleep 3
fi

# Show status
./scripts/status.sh

echo ""
echo "=== Ready to Code! ==="
echo ""
echo "💡 Quick Commands:"
echo "   aider file.py          # Start coding with AI (FREE Ollama)"
echo "   aider --model claude-sonnet  # Use Claude Pro"
echo "   ./scripts/adr-new.sh 'Decision'  # Document decision"
echo ""
echo "📚 Full docs: ~/ProjectLodestar/docs/"
