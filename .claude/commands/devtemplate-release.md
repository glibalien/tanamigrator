# /release

Prepare and publish a new version release with proper versioning, changelog, and documentation updates.

## Usage

```
/release [version-type]
```

### Parameters

- `version-type` (optional): Type of version bump - `major`, `minor`, or `patch`. If not provided, will prompt.

## Description

This command performs a complete release workflow:

1. **Pre-flight Checks**: Verify git status and current version
2. **Version Bump**: Update VERSION file based on semver
3. **Update Documentation**:
   - Update version badge in `.devcontainer/README.md`
   - Update version in `docs/TESTING-CHECKLIST.md`
   - Add new section to `.devcontainer/CHANGELOG.md`
4. **Commit Release**: Create release commit with all version updates
5. **Git Tag**: Create annotated tag for the release
6. **Push**: Push commit and tags to remote

## Implementation

When executed, the command will:

1. Read current version from `.devcontainer/VERSION`
2. Calculate new version based on bump type:
   - `major`: 1.2.3 → 2.0.0 (breaking changes)
   - `minor`: 1.2.3 → 1.3.0 (new features)
   - `patch`: 1.2.3 → 1.2.4 (bug fixes)
3. Prompt for changelog entries (what was added/changed/fixed)
4. Update all version references:
   - `.devcontainer/VERSION`
   - `.devcontainer/README.md` (badge and footer)
   - `.devcontainer/CHANGELOG.md` (new version section)
   - `docs/TESTING-CHECKLIST.md`
5. Create commit: `release: v{NEW_VERSION}`
6. Create tag: `v{NEW_VERSION}`
7. Push commit and tag to origin

## Pre-Release Checklist

Before running `/release`, ensure:

- [ ] All features are committed
- [ ] Tests pass (if applicable)
- [ ] Documentation is up to date
- [ ] CHANGELOG entries are prepared

## Examples

```bash
/release patch     # Bug fix release: 1.3.0 → 1.3.1
/release minor     # Feature release: 1.3.0 → 1.4.0
/release major     # Breaking change: 1.3.0 → 2.0.0
/release           # Interactive - will prompt for type
```

## Changelog Entry Format

The command will prompt for entries in these categories:

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Fixed**: Bug fixes
- **Removed**: Removed features
- **Security**: Security-related changes

## Files Modified

| File | Change |
|------|--------|
| `.devcontainer/VERSION` | New version number |
| `.devcontainer/README.md` | Version badge + footer |
| `.devcontainer/CHANGELOG.md` | New version section at top |
| `docs/TESTING-CHECKLIST.md` | Version header |

## Post-Release

After the release is pushed:

1. Verify the tag appears on GitHub
2. Consider creating a GitHub Release from the tag
3. Notify stakeholders of the new version

## Rollback

If something goes wrong:

```bash
# Undo the last commit (before push)
git reset --soft HEAD~1

# Delete local tag
git tag -d v{VERSION}

# If already pushed, delete remote tag
git push origin :refs/tags/v{VERSION}
```
