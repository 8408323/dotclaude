# dotclaude

A reusable Claude Code dev environment — guardrail hooks, reviewer subagents, and workflow skills — packaged as a **plugin + marketplace**, with an `init` skill that scaffolds the project-local config a plugin can't ship (rules, settings baseline, `CLAUDE.md` block, GitHub AI-review workflows).

One generic layer, reused across repos; a thin project-specific layer that **never clashes** with it. See [PLAN.md](PLAN.md) for the design and the ownership model.

## Install

```bash
# in any project
/plugin marketplace add 8408323/dotclaude
/plugin install dotclaude@dotclaude
/dotclaude:init           # scaffold rules, settings, CLAUDE.md block, .github workflows
/reload-plugins
```

`/dotclaude:init --dry-run` previews changes. `--no-github` skips workflow templates; `--no-rules` skips base rules.

## What you get

- **Hooks** (auto): secret scan, dangerous-command block, file protection, build-artifact block, format-on-save, auto-test, session-start context, post-compaction recovery, desktop notify.
- **Agents**: `@security-reviewer`, `@code-reviewer`, `@performance-reviewer`, `@doc-reviewer`, `@frontend-designer`.
- **Skills**: `/dotclaude:tdd`, `/dotclaude:ship`, `/dotclaude:debug-fix`, `/dotclaude:pr-review`, `/dotclaude:refactor`, `/dotclaude:explain`, `/dotclaude:test-writer`, `/dotclaude:context-budget`, `/dotclaude:init`.
- **Base rules** + **settings baseline** + **CLAUDE.md block** + **AGENTS.md** + **GitHub AI-review workflows**, scaffolded by `/dotclaude:init`.
- **Copilot instructions generated from the Claude rules** — `.github/copilot-instructions.md` (always-on) and `.github/instructions/*.instructions.md` (path-scoped `applyTo`). Single source, so Claude and Copilot never drift.
- **Plans**: generic playbooks ship in the plugin (`templates/plans/`); project plans live in the gitignored `.claude/plans/`.

## Updating

```bash
/plugin update dotclaude@dotclaude     # engine (hooks/agents/skills)
/dotclaude:init                        # refresh the managed project-local layer
```

## Ownership in one line

Files marked `dotclaude:managed` are regenerated on init; delete a file's marker to take local ownership and dotclaude will leave it alone. `settings.json` is additive-merged. `CLAUDE.md` changes are confined to the dotclaude block.

## Develop

```bash
claude --plugin-dir ./plugins/dotclaude          # load locally
bash plugins/dotclaude/hooks/tests/run-all.sh    # 106 hook fixtures
python3 plugins/dotclaude/skills/dotclaude-init/test_sync.py
claude plugin validate ./plugins/dotclaude
```

## License

MIT — see [LICENSE](LICENSE).
