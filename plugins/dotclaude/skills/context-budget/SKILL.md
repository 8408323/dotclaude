---
name: context-budget
description: Estimate per-turn token cost of this project's `.claude/` configuration and `CLAUDE.md`. Reports always-loaded vs path-scoped vs invoked-only, ranks the top contributors, and flags entries over budget. Add `--api` for exact counts via Anthropic's count_tokens endpoint instead of the chars/4 heuristic.
argument-hint: "[--api]"
disable-model-invocation: true
---

Estimate the token cost of this project's `.claude/` configuration and `CLAUDE.md`, so the user can see which files load on every turn versus only when triggered.

## Step 1: Discover loadable files

From the project root:

```bash
ls CLAUDE.md 2>/dev/null
find .claude/rules -name '*.md' -type f 2>/dev/null
find .claude/skills -name 'SKILL.md' -type f 2>/dev/null
find .claude/agents -name '*.md' -type f 2>/dev/null
[ -f .claude/CLAUDE.md ] && echo "WARN: .claude/CLAUDE.md exists. CLAUDE.md belongs at the project root."
```

Skip README files such as `.claude/agents/README.md` and `.claude/rules/README.md`. They are folder descriptions, and Claude Code does not load them at runtime.

## Step 2: Classify rules by frontmatter

For every `.md` file in `.claude/rules/`, read the YAML frontmatter (the block between the first two `---` lines).

| Frontmatter contains | Classification | Per-turn cost |
|---|---|---|
| `alwaysApply: true` | Always-loaded | Every turn |
| `paths: [...]` | Path-scoped | Loaded only when working near matched files |
| Neither | Defaults to always-loaded; flag for review | Every turn |

The other categories:
- `./CLAUDE.md` -> always-loaded, by definition.
- `.claude/skills/<name>/SKILL.md` -> invoked-only, with zero per-turn cost. It loads only when the user runs `/skill-name`, or, if `disable-model-invocation` is unset, when Claude auto-triggers it.
- `.claude/agents/<name>.md` -> invoked-only and runs in isolated context. Its cost is per-invocation in its own session, not per-turn in the main thread.

## Step 3: Count tokens per file

Default mode (no API call) uses a character-based heuristic. Anthropic documents that English text averages roughly 4 characters per token, so compute:

```bash
chars=$(wc -c < "$FILE" | tr -d ' ')
tokens=$((chars / 4))
```

Note this in the report so the user knows the count is approximate — typically within 10 to 15 percent of the exact count for config text.

`--api` mode: if `$ARGUMENTS` contains `--api`:

```bash
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "ERROR: --api requested but ANTHROPIC_API_KEY is not set. Falling back to heuristic."
else
  CONTENT=$(jq -Rs . < "$FILE")
  tokens=$(curl -s https://api.anthropic.com/v1/messages/count_tokens \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "content-type: application/json" \
    -d "{\"model\":\"claude-sonnet-4-6\",\"messages\":[{\"role\":\"user\",\"content\":$CONTENT}]}" \
    | jq -r '.input_tokens')
fi
```

The endpoint returns Anthropic's exact tokenizer count — the same number Claude Code itself sees when it loads the file.

## Step 4: Aggregate and report

Sum the tokens in each category, identify the top 3 contributors among the always-loaded files, then print:

```
Context budget for <project root>
Method: heuristic (chars/4)        [or: Anthropic count_tokens API]

Always-loaded (every turn):                 ~N tokens
  CLAUDE.md                                  ~N tokens
  .claude/rules/code-quality.md  (alwaysApply)  ~N tokens
  .claude/rules/testing.md       (alwaysApply)  ~N tokens

Path-scoped (loaded near matched files):    ~N tokens (max, if every glob matches)
  .claude/rules/security.md      (paths: src/api/**, ...)  ~N tokens
  .claude/rules/frontend.md      (paths: **/*.tsx, ...)    ~N tokens

Invoked-only (zero per-turn cost):
  Cumulative size if every skill and agent loaded once: ~N tokens
  .claude/skills/<name>/SKILL.md   ~N tokens
  .claude/agents/<name>.md         ~N tokens

Top 3 always-loaded contributors:
  1. <file>   ~N tokens
  2. <file>   ~N tokens
  3. <file>   ~N tokens

Verdict: PASS / NEAR LIMIT / OVER BUDGET
```

If any class is over budget, end the report with the single highest-leverage trim recommendation.

## Budget guidance (used to compute the verdict)

| Class                          | Target              | Hard cap            | Action when over |
|-------------------------------|--------------------|--------------------|------------------|
| `CLAUDE.md`                   | <25 non-blank lines | <50 non-blank lines | Keep the dotclaude block tight; move detail into path-scoped rules. |
| Each `alwaysApply` rule       | <30 lines, ~250 tok | n/a                 | Push content to a path-scoped rule or into an agent. |
| Total always-loaded           | <1000 tokens        | <1500 tokens        | Identify the single biggest contributor and trim it. |

## Caveats to mention in the report

- The heuristic is approximate. Re-run with `--api` (requires `$ANTHROPIC_API_KEY`) for the exact count from Anthropic's tokenizer.
- Claude Code does not expose live context-window state to skills, so this report estimates what would load each turn for this configuration — not what's currently in your session window.
- Agents run in isolated context. Their prompt cost is per-invocation in their own session, not per-turn in your main thread.
- Skills cost zero until invoked. Most carry `disable-model-invocation: true`, so they fire only on `/name`.
- Path-scoped rules cost zero unless the conversation touches files matching their globs.
- Hooks add to context only when they print to stdout. dotclaude's hooks are silent on success by design.
