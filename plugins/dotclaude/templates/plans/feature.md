# Playbook: feature → merged PR

A generic, project-agnostic flow. Copy it into `.claude/plans/` and adapt it to the specific feature.

1. **Frame it.** In one sentence, state what changes for the user and how you'll know it works. Note the smallest shippable slice.
2. **Find the seams.** Locate the files and modules involved and the existing patterns to match. Don't design new abstractions before you've seen the current ones.
3. **Branch.** Create `feat/<topic>` off the default branch.
4. **TDD the core.** Write the failing test for the next behavior, make it pass, then refactor. Repeat. (`/dotclaude:tdd`)
5. **Wire it up.** Integrate behind the existing interfaces. Keep the diff scoped — no drive-by refactors.
6. **Verify.** Run the specific test file, then the full suite. Run the formatter and linter. Manually exercise the happy path and one edge case.
7. **Ship.** Self-review the diff, write a tight PR description (what and why), and open the PR. (`/dotclaude:ship`)
8. **Close the loop.** Address review threads, resolve them, and re-request review. Merge when green.
