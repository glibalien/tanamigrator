# save-work-session

Save a comprehensive work session summary with Obsidian-compatible frontmatter.

## Usage

```
/save-work-session [description]
```

### Parameters

- `description` (optional): Short description of the main topic or accomplishment

## Description

This command creates an Obsidian-compatible work session summary and saves it to `docs/work-sessions/` with proper naming conventions. Use this command before compacting chat, ending sessions, or when switching to major new topics.

## Output Format

**CRITICAL: You MUST include the Obsidian frontmatter exactly as shown below. Do not skip, omit, or modify the frontmatter format. The frontmatter is required for Obsidian compatibility.**

The generated file includes Obsidian frontmatter and follows this template:

```markdown
---
created: YYYY-MM-DDTHH:MM
updated: YYYY-MM-DDTHH:MM
duration: Xh Ym
ai_cost: $X.XX
tags: []
NoteType: Work Session
Parent:
Summary: [description or auto-generated summary]
---

## Session Goals

[What was the intended outcome of this session]

## Notes

[Key observations, decisions, and context from the session]

## Progress Made

[Concrete accomplishments - files created/modified, features implemented, bugs fixed]

## Next Steps

[Outstanding items, follow-up tasks, and blockers]

## Usage

| Metric | Value |
|--------|-------|
| Duration | Xh Ym |
| Input Tokens | X |
| Output Tokens | X |
| Total Tokens | X |
| Total Cost | $X.XX |
```

## Implementation

When executed:

1. Create `docs/work-sessions/` directory if it doesn't exist
2. Generate filename: `YYYY-MM-DD-HHMM-[appname]-[description].md`
   - `HHMM` is the current time (24-hour format, no separator)
   - `[appname]` is derived from the repository/project name (e.g., `devtemplate`)
3. Generate current timestamp for `created` and `updated` fields
4. Calculate `duration` from conversation start time to now (format: `Xh Ym`, e.g., `2h 15m`)
5. Get usage stats by running `ccusage` (if available) for today's session:
   - Input tokens, output tokens, total tokens
   - Total cost
6. Populate frontmatter with session metadata (duration and ai_cost only; token counts go in Usage table)
7. Fill in the four main sections based on conversation context:
   - **Session Goals**: Infer from initial user requests
   - **Notes**: Key decisions, approaches taken, technical details
   - **Progress Made**: Files changed, features completed, issues resolved
   - **Next Steps**: Remaining work, blockers, future considerations
8. Add Usage section with token counts and cost table

## Examples

```bash
/save-work-session setup-authentication
# Creates: 2026-01-19-0822-myproject-setup-authentication.md

/save-work-session debug-api-endpoints
# Creates: 2026-01-19-1430-myproject-debug-api-endpoints.md

/save-work-session implement-user-dashboard
# Creates: 2026-01-19-1645-myproject-implement-user-dashboard.md
```

## Priority

HIGH - This command should not be skipped when triggered by:
- User requesting chat compaction
- Context limit approaching
- Session ending
- Major topic transitions
