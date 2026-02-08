#!/bin/bash
# Start LiteLLM router in the background

cd ~/ProjectLodestar

echo "🚀 Starting LiteLLM router..."
litellm --config config/litellm_config.yaml --port 4000 > .lodestar/router.log 2>&1 &
ROUTER_PID=$!

echo "Router PID: $ROUTER_PID" > .lodestar/router.pid
echo "✅ Router started on http://localhost:4000"
echo "📋 Log: ~/.lodestar/router.log"
echo "🛑 Stop with: kill $(cat .lodestar/router.pid)"
