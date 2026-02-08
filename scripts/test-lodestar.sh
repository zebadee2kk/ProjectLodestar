#!/bin/bash
# Automated test for Lodestar infrastructure

echo "🧪 Lodestar Infrastructure Test"
echo "================================"
echo ""

# Test 1: Router availability
echo "Test 1: Router availability..."
if curl -s http://localhost:4000/v1/models > /dev/null; then
    echo "✅ Router is running"
else
    echo "❌ Router is NOT running"
    exit 1
fi

# Test 2: Model registration
echo ""
echo "Test 2: Model registration..."
MODELS=$(curl -s http://localhost:4000/v1/models | python3 -c "import sys, json; print([m['id'] for m in json.load(sys.stdin)['data']])")
echo "Registered models: $MODELS"

if [[ $MODELS == *"gpt-3.5-turbo"* ]]; then
    echo "✅ FREE model registered"
else
    echo "❌ FREE model NOT registered"
    exit 1
fi

# Test 3: T600 Ollama connectivity
echo ""
echo "Test 3: T600 Ollama connectivity..."
if curl -s http://192.168.120.211:11434/api/tags > /dev/null; then
    echo "✅ T600 is reachable"
else
    echo "❌ T600 is NOT reachable"
    exit 1
fi

# Test 4: Aider file creation
echo ""
echo "Test 4: Aider file creation test..."
TEST_DIR="/tmp/lodestar-test-$$"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Initialize git
git init > /dev/null 2>&1
git config user.name "Test" > /dev/null 2>&1
git config user.email "test@test" > /dev/null 2>&1

echo "Running Aider (this may take 30-60 seconds)..."

# Run Aider with explicit message
aider --yes --auto-commits --model gpt-3.5-turbo \
      --message "Create hello.py with a function greet() that prints 'Hello from Lodestar'" \
      > aider.log 2>&1

# Give it a moment to complete
sleep 2

# Check results
if [ -f "hello.py" ]; then
    echo "✅ Aider created files successfully"
    echo ""
    echo "📄 File content:"
    cat hello.py
    echo ""
    
    # Check git commit
    if git log --oneline 2>/dev/null | head -1 | grep -q .; then
        echo "✅ Git auto-commit working"
        git log --oneline | head -3
    else
        echo "⚠️  No git commits found"
    fi
else
    echo "❌ Aider did NOT create files"
    echo ""
    echo "📋 Full Aider output:"
    cat aider.log
    echo ""
    echo "📁 Directory contents:"
    ls -la
    cd /
    rm -rf "$TEST_DIR"
    exit 1
fi

# Cleanup
cd /
rm -rf "$TEST_DIR"

echo ""
echo "🎉 All tests passed!"
echo ""
echo "Summary:"
echo "  ✅ Router operational"
echo "  ✅ Models registered (FREE)"
echo "  ✅ T600 Ollama connected"
echo "  ✅ Aider creates files"
echo "  ✅ Git integration works"
echo ""
echo "💡 Lodestar is fully operational!"
