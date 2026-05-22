# Plans — two layers

Plans split the same way as everything else in dotclaude:

- **Generic plans** are reusable playbooks not tied to any one project. They live here, in the plugin (`plugins/dotclaude/templates/plans/`), and ship as reference material — open them when you start that kind of work. See the list below.
- **Project-specific plans** live in the consuming repo under `.claude/plans/`, which `/dotclaude:init` adds to the project's `.gitignore`. They're local working documents — the current implementation plan, a migration checklist for this repo — and aren't committed.

`/dotclaude:init` does **not** copy the generic plans into your project; they're a shared library. Reference them in place, or copy the relevant one into `.claude/plans/` and adapt it.

## Available generic playbooks

- [release.md](release.md) — cut and ship a release.
- [feature.md](feature.md) — take a feature from idea to merged PR.
