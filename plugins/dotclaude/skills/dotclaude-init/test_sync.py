#!/usr/bin/env python3
"""Standalone tests for the dotclaude sync engine. Run: python3 test_sync.py"""

from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location("sync", Path(__file__).with_name("sync.py"))
assert _spec and _spec.loader
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


def test_block_replace():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        rep = sync.Report()
        dst = root / "CLAUDE.md"
        dst.write_text("# Proj\nkeep me\n<!-- dotclaude:begin -->\nV1\n<!-- dotclaude:end -->\ntail")
        sync.sync_block("<!-- dotclaude:begin -->\nV2\n<!-- dotclaude:end -->", dst,
                        sync.BLOCK_BEGIN, sync.BLOCK_END, root, rep, dry=False)
        out = dst.read_text()
        check("block replaced", "V2" in out and "V1" not in out)
        check("project content kept", "keep me" in out and "tail" in out)


def test_parse_rule():
    always, paths, body = sync.parse_rule(
        "---\nalwaysApply: true\n---\n<!-- dotclaude:managed -->\n# Code\n- be terse")
    check("always-on detected", always and not paths)
    check("marker + frontmatter stripped from body", "dotclaude:managed" not in body and "be terse" in body)
    always2, paths2, _ = sync.parse_rule(
        "---\npaths:\n  - \"src/**\"\n  - \"lib/**\"\n---\n# Sec\nvalidate")
    check("path-scoped parsed", not always2 and paths2 == ["src/**", "lib/**"])


def test_generate_copilot():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        rep = sync.Report()
        rules = root / ".claude" / "rules"
        rules.mkdir(parents=True)
        (rules / "code-quality.md").write_text("---\nalwaysApply: true\n---\n<!-- dotclaude:managed -->\n# CQ\n- no dead code")
        (rules / "security.md").write_text("---\npaths:\n  - \"app/**\"\n---\n<!-- dotclaude:managed -->\n# Sec\n- validate input")
        header = root / "header.md"
        header.write_text("<!-- dotclaude:managed -->\n# Copilot Instructions")
        sync.generate_copilot(rules, header, root, rep, dry=False)
        ci = (root / ".github" / "copilot-instructions.md").read_text()
        check("repo-wide includes header + always-on body", "Copilot Instructions" in ci and "no dead code" in ci)
        check("repo-wide excludes path-scoped body", "validate input" not in ci)
        inst = (root / ".github" / "instructions" / "security.instructions.md").read_text()
        check("path-scoped applyTo mapped", 'applyTo: "app/**"' in inst and "validate input" in inst)
        check("generated files carry managed marker", sync.MARKER in ci and sync.MARKER in inst)


def test_split_frontmatter():
    fields, body = sync.split_frontmatter(
        "---\nname: ship\ndescription: Ship it\nallowed-tools:\n  - Bash\n---\n<!-- dotclaude:managed -->\n# Ship\ndo $ARGUMENTS")
    check("scalar fields read", fields["name"] == "ship" and fields["description"] == "Ship it")
    check("list keys + marker not in body", "allowed-tools" not in body and "dotclaude:managed" not in body and "do $ARGUMENTS" in body)


def test_generate_copilot_prompts_and_agents():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        rep = sync.Report()
        skills = root / "plugin" / "skills"
        (skills / "ship").mkdir(parents=True)
        (skills / "ship" / "SKILL.md").write_text("---\nname: ship\ndescription: Ship changes\n---\n# Ship\nUse $ARGUMENTS to title it")
        (skills / "context-budget").mkdir()
        (skills / "context-budget" / "SKILL.md").write_text("---\ndescription: budget\n---\nclaude-only")
        agents = root / "plugin" / "agents"
        agents.mkdir(parents=True)
        (agents / "code-reviewer.md").write_text("---\nname: code-reviewer\ndescription: Reviews code\ntools:\n  - Read\n---\nReview for bugs")
        (agents / "README.md").write_text("# Agents")
        sync.generate_copilot_prompts(skills, root, rep, dry=False)
        sync.generate_copilot_agents(agents, root, rep, dry=False)
        prompt = (root / ".github" / "prompts" / "ship.prompt.md").read_text()
        check("prompt uses agent frontmatter key + description", "agent: 'agent'" in prompt and "mode: agent" not in prompt and "Ship changes" in prompt)
        check("prompt maps $ARGUMENTS to copilot input", "${input:args}" in prompt and "$ARGUMENTS" not in prompt)
        check("claude-only skill skipped", not (root / ".github" / "prompts" / "context-budget.prompt.md").exists())
        agent = (root / ".github" / "agents" / "code-reviewer.md").read_text()
        check("agent has description + body, no claude tools frontmatter", "Reviews code" in agent and "Review for bugs" in agent and "Read" not in agent.split("\n\n")[0])
        check("agents README skipped", not (root / ".github" / "agents" / "README.md").exists())
        check("generated files are managed", sync.MARKER in prompt and sync.MARKER in agent)


for fn in [test_merge_json, test_is_managed, test_managed_overwrite_and_ownership,
           test_block_replace, test_parse_rule, test_generate_copilot,
           test_split_frontmatter, test_generate_copilot_prompts_and_agents]:
    fn()
print(f"OK — {passed} checks passed")
