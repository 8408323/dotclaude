---
name: test-writer
description: Write comprehensive tests for new or changed code. Use automatically when new features are added, functions are created, or behavior is modified.
# No disable-model-invocation. Claude can auto-trigger this when adding features.
# Add "disable-model-invocation: true" below if you prefer manual-only via /dotclaude:test-writer.
---

Write comprehensive tests for the code that was just added or changed.

## Step 1: Discover What Changed

- Check `git diff` and `git diff --cached` to find new and modified functions, classes, and modules
- Read each changed file to understand the behavior being added
- Find the project's existing test files to learn its test framework, patterns, and conventions
- Place new test files next to the source files or in the project's established test directory — match whatever the project already does

## Step 2: Analyze Every Code Path

For each new or modified function, method, or component, map out:

- **Happy path**: normal input, expected output
- **Edge cases**: empty input, single element, boundary values (0, 1, -1, MAX_INT)
- **Null/undefined/nil**: what happens with missing data
- **Type boundaries**: wrong types, type-coercion traps
- **Error paths**: invalid input, network failures, timeouts, permission denied
- **Concurrency**: race conditions, parallel calls with shared state
- **State transitions**: initial, intermediate, and final states
- **Integration points**: how this code interacts with its dependencies

## Step 3: Write the Tests

Write a test for EACH scenario identified above. No skipping.

### Structure

- **One behavior per test**. Multiple related asserts on the same observed output are fine — that's the established style in this repo's pytest suite. If a test name needs "and", split it into two tests; that signals two behaviors, not two assertions.
- **Descriptive names**. Test names read as sentences that describe the behavior:
  - `should return empty array when input is empty`
  - `should throw ValidationError when email format is invalid`
  - `should retry 3 times before failing on network timeout`
- **Arrange-Act-Assert**. Set up, execute, verify — kept clearly separate.

### What to Test

**Pure functions / business logic:**
- Every branch (if/else, switch, ternary)
- Every thrown error with exact error type and message
- Return value types and shapes
- Side effects (mutations, calls to external services)

**API endpoints / handlers:**
- Success response (status code, body shape, headers)
- Validation errors for each field (missing, wrong type, out of range)
- Authentication/authorization failures
- Rate limiting behavior if applicable
- Idempotency for non-GET methods

**UI components (if applicable):**
- Renders without crashing with required props
- Renders correct content for each state (loading, error, empty, populated)
- User interactions trigger correct callbacks (click, submit, type, select)
- Accessibility: focusable, keyboard navigable, correct ARIA attributes
- Conditional rendering. Each branch shows/hides correct elements

**Database / data layer:**
- CRUD operations return correct data
- Unique constraints reject duplicates
- Cascade deletes work as expected
- Transactions roll back on failure

**Async operations:**
- Successful resolution
- Rejection / error handling
- Timeout behavior
- Cancellation if supported
- Concurrent calls don't interfere

### Mocking Rules

- Prefer real implementations over mocks
- Mock only at system boundaries: network, filesystem, clock, random
- Never mock the code under test
- When you do mock, verify the mock was called with the expected arguments
- Reset mocks between tests so no shared state leaks

## Step 4: Verify

- Run the new tests and confirm they all pass
- Temporarily break the code (change a return value or condition) and confirm at least one test fails
- If no test fails when the code is broken, the tests are useless — rewrite them
- Check coverage: every new function should have at least one test, and every branch should be exercised

## Output

- Complete, runnable test file(s), not snippets
- Tests grouped by the function or component they cover
- A brief summary: how many tests, which scenarios they cover, and any gaps you couldn't cover and why
