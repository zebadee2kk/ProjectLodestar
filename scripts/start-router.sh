#!/bin/bash
# Start LiteLLM router and wait for it to be ready

cd ~/ProjectLodestar

echo "🚀 Starting LiteLLM router..."

# Kill any existing router
pkill -f "litellm.*4000" 2>/dev/null || true
sleep 2

# Create log directory
mkdir -p .lodestar

# Start with full logging
nohup litellm --config config/litellm_config.yaml \
              --port 4000 \
              --detailed_debug \
              > .lodestar/router.log 2>&1 &

ROUTER_PID=$!
echo "$ROUTER_PID" > .lodestar/router.pid

echo "⏳ Waiting for router to be ready..."

# Wait up to 15 seconds for router to respond
for i in {1..15}; do
    if curl -s http://localhost:4000/v1/models > /dev/null 2>&1; then
        echo "✅ Router is ready! (PID: $ROUTER_PID)"
        echo "📋 Log: ~/ProjectLodestar/.lodestar/router.log"
        echo "🛑 Stop with: kill $ROUTER_PID"
        exit 0
    fi
    sleep 1
    echo -n "."
done

echo ""
echo "❌ Router failed to become ready after 15 seconds"
echo "Last 20 lines of log:"
tail -20 .lodestar/router.log
exit 1
