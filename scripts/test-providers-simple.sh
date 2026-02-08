#!/bin/bash
# Simple provider test with detailed output

echo "🧪 Simple Provider Test"
echo "======================"
echo ""

test_model() {
    local MODEL=$1
    local NAME=$2
    
    echo "Testing $NAME ($MODEL)..."
    
    RESULT=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST http://localhost:4000/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"$MODEL\",
            \"messages\": [{\"role\": \"user\", \"content\": \"Hi\"}],
            \"max_tokens\": 10
        }")
    
    HTTP_CODE=$(echo "$RESULT" | grep "HTTP_CODE:" | cut -d: -f2)
    BODY=$(echo "$RESULT" | sed '/HTTP_CODE:/d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        if echo "$BODY" | grep -q '"content"'; then
            CONTENT=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['choices'][0]['message']['content'][:50])" 2>/dev/null)
            echo "  ✅ WORKING - Response: $CONTENT"
        else
            echo "  ⚠️  Got 200 but no content"
        fi
    else
        ERROR=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('error', {}).get('message', 'Unknown error')[:100])" 2>/dev/null)
        if echo "$ERROR" | grep -qi "credit\|quota\|billing\|permission"; then
            echo "  💳 Needs Credits"
        else
            echo "  ❌ FAILED - $ERROR"
        fi
    fi
    
    # GPU switch delay
    sleep 3
    echo ""
}

# Test all models
test_model "gpt-3.5-turbo" "DeepSeek Coder (FREE)"
test_model "local-llama" "Llama 3.1 (FREE)"
test_model "claude-sonnet" "Claude Sonnet"
test_model "gpt-4o-mini" "GPT-4o Mini"
test_model "grok-beta" "Grok Beta"
test_model "gemini-pro" "Gemini Pro"

echo "Done!"
