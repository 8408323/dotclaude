# Skills

Skills are slash commands. As plugin skills they are namespaced, so you invoke them as `/dotclaude:<name>` (e.g. `/dotclaude:tdd`). They run in the main conversation context, so they see all loaded rules and `CLAUDE.md`.

- `disable-model-invocation: true` means manual only: you type the command to trigger it.
- Without that flag, Claude can also trigger the skill automatically when it's relevant.

## Available skills

### /dotclaude:init [--dry-run] [--no-github] [--no-rules]
**Trigger**: Manual only

Scaffolds or updates the project-local layer the plugin can't ship: base rules, a `settings.json` baseline (marketplace wiring + permissions), the `CLAUDE.md` block, and the GitHub AI-review workflows. It respects the ownership model — managed files are regenerated, files you've taken ownership of (marker deleted) are left alone, and `settings.json` is additively merged. Run it after installing the plugin, and again to pull base-config updates.

### /dotclaude:debug-fix [issue, error, or description] [--fast]
**Trigger**: Manual only

Finds and fixes a bug. The default is the careful path: understand, reproduce, investigate, fix, verify, commit. Add `--fast` for emergency production mode: it creates a `hotfix/` branch from production, makes the smallest correct change (no refactoring), runs only critical tests, and ships a `[HOTFIX]` PR. It warns you if the fix is too complex for fast mode.

### /dotclaude:ship [optional message]
**Trigger**: Manual only

The full shipping workflow, with confirmation at every step: scan changes, stage and commit, push, create the PR. It proposes commit messages and PR descriptions, and blocks secrets, force-push, and push to main.

### /dotclaude:pr-review [PR number | staged | file path]
**Trigger**: Manual only

Reviews code changes by delegating to specialist agents (`@code-reviewer`, `@security-reviewer`, `@performance-reviewer`, `@doc-reviewer`). Given a PR number (or one auto-detected from the branch), it also checks the PR title, description quality, CI status, unresolved comments, and size, and ends with a clear merge or needs-changes verdict. It also works on staged changes or specific files for a pre-PR review.

### /dotclaude:tdd [feature description]
**Trigger**: Manual only

A strict Test-Driven Development loop. Red: write a failing test for the smallest next behavior. Green: write the minimum code to pass. Refactor: clean up without changing behavior. Repeat, committing after each green-plus-refactor cycle.

### /dotclaude:explain [file, function, or concept]
**Trigger**: Manual only

Explains code with a one-sentence summary, a mental-model analogy, an ASCII diagram, key details, and a modification guide.

### /dotclaude:refactor [target]
**Trigger**: Manual only

Safe refactoring with tests as a safety net. It writes tests first if none exist, makes changes in small testable steps, and verifies that behavior doesn't change.

### /dotclaude:test-writer
**Trigger**: Automatic (when new features are added)

Writes comprehensive tests covering every code path: happy path, edge cases, nulls, type boundaries, error paths, concurrency, and state transitions. It covers API endpoints, UI components, database operations, and async code, and verifies the tests actually catch bugs by breaking the code.

### /dotclaude:context-budget [--api]
**Trigger**: Manual only

Estimates the per-turn token cost of this project's `.claude/` configuration and `CLAUDE.md`. It reports always-loaded files (rules with `alwaysApply` plus `CLAUDE.md`), path-scoped rules, and invoked-only agents and skills, ranks the top contributors, and flags entries over budget. By default it uses Anthropic's documented `chars/4` heuristic; add `--api` to call Anthropic's `count_tokens` endpoint for exact counts (requires `$ANTHROPIC_API_KEY`).

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
