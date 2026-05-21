# Plans — two layers

Plans split the same way as everything else in dotclaude:

- **Generic plans** (reusable playbooks that aren't tied to one project) live here, in the plugin: `plugins/dotclaude/templates/plans/`. They ship with the plugin as reference material — open them when you start that kind of work. Examples below.
- **Project-specific plans** live in the consuming repo under `.claude/plans/`, which `/dotclaude:init` adds to the project's `.gitignore`. They're local working documents (the current implementation plan, a migration checklist for this repo), not committed.

`/dotclaude:init` does **not** copy these generic plans into your project — they're a shared library. Reference them, or copy the relevant one into `.claude/plans/` and adapt it.

## Available generic playbooks

- [release.md](release.md) — cut and ship a release.
- [feature.md](feature.md) — take a feature from idea to merged PR.
