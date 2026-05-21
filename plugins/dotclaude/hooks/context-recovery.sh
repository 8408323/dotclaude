#!/bin/bash
# Re-injects critical project rules after context compaction.
# Used as a SessionStart hook with matcher "compact".
#
# When Claude's context window fills up, compaction summarizes the conversation
# and loses specific details. This hook restores the project's non-negotiable
# rules so Claude stays aligned even after compaction.
#
# It re-injects the project's own always-on rules (the `.claude/rules/*.md`
# files with `alwaysApply: true`), so recovery is automatically project-aware —
# no per-project editing of this script needed. If the project has no such
# rules, it falls back to a minimal generic block.

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
RULES_DIR="$PROJECT_DIR/.claude/rules"

# ──────────────────────────────────────────────
# Dynamic context (same as session-start.sh)
# ──────────────────────────────────────────────

CONTEXT=""

BRANCH=$(git branch --show-current 2>/dev/null)
if [ -n "$BRANCH" ]; then
  CONTEXT="Branch: $BRANCH"
fi

LAST_COMMIT=$(git log --oneline -1 2>/dev/null)
if [ -n "$LAST_COMMIT" ]; then
  CONTEXT="$CONTEXT | Last commit: $LAST_COMMIT"
fi

CHANGES=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
if [ "$CHANGES" -gt 0 ] 2>/dev/null; then
  CONTEXT="$CONTEXT | Uncommitted changes: $CHANGES files"
fi

# ──────────────────────────────────────────────
# Re-inject the project's always-on rules
# ──────────────────────────────────────────────
# An always-on rule has `alwaysApply: true` in its frontmatter. Path-scoped
# rules are deliberately skipped — they load on demand near matching files and
# don't need to survive compaction. The frontmatter and the dotclaude:managed
# marker are stripped so only the instruction body is re-injected.

emit_rule_bodies() {
  local found=1 f
  for f in "$RULES_DIR"/*.md; do
    [ -f "$f" ] || continue
    awk 'NR==1 && $0=="---"{fm=1; next}
         fm && $0=="---"{exit}
         fm && /^alwaysApply:[[:space:]]*true[[:space:]]*$/{ok=1}
         END{exit !ok}' "$f" || continue
    found=0
    echo "── ${f##*/} ──"
    # Drop the YAML frontmatter block and the managed-marker comment.
    awk 'NR==1 && $0=="---"{infm=1; next}
         infm && $0=="---"{infm=0; next}
         infm{next}
         /dotclaude:managed/{next}
         {print}' "$f"
    echo
  done
  return $found
}

echo "=== CONTEXT RECOVERED AFTER COMPACTION ==="
echo ""
echo "CRITICAL PROJECT RULES (restored automatically — do not ignore):"
echo ""

if ! emit_rule_bodies; then
  # Fallback for projects that haven't scaffolded .claude/rules yet.
  cat <<'RULES'
- Verify behavior, not implementation. Run the specific test file, not the full suite.
- Don't add features beyond what was asked. No dead code. Match surrounding conventions.
- Never commit or log secrets, tokens, credentials, or PII. Validate untrusted input at boundaries.
- Don't push to main/master; no force pushes (use --force-with-lease); work on feature branches.
- Don't modify generated files, lock files, or .env files.
RULES
fi

# ──────────────────────────────────────────────
# Append dynamic context
# ──────────────────────────────────────────────

if [ -n "$CONTEXT" ]; then
  echo ""
  echo "Current state: $CONTEXT"
fi

# Full CLAUDE.md is intentionally not re-injected — it can be large and would
# negate the benefit of compaction. Claude can re-read it from disk on demand;
# the always-on rules above are what genuinely must survive a compaction cycle.

echo ""
echo "=== END CONTEXT RECOVERY ==="

exit 0
