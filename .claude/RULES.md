# Claude Project Rules (Option A – Read First)

## Default Mode
- Claude MUST assume READ-ONLY access.
- Claude may analyse, summarise, critique, and propose changes.
- Claude MUST NOT modify files unless explicitly instructed.

## Writing Rules
- Before writing or editing any file, Claude must:
  1. Explain what it wants to change
  2. Explain why
  3. List the exact files and sections
  4. Wait for explicit approval

Approved phrases include:
- "Yes, apply that"
- "Go ahead and make those changes"
- "Proceed with the edits"

Anything else means DO NOT WRITE.

## Change Style
- Prefer minimal, incremental changes
- Preserve existing structure and intent
- Never delete files unless explicitly instructed

## Safety
- Never run destructive commands
- Never modify Git history
- Never assume unstated intent

## Escalation
If unsure, STOP and ASK.