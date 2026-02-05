# sync-devtemplate

Sync the `.devcontainer/` directory with the latest changes from the devtemplate repository's `dist` branch using git subtree.

## Usage

```
/sync-devtemplate
```

## What This Command Does

1. Checks for uncommitted changes in the working tree
2. Stashes any uncommitted changes temporarily
3. Pulls the latest from devtemplate `dist` branch via git subtree
4. Restores any stashed changes
5. Reports what was updated

## Implementation

When executed, perform the following steps:

### 1. Pre-flight Checks

Verify:
- We're in a git repository
- `.devcontainer/` exists
- Git is available

### 2. Check Current Version

Read the current version from `.devcontainer/VERSION` and report it.

### 3. Handle Uncommitted Changes

Check `git status --porcelain`. If there are changes:
- Inform the user there are uncommitted changes
- Stash them with: `git stash push -u -m "Auto-stash before devtemplate sync"`
- Remember that we stashed

### 4. Pull Subtree Updates

Run the subtree pull command:

```bash
git subtree pull --prefix=.devcontainer https://github.com/Steve-Klingele/devtemplate.git dist --squash
```

Capture the output to determine if there were updates or if already up-to-date.

### 5. Restore Stashed Changes

If we stashed changes in step 3:
- Run `git stash pop`
- Report if there were any conflicts

### 6. Report Results

Read the new version from `.devcontainer/VERSION` and report:
- Previous version → New version (if changed)
- "Already up to date" (if no changes)
- Any files that were updated
- Reminder to rebuild container if Dockerfile or devcontainer.json changed

## Example Output

```
Syncing devtemplate...

Current version: 1.3.1
Stashing uncommitted changes...

Pulling from devtemplate dist branch...
Updated .devcontainer from 1.3.1 → 1.3.2

Changed files:
- Dockerfile (modified)
- scripts/setup/features/new-feature.sh (added)

Restored stashed changes.

Note: Dockerfile was updated. Consider rebuilding your devcontainer.
```

## Error Handling

- If subtree pull fails due to conflicts, report them and do NOT auto-resolve
- If stash pop has conflicts, report them
- Always try to restore the stash even if pull fails

## Notes

- This command uses `--squash` to keep commit history clean
- The devtemplate repo's `dist` branch contains only distributable content (no dev docs)
- Source repo: https://github.com/Steve-Klingele/devtemplate

## First-Time Setup

If this is a new project that hasn't adopted devtemplate yet, see the [Adoption Guide](.devcontainer/docs/ADOPTION-GUIDE.md) for initial setup instructions.
