---
name: refactor
description: Safely refactor code with test coverage as a safety net
argument-hint: "[target to refactor. File, function, or pattern]"
disable-model-invocation: true
---

Refactor `$ARGUMENTS` safely.

## Process

### 1. Understand the current state
- Read the code and its tests
- Identify what the code does, who calls it, and what it depends on
- If there are no tests, WRITE TESTS FIRST. You need a safety net before changing anything

### 2. Plan the refactoring
- State what you're changing and why (clearer naming, less duplication, better structure)
- List the specific transformations (extract function, inline variable, move module, etc.)
- Check whether this changes any external behavior. If it does, it isn't a refactor — reconsider.

### 3. Make changes in small, testable steps
- One transformation at a time
- Run the tests after EACH step, not just at the end
- If a test breaks, undo the last step and make a smaller change

### 4. Verify
- All existing tests pass
- Lint and typecheck pass
- The public API is unchanged (unless changing it was the explicit goal)
- The code is objectively simpler: fewer lines, fewer branches, clearer names

## Rules
- If you can't run the tests, don't refactor
- Never mix refactoring with behavior changes in the same commit
- If the refactoring is large (10+ files), split it across multiple commits
