# Playbook: cut a release

A generic, project-agnostic flow. Copy into `.claude/plans/` and adapt to the project's versioning and publish steps.

1. **Pick the version.** Decide the bump (semver: major/minor/patch) from what changed since the last tag. Skim `git log <last-tag>..HEAD`.
2. **Green main.** Confirm the default branch is green in CI and there's nothing half-merged.
3. **Changelog.** Summarize user-facing changes grouped by type (features / fixes / breaking). Link PRs.
4. **Bump.** Update the version in the project's manifest(s) and lockfile. One commit: `chore(release): vX.Y.Z`.
5. **Tag.** Annotated tag `vX.Y.Z` on the release commit; push the tag.
6. **Publish.** Run the project's publish path (package registry, GitHub release, image build) — or let the tag-triggered CI do it. Verify the artifact is actually fetchable.
7. **Announce + verify.** Post the release notes; smoke-test the published artifact in a clean environment.
8. **Open the next cycle.** Bump to the next dev version if the project uses one.
