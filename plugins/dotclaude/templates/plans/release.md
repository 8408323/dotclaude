# Playbook: cut a release

A generic, project-agnostic flow. Copy it into `.claude/plans/` and adapt it to the project's versioning and publish steps.

1. **Pick the version.** Choose the bump (semver: major, minor, or patch) based on what changed since the last tag. Skim `git log <last-tag>..HEAD`.
2. **Green main.** Confirm the default branch is green in CI and nothing is half-merged.
3. **Changelog.** Summarize the user-facing changes, grouped by type (features, fixes, breaking). Link the PRs.
4. **Bump.** Update the version in the project's manifest(s) and lockfile, in one commit: `chore(release): vX.Y.Z`.
5. **Tag.** Create an annotated tag `vX.Y.Z` on the release commit and push it.
6. **Publish.** Run the project's publish path (package registry, GitHub release, image build), or let the tag-triggered CI do it. Verify the artifact is actually fetchable.
7. **Announce and verify.** Post the release notes, then smoke-test the published artifact in a clean environment.
8. **Open the next cycle.** Bump to the next dev version if the project uses one.
