# Release Management Guide

## Overview

This document describes the release workflow for DATAMIMIC. We use a streamlined approach where:

- Development happens on the `development` branch
- Releases are tagged on `development`
- Main branch serves as a clean release history

## Branch Structure

- `development`: Active development branch, source of truth
- `main`: Clean release history, one commit per release
- `feature/*`: Feature branches for ongoing work

## Development Workflow

1. **Feature Development**

```bash
# Create feature branch from development
git checkout development
git pull origin development
git checkout -b feature/DAT-XXX-description

# Regular commits during development
git commit -m "feat: your changes"
git push origin feature/DAT-XXX-description

# Keep in sync with development
git fetch origin development
git rebase origin/development
```

2. **Feature Completion**

```bash
# Ensure tests pass
pytest

# Merge to development (via PR)
git checkout development
git merge --no-ff feature/DAT-XXX-description
git push origin development
```

## Release Process

1. **Prepare Release on Development**

```bash
# Ensure development is clean
git checkout development
git pull origin development
pytest

# Create the approved release tag
VERSION=X.Y.Z
git tag -a "$VERSION" -m "Release version $VERSION"
git push origin development --tags
```

2. **Prepare the plugin after the package is on PyPI**

Wait for the tag pipeline to publish the package. Download its wheel from
PyPI into a new, empty directory. Use the same `VERSION` as the tag.

```bash
uvx --from pip pip download --index-url https://pypi.org/simple --only-binary=:all: --no-deps \
  --dest release-wheel "datamimic-ce==$VERSION"
.venv/bin/python script/prepare_plugin_release.py prepare release-wheel/*.whl "$VERSION"
.venv/bin/python script/prepare_plugin_release.py verify release-wheel/*.whl "$VERSION"
```

The script checks the wheel metadata and its SHA-256 against PyPI. It updates
both plugin versions and pins the MCP server to that package version. If a
write fails, check all three files and any temporary file before retrying.
Create a PR for the changes. Plugin tests refuse a pinned package version that
differs from either manifest. Check the published plugin and its runtime after
the PR merges.

3. **Update Main Branch**

```bash
# Squash merge release to main
git checkout main
git merge --squash development --strategy-option theirs
git commit -m "release: X.Y.Z"
git push origin main
```

## Version Numbering

We follow semantic versioning (MAJOR.MINOR.PATCH):

- MAJOR: Breaking changes
- MINOR: New features, backward compatible
- PATCH: Bug fixes, backward compatible

## Important Notes

1. **Clean History**
   - Main branch maintains one commit per release
   - All development details preserved in development branch
   - Tags created on development branch first

2. **CI/CD**
   - Primary CI/CD runs on development branch
   - Main branch is for historical record only

3. **Rollback Process**

```bash
# To rollback to a previous release
git checkout main
git reset --hard X.Y.Z
git push --force-with-lease origin main
```

## Emergency Hotfix Process

1. **Create Hotfix**

```bash
# Create hotfix branch from latest release tag
git checkout -b hotfix/DAT-XXX-description X.Y.Z

# Make fixes and commit
git commit -m "fix: critical issue"
```

2. **Release Hotfix**

After the hotfix package is on PyPI, run the plugin preparation step in the
release process with the hotfix version. Merge its PR before publishing the
plugin.

```bash
# Tag on development
git checkout development
git merge --no-ff hotfix/DAT-XXX-description
git tag -a X.Y.Z+1 -m "Hotfix release X.Y.Z+1"
git push origin development --tags

# Update main
git checkout main
git merge --squash development --strategy-option theirs
git commit -m "release: X.Y.Z+1"
git push origin main
```

## Best Practices

1. Always create release tags on development first
2. Keep main branch clean with only release commits
3. Use `--squash` when merging to main
4. Maintain detailed release notes for each version
5. Run full test suite before creating release tags

## Release Checklist

- [ ] All tests passing on development
- [ ] Version numbers updated in relevant files
- [ ] Documentation updated
- [ ] Release notes prepared
- [ ] Release tag created on development
- [ ] Release squashed and merged to main
- [ ] Release notes published on GitHub
