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
  - The CLAUDE.md block is replaced only between its begin/end markers;
    everything else in CLAUDE.md is left intact.

Stdlib only. Safe to re-run (idempotent).
"""

from __future__ import annotations

import argparse
import json
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


def sync_managed_file(src: Path, dst: Path, root: Path, rep: Report, dry: bool) -> None:
    """Copy a managed template file, respecting local ownership."""
    new = src.read_text()
    if dst.exists():
        cur = dst.read_text()
        if not is_managed(cur):
            rep.add("skip-own", dst, root)  # project took ownership
            return
        if cur == new:
            rep.add("unchanged", dst, root)
            return
        rep.add("update", dst, root)
    else:
        rep.add("create", dst, root)
    if not dry:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(new)


def merge_json(base, proj):
    """Additive deep merge: never drop project data.

    - dicts: recurse, base only fills missing keys' subtrees but ensures its
      own keys exist (project scalar wins if already set).
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
    return proj  # scalar / type mismatch: project wins


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


def sync_claude_block(tpl: Path, dst: Path, root: Path, rep: Report, dry: bool) -> None:
    block = tpl.read_text().strip("\n")
    if not dst.exists():
        rep.add("create", dst, root)
        if not dry:
            dst.write_text(block + "\n")
        return
    cur = dst.read_text()
    if BLOCK_BEGIN in cur and BLOCK_END in cur:
        pre = cur[: cur.index(BLOCK_BEGIN)]
        post = cur[cur.index(BLOCK_END) + len(BLOCK_END):]
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


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync the dotclaude project-local layer.")
    ap.add_argument("--project", default=None, help="target project root (default: $CLAUDE_PROJECT_DIR or cwd)")
    ap.add_argument("--dry-run", action="store_true", help="show what would change, write nothing")
    ap.add_argument("--no-github", action="store_true", help="skip .github workflow templates")
    ap.add_argument("--no-rules", action="store_true", help="skip .claude/rules base files")
    args = ap.parse_args()

    import os
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
    sync_claude_block(tpl / "CLAUDE.block.md", root / "CLAUDE.md", root, rep, args.dry_run)

    if not args.no_github:
        for src in sorted((tpl / "github" / "workflows").glob("*.yml")):
            sync_managed_file(src, root / ".github" / "workflows" / src.name, root, rep, args.dry_run)
        ci = tpl / "github" / "copilot-instructions.md"
        if ci.exists():
            sync_managed_file(ci, root / ".github" / "copilot-instructions.md", root, rep, args.dry_run)

    print(rep.render())
    print("\nLegend: create=new  update=managed file changed  merge=settings merged  "
          "append=CLAUDE.md block added  skip-own=you own it (untouched)  unchanged=already current")
    if not args.dry_run:
        print("\nNext: reload Claude Code (or /reload-plugins) so new rules/settings take effect.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
