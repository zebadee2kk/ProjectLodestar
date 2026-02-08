#!/bin/bash
# Create a new Architecture Decision Record

if [ -z "$1" ]; then
    echo "Usage: ./scripts/adr-new.sh 'Decision Title'"
    exit 1
fi

ADR_DIR="docs/adr"
TITLE="$1"
DATE=$(date +%Y-%m-%d)

# Count existing ADRs
NUM=$(find "$ADR_DIR" -name "*.md" 2>/dev/null | wc -l)
NUM=$((NUM + 1))

# Create filename
FILENAME=$(printf "%04d" $NUM)-$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd '[:alnum:]-').md
FILEPATH="$ADR_DIR/$FILENAME"

# Create ADR from template
cat > "$FILEPATH" << EOF
# $TITLE

**Status:** Proposed  
**Date:** $DATE  
**Deciders:** Lodestar Team

## Context

What is the issue we're seeing that motivates this decision?

## Decision

What change are we proposing/making?

## Consequences

### Positive
- 

### Negative
- 

### Neutral
- 

## Implementation Notes

EOF

echo "✅ Created: $FILEPATH"
echo "📝 Opening in nano..."
nano "$FILEPATH"

# Add to git
git add "$FILEPATH"
echo "✨ ADR added to git staging"
