#!/usr/bin/env python3
"""Scaffold/update the dotclaude project-local layer into a target project.

Implements the dotclaude ownership model so the generic layer and the
project-specific layer never clash:

  - Managed files carry a `dotclaude:managed` marker. They are (over)written
    on every run. Delete the marker line in a file to take local ownership;
    this tool then leaves it alone.
  - Unmarked files are project-owned and never touched.
  - settings.json is additive-merged: base allow/deny entries and the
    marketplace/plugin wiring are ensured present, project entries are kept.
  - The CLAUDE.md block (and the .gitignore block) is replaced only between
    its begin/end markers; everything else is left intact.

Copilot instructions are GENERATED from the Claude rules (single source):
always-on rules -> .github/copilot-instructions.md; path-scoped rules ->
.github/instructions/<name>.instructions.md (with applyTo). Edit the rule, not
the generated copy.

Stdlib only. Safe to re-run (idempotent).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

MARKER = "dotclaude:managed"
BLOCK_BEGIN = "<!-- dotclaude:begin"
BLOCK_END = "dotclaude:end -->"


def find_templates() -> Path:
    # sync.py lives at <plugin>/skills/dotclaude-init/sync.py; templates at <plugin>/templates
    return (Path(__file__).resolve().parent.parent.parent / "templates").resolve()


def is_managed(text: str) -> bool:
    return MARKER in text.split("\n\n", 1)[0] if text else False


class Report:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def add(self, action: str, path: Path, root: Path) -> None:
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = path
        self.lines.append(f"  {action:9s} {rel}")

    def render(self) -> str:
        return "\n".join(self.lines) if self.lines else "  (nothing to do)"


def write_managed(dst: Path, content: str, root: Path, rep: Report, dry: bool) -> None:
    """Write managed content to dst, respecting local ownership (marker removed)."""
    if dst.exists():
        cur = dst.read_text()
        if not is_managed(cur):
            rep.add("skip-own", dst, root)
            return
        if cur == content:
            rep.add("unchanged", dst, root)
            return
        rep.add("update", dst, root)
    else:
        rep.add("create", dst, root)
    if not dry:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(content)


def sync_managed_file(src: Path, dst: Path, root: Path, rep: Report, dry: bool) -> None:
    write_managed(dst, src.read_text(), root, rep, dry)


def merge_json(base, proj):
    """Additive deep merge: never drop project data.

    - dicts: recurse; base ensures its keys exist, project scalar wins if set.
    - lists: union preserving project order, appending base items not present.
    - scalars: keep project value if present; otherwise take base.
    """
    if isinstance(base, dict) and isinstance(proj, dict):
        out = dict(proj)
        for k, v in base.items():
            out[k] = merge_json(v, proj[k]) if k in proj else v
        return out
    if isinstance(base, list) and isinstance(proj, list):
        out = list(proj)
        for item in base:
            if item not in out:
                out.append(item)
        return out
    return proj


def sync_settings(tpl: Path, dst: Path, root: Path, rep: Report, dry: bool) -> None:
    base = json.loads(tpl.read_text())
    proj = json.loads(dst.read_text()) if dst.exists() else {}
    merged = merge_json(base, proj)
    if merged == proj:
        rep.add("unchanged", dst, root)
        return
    rep.add("merge" if dst.exists() else "create", dst, root)
    if not dry:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(json.dumps(merged, indent=2) + "\n")


def sync_block(block: str, dst: Path, begin: str, end: str, root: Path, rep: Report, dry: bool) -> None:
    """Insert/replace a marker-delimited block; leave the rest of the file intact."""
    block = block.strip("\n")
    if not dst.exists():
        rep.add("create", dst, root)
        if not dry:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(block + "\n")
        return
    cur = dst.read_text()
    if begin in cur and end in cur:
        pre = cur[: cur.index(begin)]
        post = cur[cur.index(end) + len(end):]
        rebuilt = pre + block + post
        if rebuilt == cur:
            rep.add("unchanged", dst, root)
            return
        rep.add("update", dst, root)
        if not dry:
            dst.write_text(rebuilt)
    else:
        rep.add("append", dst, root)
        if not dry:
            sep = "" if cur.endswith("\n\n") else ("\n" if cur.endswith("\n") else "\n\n")
            dst.write_text(cur + sep + block + "\n")


# ── Rule parsing & Copilot generation ─────────────────────────────────────────

def parse_rule(text: str):
    """Return (always_apply, paths, body) for a Claude rule file.

    Minimal YAML-frontmatter reader: handles `alwaysApply: true` and a `paths:`
    block list. The body has its frontmatter and dotclaude:managed marker stripped.
    """
    always = False
    paths: list[str] = []
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            fm = text[3:end]
            body = text[end + 4:].lstrip("\n")
            in_paths = False
            for line in fm.splitlines():
                s = line.strip()
                if s.startswith("alwaysApply:"):
                    always = "true" in s.split(":", 1)[1].lower()
                    in_paths = False
                elif s.startswith("paths:"):
                    in_paths = True
                elif in_paths and s.startswith("- "):
                    paths.append(s[2:].strip().strip("\"'"))
                elif s and not s.startswith("-"):
                    in_paths = False
    body = "\n".join(ln for ln in body.splitlines() if MARKER not in ln).strip("\n")
    return always, paths, body


def generate_copilot(rules_dir: Path, header_tpl: Path, root: Path, rep: Report, dry: bool) -> None:
    """Generate Copilot instruction files from the project's Claude rules."""
    if not rules_dir.is_dir():
        return
    always_bodies: list[str] = []
    path_scoped: list[tuple[str, list[str], str]] = []
    for f in sorted(rules_dir.glob("*.md")):
        if f.name == "README.md":
            continue
        always, paths, body = parse_rule(f.read_text())
        if not body:
            continue
        if always:
            always_bodies.append(body)
        elif paths:
            path_scoped.append((f.stem, paths, body))

    # Repo-wide: header + always-on rule bodies.
    header = header_tpl.read_text().strip("\n") if header_tpl.exists() else (
        f"<!-- {MARKER} — generated by /dotclaude:init. -->\n# Copilot Instructions"
    )
    parts = [header, *always_bodies]
    content = "\n\n".join(p.strip("\n") for p in parts if p).rstrip("\n") + "\n"
    write_managed(root / ".github" / "copilot-instructions.md", content, root, rep, dry)

    # Path-scoped: one .instructions.md per rule, mapping paths -> applyTo.
    for name, paths, body in path_scoped:
        apply_to = ",".join(paths)
        gen = (
            f"---\napplyTo: \"{apply_to}\"\n---\n"
            f"<!-- {MARKER} — generated from .claude/rules/{name}.md by /dotclaude:init. "
            f"Edit the rule, not this file. -->\n\n{body}\n"
        )
        write_managed(root / ".github" / "instructions" / f"{name}.instructions.md", gen, root, rep, dry)


# Skills that are Claude-Code-specific and don't translate to a Copilot prompt.
SKILL_PROMPT_SKIP = {"context-budget", "dotclaude-init"}

# Claude-Code-isms rewritten when generating Copilot prompts (longest keys first).
PROMPT_REWRITES = {
    "$ARGUMENTS": "${input:args}",
    "AskUserQuestion tool": "an interactive confirmation",
    "AskUserQuestion": "an interactive confirmation",
    "/dotclaude:": "/",
}


def split_frontmatter(text: str):
    """Return ({key: value}, body) for a markdown file with simple `key: value` frontmatter.

    Only top-level scalar keys are read (enough for `description`/`name`); the
    dotclaude:managed marker is stripped from the body.
    """
    fields: dict[str, str] = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].splitlines():
                if ":" in line and not line[:1].isspace() and not line.startswith("-"):
                    k, _, v = line.partition(":")
                    fields[k.strip()] = v.strip().strip("\"'")
            body = text[end + 4:].lstrip("\n")
    body = "\n".join(ln for ln in body.splitlines() if MARKER not in ln).strip("\n")
    return fields, body


def _derived_marker(source: str) -> str:
    return (f"<!-- {MARKER} — generated from the dotclaude {source} by /dotclaude:init. "
            f"Edit the source in the dotclaude repo, not this file. -->")


def generate_copilot_prompts(skills_dir: Path, root: Path, rep: Report, dry: bool) -> None:
    """Emit .github/prompts/<name>.prompt.md from the plugin's workflow skills."""
    if not skills_dir.is_dir():
        return
    for d in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        skill = d / "SKILL.md"
        if not skill.exists() or d.name in SKILL_PROMPT_SKIP:
            continue
        fields, body = split_frontmatter(skill.read_text())
        desc = fields.get("description", d.name)
        for old, new in PROMPT_REWRITES.items():
            body = body.replace(old, new)
        # GitHub Copilot prompt files select agent mode via the `agent` key (not `mode`).
        out = (f"---\nagent: 'agent'\ndescription: {json.dumps(desc)}\n---\n"
               f"{_derived_marker(d.name + ' skill')}\n\n{body}\n")
        write_managed(root / ".github" / "prompts" / f"{d.name}.prompt.md", out, root, rep, dry)


def generate_copilot_agents(agents_dir: Path, root: Path, rep: Report, dry: bool) -> None:
    """Emit .github/agents/<name>.md from the plugin's reviewer agents."""
    if not agents_dir.is_dir():
        return
    for f in sorted(agents_dir.glob("*.md")):
        if f.name == "README.md":
            continue
        fields, body = split_frontmatter(f.read_text())
        desc = fields.get("description", f.stem)
        # Drop Claude tool names; Copilot custom agents use their own tool set (default if omitted).
        out = (f"---\ndescription: {json.dumps(desc)}\n---\n"
               f"{_derived_marker(f.stem + ' agent')}\n\n{body}\n")
        write_managed(root / ".github" / "agents" / f"{f.stem}.md", out, root, rep, dry)


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync the dotclaude project-local layer.")
    ap.add_argument("--project", default=None, help="target project root (default: $CLAUDE_PROJECT_DIR or cwd)")
    ap.add_argument("--dry-run", action="store_true", help="show what would change, write nothing")
    ap.add_argument("--no-github", action="store_true", help="skip .github workflow templates")
    ap.add_argument("--no-rules", action="store_true", help="skip .claude/rules base files")
    ap.add_argument("--no-copilot", action="store_true", help="skip generating Copilot instructions")
    ap.add_argument("--no-claude", action="store_true", help="skip the CLAUDE.md block (for projects that hand-manage CLAUDE.md)")
    args = ap.parse_args()

    root = Path(args.project or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()
    tpl = find_templates()
    if not tpl.is_dir():
        print(f"error: templates not found at {tpl}", file=sys.stderr)
        return 1

    rep = Report()
    mode = " (dry-run)" if args.dry_run else ""
    print(f"dotclaude sync → {root}{mode}\n")

    if not args.no_rules:
        for src in sorted((tpl / "rules").glob("*.md")):
            sync_managed_file(src, root / ".claude" / "rules" / src.name, root, rep, args.dry_run)

    sync_settings(tpl / "settings.base.json", root / ".claude" / "settings.json", root, rep, args.dry_run)
    sync_managed_file(tpl / "AGENTS.md", root / "AGENTS.md", root, rep, args.dry_run)
    sync_managed_file(tpl / "github" / "pull_request_template.md",
                      root / ".github" / "pull_request_template.md", root, rep, args.dry_run)
    if not args.no_claude:
        sync_block(
            (tpl / "CLAUDE.block.md").read_text(), root / "CLAUDE.md",
            BLOCK_BEGIN, BLOCK_END, root, rep, args.dry_run,
        )

    # Project plans are local working docs — keep them out of git.
    sync_block(
        "# dotclaude:begin\n.claude/plans/\nCLAUDE.local.md\n.claude/settings.local.json\n# dotclaude:end",
        root / ".gitignore", "# dotclaude:begin", "# dotclaude:end", root, rep, args.dry_run,
    )

    # Copilot layer, generated from the Claude rules / skills / agents (single source).
    if not args.no_copilot:
        plugin = tpl.parent  # <plugin>/templates → <plugin>
        generate_copilot(
            root / ".claude" / "rules", tpl / "github" / "copilot-instructions.header.md",
            root, rep, args.dry_run,
        )
        generate_copilot_prompts(plugin / "skills", root, rep, args.dry_run)
        generate_copilot_agents(plugin / "agents", root, rep, args.dry_run)

    if not args.no_github:
        for src in sorted((tpl / "github" / "workflows").glob("*.yml")):
            sync_managed_file(src, root / ".github" / "workflows" / src.name, root, rep, args.dry_run)

    print(rep.render())
    print("\nLegend: create=new  update=managed changed  merge=settings merged  "
          "append=block added  skip-own=you own it (untouched)  unchanged=already current")
    if not args.dry_run:
        print("\nNext: reload Claude Code (or /reload-plugins) so new rules/settings take effect.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
