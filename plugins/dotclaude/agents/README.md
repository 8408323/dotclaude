# Agents

Agents are specialized Claude instances that run in **isolated context**. They don't see your conversation history or loaded rules — only their own system prompt and tools.

Claude delegates to an agent automatically based on the task description, or you can invoke one directly with `@agent-name`.

## Available agents

### frontend-designer
Builds distinctive, production-grade UI. It finds or creates design tokens first, picks a design principle, then builds the components. It has Write and Edit tools, so it actually generates files. Anti-AI-slop aesthetics are built in.

### security-reviewer
Reviews code for OWASP-style vulnerabilities: injection, broken auth, data exposure, weak crypto, and missing validation. It reports findings by severity, each with an exact file:line location and a specific fix.

### performance-reviewer
Finds real bottlenecks rather than theoretical micro-optimizations. It covers the database (N+1, missing indexes), memory (leaks, unbounded caches), computation (repeated work, blocking calls), network (sequential calls, missing timeouts), frontend (re-renders, bundle size), and concurrency (lock contention, missing pooling).

### code-reviewer
General code review aimed at specific bug patterns: off-by-one errors, null dereferences, inverted conditions, race conditions, swallowed errors, misleading names, and excessive complexity. It gives concrete examples for each category and skips style nitpicks.

### doc-reviewer
Reviews documentation for accuracy (do the docs match the code?), completeness (are required params documented?), staleness (do referenced APIs still exist?), and clarity. It cross-references the actual source using grep and file reads.

## Adding your own

Create a new `.md` file in this directory:

```yaml
---
name: your-agent-name
description: When Claude should delegate to this agent
tools:
  - Read
  - Grep
  - Glob
  - Bash
---

Your agent's system prompt here.
```

See [Claude Code docs](https://code.claude.com/docs/en/sub-agents) for all frontmatter options.
