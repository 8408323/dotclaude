#!/usr/bin/env python3
"""Standalone tests for the dotclaude sync engine. Run: python3 test_sync.py"""

from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location("sync", Path(__file__).with_name("sync.py"))
sync = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync)

passed = 0


def check(name: str, cond: bool) -> None:
    global passed
    assert cond, f"FAIL: {name}"
    passed += 1


def test_merge_json():
    base = {"a": {"x": [1, 2]}, "k": 1}
    proj = {"a": {"x": [2, 3], "y": 9}, "k": 5, "own": True}
    out = sync.merge_json(base, proj)
    check("union lists preserving project order", out["a"]["x"] == [2, 3, 1])
    check("project scalar wins", out["k"] == 5)
    check("project-only keys kept", out["own"] is True and out["a"]["y"] == 9)


def test_is_managed():
    check("managed detected", sync.is_managed("---\npaths: []\n---\n<!-- dotclaude:managed -->\n# r"))
    check("unmanaged detected", not sync.is_managed("---\n---\n# plain rule"))


def test_managed_overwrite_and_ownership():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        rep = sync.Report()
        src = root / "src.md"
        src.write_text("---\n---\n<!-- dotclaude:managed -->\nNEW")
        dst = root / "dst.md"
        # create
        sync.sync_managed_file(src, dst, root, rep, dry=False)
        check("created", dst.read_text().endswith("NEW"))
        # managed update
        dst.write_text("---\n---\n<!-- dotclaude:managed -->\nOLD")
        sync.sync_managed_file(src, dst, root, rep, dry=False)
        check("managed overwritten", dst.read_text().endswith("NEW"))
        # ownership: drop marker -> never touched
        dst.write_text("MINE")
        sync.sync_managed_file(src, dst, root, rep, dry=False)
        check("project ownership respected", dst.read_text() == "MINE")


def test_claude_block_replace():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        rep = sync.Report()
        tpl = root / "block.md"
        tpl.write_text("<!-- dotclaude:begin -->\nV2\n<!-- dotclaude:end -->")
        dst = root / "CLAUDE.md"
        dst.write_text("# Proj\nkeep me\n<!-- dotclaude:begin -->\nV1\n<!-- dotclaude:end -->\ntail")
        sync.sync_claude_block(tpl, dst, root, rep, dry=False)
        out = dst.read_text()
        check("block replaced", "V2" in out and "V1" not in out)
        check("project content kept", "keep me" in out and "tail" in out)


for fn in [test_merge_json, test_is_managed, test_managed_overwrite_and_ownership, test_claude_block_replace]:
    fn()
print(f"OK — {passed} checks passed")
