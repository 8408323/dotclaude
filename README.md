# dotclaude

A reusable Claude Code dev environment — guardrail hooks, reviewer subagents, and workflow skills — shipped as a **plugin + marketplace**. An `init` skill scaffolds the project-local config a plugin can't carry on its own: rules, a settings baseline, a `CLAUDE.md` block, and GitHub AI-review workflows.

The result is one generic layer reused across every repo, plus a thin project-specific layer that **never clashes** with it. See [PLAN.md](PLAN.md) for the design and the ownership model.

## Install

```bash
# in any project
/plugin marketplace add 8408323/dotclaude
/plugin install dotclaude@dotclaude
/dotclaude:init           # scaffold rules, settings, CLAUDE.md block, .github workflows
/reload-plugins
```

Use `/dotclaude:init --dry-run` to preview changes. `--no-github` skips the workflow templates; `--no-rules` skips the base rules.

## What you get

- **Hooks** (run automatically): secret scan, dangerous-command block, file protection, build-artifact block, format-on-save, auto-test, session-start context, post-compaction recovery, desktop notify.
- **Agents**: `@security-reviewer`, `@code-reviewer`, `@performance-reviewer`, `@doc-reviewer`, `@frontend-designer`.
- **Skills**: `/dotclaude:tdd`, `/dotclaude:ship`, `/dotclaude:debug-fix`, `/dotclaude:pr-review`, `/dotclaude:refactor`, `/dotclaude:explain`, `/dotclaude:test-writer`, `/dotclaude:context-budget`, `/dotclaude:init`.
- **Base rules**, a **settings baseline**, a **CLAUDE.md block**, an **AGENTS.md**, and **GitHub AI-review workflows**, all scaffolded by `/dotclaude:init`.
- **A Copilot layer generated from a single source** — `.github/copilot-instructions.md` and `.github/instructions/*` from the rules, `.github/prompts/*.prompt.md` from the workflow skills, and `.github/agents/*.md` from the reviewer agents. Because these are generated rather than hand-duplicated, Claude and Copilot stay in sync.
- **Plans**: generic playbooks ship in the plugin (`templates/plans/`); project plans live in the gitignored `.claude/plans/`.

## Updating

```bash
/plugin update dotclaude@dotclaude     # engine (hooks/agents/skills)
/dotclaude:init                        # refresh the managed project-local layer
```

## Ownership in one line

Files marked `dotclaude:managed` are regenerated on init. Delete a file's marker to take local ownership, and dotclaude leaves it alone. `settings.json` is merged additively, and `CLAUDE.md` edits stay inside the dotclaude block.

## Develop

```bash
claude --plugin-dir ./plugins/dotclaude          # load locally
bash plugins/dotclaude/hooks/tests/run-all.sh    # 106 hook fixtures
python3 plugins/dotclaude/skills/dotclaude-init/test_sync.py
claude plugin validate ./plugins/dotclaude
```

## License

MIT — see [LICENSE](LICENSE).
