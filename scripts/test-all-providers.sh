#!/bin/bash
# Comprehensive test of all Lodestar providers
#
# Expected results:
# - gpt-3.5-turbo (DeepSeek): WORKING (essential - FREE)
# - local-llama: May timeout on first run (non-essential)
# - Claude/OpenAI/Grok: Needs credits (routing verified)
# - Gemini: Needs correct config + credits

echo "🧪 Lodestar Provider Connection Test"
echo "===================================="
echo ""
echo "Testing all 8 providers with dummy prompts..."
echo ""

# Test configuration
TEST_PROMPT="Respond with exactly: 'Connection successful'"
MAX_TOKENS=20
TIMEOUT=60  # Increased from 45 to 60 seconds
GPU_SWITCH_DELAY=5  # Increased from 3 to 5 seconds

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Results tracking
WORKING=0
NEEDS_CREDITS=0
FAILED=0

# Function to test a provider
test_provider() {
    local MODEL=$1
    local PROVIDER=$2
    local COST=$3
    
    echo -n "Testing ${BLUE}${MODEL}${NC} (${PROVIDER})... "
    
# Make API call with timeout (increased for GPU model switching)
    RESPONSE=$(timeout ${TIMEOUT}s curl -s -X POST http://localhost:4000/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"${MODEL}\",
            \"messages\": [{\"role\": \"user\", \"content\": \"${TEST_PROMPT}\"}],
            \"max_tokens\": ${MAX_TOKENS}
        }" 2>&1)

    # Allow GPU time to unload model before next test
    sleep $GPU_SWITCH_DELAY

    # Check for success - look for valid completion response
    if echo "$RESPONSE" | grep -q '"choices"' && echo "$RESPONSE" | grep -q '"content"'; then
        echo -e "${GREEN}✅ WORKING${NC} (${COST})"
        WORKING=$((WORKING + 1))
        return 0
    # Check for credit issues (including permission errors that mean needs credits)
    elif echo "$RESPONSE" | grep -qi "credit\|quota\|billing\|payment\|balance\|permission.*execute"; then
        echo -e "${YELLOW}💳 Needs Credits${NC} (${COST})"
        NEEDS_CREDITS=$((NEEDS_CREDITS + 1))
        return 1
    # Check for auth issues
    elif echo "$RESPONSE" | grep -qi "unauthorized\|forbidden\|api.key\|authentication"; then
        echo -e "${RED}❌ Auth Failed${NC} - Check API key"
        FAILED=$((FAILED + 1))
        return 2
    # Check for network issues
    elif echo "$RESPONSE" | grep -qi "connection\|timeout\|network\|dns"; then
        echo -e "${RED}❌ Network Error${NC} - Check connectivity"
        FAILED=$((FAILED + 1))
        return 3
    # Unknown error
    else
        echo -e "${RED}❌ FAILED${NC}"
        if [ -n "$RESPONSE" ]; then
            echo "    Error: $(echo "$RESPONSE" | grep -o '"message":"[^"]*"' | head -1 | cut -d'"' -f4 | cut -c1-80)"
        fi
        FAILED=$((FAILED + 1))
        return 4
    fi
}

# Check if router is running
if ! curl -s http://localhost:4000/v1/models > /dev/null 2>&1; then
    echo -e "${RED}❌ Router is not running!${NC}"
    echo ""
    echo "Start it with: cd ~/ProjectLodestar && ./scripts/start-router.sh"
    exit 1
fi

echo "Router: ✅ Running"
echo ""

# Test FREE Local Models (Tier 1)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TIER 1: FREE Local Models (Unlimited)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_provider "gpt-3.5-turbo" "DeepSeek Coder 6.7B" "FREE"
test_provider "local-llama" "Llama 3.1 8B" "FREE"

echo ""

# Test Claude Models (Tier 2)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TIER 2: Claude (Anthropic API)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_provider "claude-sonnet" "Claude Sonnet 4.5" "\$3/\$15 per M tokens"
test_provider "claude-opus" "Claude Opus 4.5" "\$15/\$75 per M tokens"

echo ""

# Test OpenAI Models (Tier 3)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TIER 3: OpenAI (ChatGPT API)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_provider "gpt-4o-mini" "GPT-4o Mini" "\$0.15/\$0.60 per M tokens"
test_provider "gpt-4o" "GPT-4o" "\$2.50/\$10 per M tokens"

echo ""

# Test Grok (Tier 4)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TIER 4: Grok (xAI API)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_provider "grok-beta" "Grok Beta" "\$5/\$15 per M tokens"

echo ""

# Test Gemini (Tier 5)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TIER 5: Gemini (Google AI)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_provider "gemini-pro" "Gemini 2.0 Flash" "\$0.075/\$0.30 per M tokens"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✅ Working:${NC} $WORKING providers"
echo -e "${YELLOW}💳 Needs Credits:${NC} $NEEDS_CREDITS providers"
echo -e "${RED}❌ Failed:${NC} $FAILED providers"
echo ""

TOTAL=$((WORKING + NEEDS_CREDITS + FAILED))
echo "Total Tested: $TOTAL/8 providers"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "RECOMMENDATIONS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $WORKING -gt 0 ]; then
    echo -e "${GREEN}✓${NC} You can start coding with FREE models now!"
    echo "  Usage: aider file.py"
fi

if [ $NEEDS_CREDITS -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}💡${NC} Add credits to unlock premium models:"
    echo "  • Claude: https://console.anthropic.com/settings/billing"
    echo "  • OpenAI: https://platform.openai.com/account/billing"
    echo "  • Grok: https://console.x.ai/"
    echo "  • Gemini: https://aistudio.google.com/billing"
fi

if [ $FAILED -gt 0 ]; then
    echo ""
    echo -e "${RED}⚠${NC}  Some providers failed - check router logs:"
    echo "  tail -100 ~/ProjectLodestar/.lodestar/router.log"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Exit code based on results
if [ $WORKING -eq 0 ]; then
    exit 1  # No working providers
elif [ $WORKING -ge 2 ]; then
    exit 0  # At least 2 FREE models working
else
    exit 2  # Some working but not ideal
fi
