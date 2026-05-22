---
name: debug-fix
description: Find and fix a bug. Default is careful (reproduce, investigate, test). Add `--fast` for emergency production mode (hotfix branch, minimal change, ship a PR fast).
argument-hint: "[issue, error, or description] [optional: --fast]"
disable-model-invocation: true
allowed-tools:
  - Bash(git *)
  - Bash(gh *)
  - Bash(make *)
  - Bash(uv sync)
  - Bash(uv run *)
  - Bash(npm run *)
  - Bash(npm install)
  - Bash(npm test *)
  - Read
  - Glob
  - Grep
  - Edit
  - Write
---

Find and fix the following issue:

**Problem**: $ARGUMENTS

## Mode

Check $ARGUMENTS for `--fast`, and strip it before parsing the problem description.

- **Default**: the careful debug-fix path. Use it when you have time to do this right.
- **--fast**: emergency hotfix. Use it when production is broken and shipping speed matters more than thoroughness. It branches `hotfix/*` from production, enforces minimal-change discipline, verifies with critical tests only, and ships a `[HOTFIX]` PR. Before committing to fast mode, briefly confirm with the user that this is genuinely emergency-grade; if not, suggest dropping `--fast`.

## Step 1: Understand

- Issue number: run `gh issue view $ARGUMENTS` (or the project's issue tracker).
- Error or stack trace: parse it for file, line, error type, and call chain.
- Description: identify expected vs. actual behavior.
- URL or screenshot: examine the referenced resource.

If anything is unclear, ask before proceeding.

## Step 2: Hotfix branch (--fast only)

In default mode, skip this step — branch creation happens in Step 7. In `--fast` mode:

- Detect the production branch with `git symbolic-ref refs/remotes/origin/HEAD` or `git remote show origin`.
- Stash uncommitted work if needed.
- Create and switch to `hotfix/<short-description>`, branched from production.
- **ASK** the user to confirm the branch name first.

## Step 3: Reproduce (default only)

In `--fast` mode, skip this step: trust the report and move to Step 5.

- Find the simplest way to trigger the issue (a test, curl, or script).
- Confirm you can reproduce it reliably.
- If you can't reproduce it:
  - **Environment-specific?** Check env vars, OS, runtime version, and database state.
  - **Intermittent?** Likely a race condition. Look for shared mutable state, timing dependencies, and async ordering assumptions.
  - **Already fixed?** Check `git log` for recent commits mentioning the issue.

## Step 4: Investigate (default only)

In `--fast` mode, skip this and go to Step 5: trust the report and keep investigation shallow.

Don't jump straight to guessing:

1. Locate the symptom. Which file and line produces the wrong output?
2. Read the code path backwards. What called this, and what data did it pass?
3. Check git history: `git log --oneline -20 -- <file>`, `git log --all --grep="<keyword>"`.
4. Narrow the scope with `git bisect` or a targeted grep.
5. Form a hypothesis: "X is wrong because Y."
6. Verify it with a targeted log or assertion.
7. If it's wrong, trace a different path. Don't keep retesting the same hypothesis.

## Step 5: Fix

- Make the smallest correct change.
- Don't patch symptoms. Trace back to where the bad data originates and fix it there.
- Don't refactor surrounding code while fixing.
- Don't add defensive checks that mask the problem.

In `--fast` mode specifically:
- If the fix needs more than ~50 lines changed, warn the user — this may not actually be a hotfix.
- Do NOT add features, change formatting, clean up unrelated issues, or add non-essential comments.

## Step 6: Verify

**Default**:
- Write a test that reproduces the bug and now passes.
- Run related tests to check for regressions.
- Run lint and typecheck.
- Temporarily revert your fix and confirm the new test fails — this proves the test catches the bug.

**--fast**:
- Run only the tests directly relevant to the changed code, not the full suite.
- Run the build.
- If you can reproduce the original error, confirm it's fixed.
- **ASK** the user whether they want extra verification before shipping.

## Step 7: Wrap up or ship

**Default**:
- Create a branch if you aren't already on one.
- Stage only the fix and test files.
- Commit: `fix: <what was wrong and why> (#number)`.

**--fast**:
- Stage only the fix files (never secrets, locks, or build output).
- Draft the commit `hotfix: <short description>`, then **ASK** the user to confirm.
- Push: `git push -u origin hotfix/<description>`.
- Create a PR targeting production:
  - Title: `[HOTFIX] <description>`.
  - Body: what broke, what caused it, and what this fixes.
  - Try to add the `hotfix` label with `gh pr create ... --label hotfix`. If that fails, proceed without the label.
- Show the PR URL.

## Rules

- NEVER skip a confirmation step in `--fast` mode (branch name, commit message, push).
- NEVER force-push.
- NEVER commit secrets or unrelated changes.
- If the user says "skip" at any step, skip it and move on.
- In `--fast` mode specifically: if the fix turns out to be complex, tell the user and suggest dropping `--fast` for the careful path.
