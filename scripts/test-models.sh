#!/bin/bash
# Test all available models

echo "🧪 Testing Lodestar Models"
echo "=========================="
echo ""

MODELS=("gpt-3.5-turbo" "local-llama" "claude-sonnet" "claude-opus" "gpt-4o" "gpt-4o-mini" "grok-beta" "gemini-pro")

for MODEL in "${MODELS[@]}"; do
    echo -n "Testing $MODEL... "
    
    # Create temp test dir
    TEST_DIR="/tmp/test-$MODEL-$$"
    mkdir -p "$TEST_DIR"
    cd "$TEST_DIR"
    git init > /dev/null 2>&1
    git config user.name "Test" > /dev/null 2>&1
    git config user.email "test@test" > /dev/null 2>&1
    
    # Try to create a simple file
    timeout 30s aider --yes --model "$MODEL" \
        --message "Create test.txt with the text 'Hello from $MODEL'" \
        > /dev/null 2>&1
    
    if [ -f "test.txt" ]; then
        echo "✅ Working"
    else
        echo "❌ Failed (check if API key is set)"
    fi
    
    # Cleanup
    cd /
    rm -rf "$TEST_DIR"
done

echo ""
echo "💡 Use working models with: aider --model <name>"
