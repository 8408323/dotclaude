---
description: Scaffold or update the dotclaude project-local layer (base rules, settings baseline, CLAUDE.md block, AGENTS.md, generated Copilot instructions, and GitHub AI-review workflows) into the current project. Use when setting up dotclaude in a repo or pulling base-config updates. Respects local ownership — never clobbers project-owned files.
argument-hint: "[--dry-run] [--no-github] [--no-rules] [--no-copilot]"
allowed-tools:
  - Bash(python3 *)
  - Read
  - Edit
  - Glob
---

# dotclaude:init

Scaffolds the **project-local layer** that the plugin itself cannot ship (Claude Code plugins carry hooks/agents/skills, but not `.claude/rules`, `settings.json` permissions, `CLAUDE.md`, `AGENTS.md`, Copilot instructions, or `.github/` workflows).

## What it does

Runs the deterministic sync engine bundled with the plugin:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/dotclaude-init/sync.py" $ARGUMENTS
```

It writes/updates, under the project root (`$CLAUDE_PROJECT_DIR`):

- `.claude/rules/*.md` — base rules (`code-quality`, `testing`, `security`, `error-handling`, `frontend`, `database`)
- `.claude/settings.json` — additive-merges the marketplace wiring (`extraKnownMarketplaces` + `enabledPlugins`) and a permission baseline
- `CLAUDE.md` — inserts/refreshes the managed dotclaude block
- `AGENTS.md` — cross-tool pointer file (Copilot, Claude, others)
- **Copilot layer, generated from the plugin (single source — edit the source in dotclaude, not these)**, skip all with `--no-copilot`:
  - instructions: always-on rules → `.github/copilot-instructions.md`; each path-scoped rule → `.github/instructions/<name>.instructions.md` with `applyTo`.
  - prompts: workflow skills → `.github/prompts/<name>.prompt.md` (`mode: agent`); skips Claude-Code-only skills (`context-budget`, `dotclaude-init`).
  - custom agents: reviewer agents → `.github/agents/<name>.md`.
- `.gitignore` — a managed block keeping project-local plans/overrides out of git (`.claude/plans/`, `CLAUDE.local.md`, `.claude/settings.local.json`)
- `.github/workflows/*.yml` — AI-review workflow templates (skip with `--no-github`)

## Ownership model (no clash)

- **Managed** files carry a `dotclaude:managed` marker and are regenerated on every run. To take local ownership of one, delete its marker line — sync then reports `skip-own` and never touches it again.
- **Unmarked** files are yours; sync never touches them.
- **settings.json** is additive-merged: base allow/deny + plugin wiring are ensured present; your entries are preserved (arrays unioned, your scalars win).
- **CLAUDE.md**: only the content between `<!-- dotclaude:begin -->` and `<!-- dotclaude:end -->` is replaced.

Copilot instructions and `.github/instructions/*` are **derived from `.claude/rules/`** — never hand-edit them; change the rule and re-run. Generic plans live in the plugin (`templates/plans/`); project plans go in the gitignored `.claude/plans/`.

## How to run

1. Confirm you're at the intended project root.
2. Run with `--dry-run` first and show the user the report.
3. If it looks right, run for real, then remind the user to delete rule files that don't fit their stack (e.g. `frontend.md`/`database.md` for a backend-only project) and to adjust `paths:` globs in `security.md`/`error-handling.md`. (Adjusting a rule's `paths:` automatically updates its generated `applyTo`.)
4. The GitHub workflows need repo secrets (`CLAUDE_CODE_OAUTH_TOKEN`, optionally `OPENAI_API_KEY` and the `_JH` fallbacks). Mention this; don't attempt to set secrets.

After a real run, tell the user to `/reload-plugins` (or restart) so new rules and settings load.
