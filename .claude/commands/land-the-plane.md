# /land-the-plane

Save work session summary, commit all changes, and push to remote repository.

## Usage

```
/land-the-plane [description]
```

### Parameters

- `description` (optional): Short description for both the work session summary and git commit message

## Description

This command performs a complete end-of-session workflow:

1. **Save Work Session**: Creates an Obsidian-compatible work session summary in `docs/work-sessions/`
2. **Git Add All**: Stages all modified and new files
3. **Git Commit**: Creates a commit with descriptive message
4. **Git Push**: Pushes changes to remote repository

## Implementation

When executed, the command will:

1. Execute `/save-work-session [description]` to create work session documentation
2. Run `git add .` to stage all changes
3. Create a commit with format: `docs: work session - [description]`
4. Push to the current remote branch
5. Report success/failure status

## Examples

```bash
/land-the-plane tana-integration-fixes
/land-the-plane debug-api-endpoints
/land-the-plane implement-user-dashboard
```

## Error Handling

- If work session save fails, the command continues with git operations
- If git operations fail, detailed error messages are provided
- Shows git status and remote sync confirmation

## Priority

HIGH - This command ensures no work is lost and maintains proper documentation of development progress.
