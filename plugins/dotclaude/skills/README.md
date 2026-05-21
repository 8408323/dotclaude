# Skills

Skills are slash commands. As plugin skills they are namespaced — invoke them as `/dotclaude:<name>` (e.g. `/dotclaude:tdd`). They run in the main conversation context, so they see all loaded rules and `CLAUDE.md`.

- `disable-model-invocation: true` means manual only. You type the command to trigger.
- Without that flag, Claude can also trigger the skill automatically when relevant.

## Available skills

### /dotclaude:init [--dry-run] [--no-github] [--no-rules]
**Trigger**: Manual only

Scaffold or update the project-local layer the plugin can't ship: base rules, a `settings.json` baseline (marketplace wiring + permissions), the `CLAUDE.md` block, and the GitHub AI-review workflows. Respects the ownership model — managed files are regenerated, files you've taken ownership of (marker deleted) are left alone, and `settings.json` is additive-merged. Run after installing the plugin, and again to pull base-config updates.

### /debug-fix [issue, error, or description] [--fast]
**Trigger**: Manual only

Find and fix a bug. Default is the careful path: understand, reproduce, investigate, fix, verify, commit. Add `--fast` for emergency production mode: creates a `hotfix/` branch from production, makes the smallest correct change (no refactoring), runs only critical tests, and ships a `[HOTFIX]` PR. Warns if the fix is too complex for fast mode.

### /ship [optional message]
**Trigger**: Manual only

Full shipping workflow with confirmation at every step: scan changes, stage and commit, push, create PR. Proposes commit messages and PR descriptions. Blocks secrets, force-push, and push to main.

### /pr-review [PR number | staged | file path]
**Trigger**: Manual only

Reviews code changes by delegating to specialist agents (`@code-reviewer`, `@security-reviewer`, `@performance-reviewer`, `@doc-reviewer`). When given a PR number (or auto-detected from branch), also checks PR title, description quality, CI status, unresolved comments, and size. Ends with a clear merge or needs-changes verdict. Also works on staged changes or specific files for pre-PR review.

### /tdd [feature description]
**Trigger**: Manual only

Strict Test-Driven Development loop. Red: write a failing test for the smallest next behavior. Green: write the minimum code to pass. Refactor: clean up without changing behavior. Repeat. Commits after each green-plus-refactor cycle.

### /explain [file, function, or concept]
**Trigger**: Manual only

Explains code with a one-sentence summary, a mental model analogy, an ASCII diagram, key details, and a modification guide.

### /refactor [target]
**Trigger**: Manual only

Safe refactoring with tests as a safety net. Writes tests first if none exist, makes changes in small testable steps, verifies no behavior change.

### /test-writer
**Trigger**: Automatic (when new features are added)

Writes comprehensive tests covering every code path: happy path, edge cases, nulls, type boundaries, error paths, concurrency, state transitions. Covers API endpoints, UI components, database operations, and async. Verifies tests actually catch bugs by breaking the code.

### /context-budget [--api]
**Trigger**: Manual only

Estimates the per-turn token cost of this project's `.claude/` configuration and `CLAUDE.md`. Reports always-loaded files (rules with `alwaysApply` plus `CLAUDE.md`), path-scoped rules, and invoked-only agents and skills. Ranks the top contributors and flags entries over budget. Default uses Anthropic's documented `chars/4` heuristic. Add `--api` to call Anthropic's `count_tokens` endpoint for exact counts (requires `$ANTHROPIC_API_KEY`).

## Adding your own

Create a directory with a `SKILL.md` file:

```
your-skill/
└── SKILL.md
```

```yaml
---
name: your-skill
description: What it does and when to use it
disable-model-invocation: true
---

Your instructions here. Use $ARGUMENTS for user input.
```

See [Claude Code docs](https://code.claude.com/docs/en/skills) for all frontmatter options.
