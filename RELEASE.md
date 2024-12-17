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

# Create release tag
git tag -a X.Y.Z -m "Release version X.Y.Z"
git push origin development --tags
```

2. **Update Main Branch**
```bash
# Squash merge release to main
git checkout main
git merge --squash X.Y.Z
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
```bash
# Tag on development
git checkout development
git merge --no-ff hotfix/DAT-XXX-description
git tag -a X.Y.Z+1 -m "Hotfix release X.Y.Z+1"
git push origin development --tags

# Update main
git checkout main
git merge --squash X.Y.Z+1
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