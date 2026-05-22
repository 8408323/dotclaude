---
name: explain
description: Explain code. Default is a one-sentence summary plus a mental model. Add `verbose` to also get an ASCII diagram, key details, and a modification guide.
argument-hint: "[target] [verbose?]"
disable-model-invocation: true
---

Explain `$ARGUMENTS` clearly.

## Mode

If `$ARGUMENTS` includes the word `verbose` (for example, `/explain my-function verbose`), produce all five sections below. Strip the word `verbose` from the target name when deciding what to explain.

Otherwise (the default), produce only sections 1 and 2, then stop. Day-to-day, that's usually all you need.

## Sections

### 1. One-sentence summary
In one sentence: what does it do, and why does it exist?

### 2. Mental model
One short paragraph: an analogy or metaphor that captures the core idea, tied to something the developer already knows.

### 3. Visual diagram (verbose only)

Draw an ASCII diagram of the data and control flow. Keep it readable:

```
Input -> [Step A] -> [Step B] -> Output
              |
              v
        [Side Effect]
```

### 4. Key details (verbose only)

Walk through the important parts and skip the obvious ones. Focus on:

- Non-obvious decisions (why this approach?)
- Edge cases and gotchas
- Dependencies and side effects

### 5. How to modify it (verbose only)

What does someone need to know to change this code safely, and where are the landmines?
