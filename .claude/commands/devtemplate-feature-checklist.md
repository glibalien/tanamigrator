# devtemplate-feature-checklist

Checklist for adding, removing, or modifying features in the DevTemplate installation menu.

## Usage

```
/devtemplate-feature-checklist [action] [feature-name]
```

### Parameters

- `action`: `add`, `remove`, or `modify`
- `feature-name`: The feature identifier (e.g., `agent-os`, `mcp-linear`)

## Description

This command ensures all necessary files and configurations are updated when changing the feature installation menu. Use this checklist every time you add, remove, or modify a feature.

**Note:** This command is for DevTemplate development only and is NOT included in the distributed template.

## Checklist

When adding/modifying/removing a feature, complete ALL applicable items:

### 1. Feature Installer Script

**Location:** `.devcontainer/scripts/setup/features/{feature-name}.sh`

- [ ] Create/update the installer script
- [ ] Include `# Description:` comment on line 2 (shown in menu)
- [ ] Include `set -e` for error handling
- [ ] Add `check_installed()` function
- [ ] Add `install()` function with:
  - Already-installed detection with upgrade/reinstall/skip options
  - Clear installation progress messages
  - Verification step after installation
  - Usage instructions displayed on success
- [ ] Test syntax: `bash -n .devcontainer/scripts/setup/features/{feature-name}.sh`
- [ ] Make executable: `chmod +x .devcontainer/scripts/setup/features/{feature-name}.sh`

### 2. Menu Configuration

**Location:** `.devcontainer/scripts/setup/menu.sh`

- [ ] Add/update `check_system_installed()` case for the feature
- [ ] Add/remove feature from appropriate category in `categories` array (appears twice in file - update BOTH):
  - `Core Tools`
  - `AI CLI Tools`
  - `MCP Servers`
  - `Orchestration`
- [ ] Test menu syntax: `bash -n .devcontainer/scripts/setup/menu.sh`

### 3. Testing Checklist

**Location:** `docs/TESTING-CHECKLIST.md`

- [ ] Add/update test cases in appropriate section
- [ ] Include installation verification commands
- [ ] Include start commands
- [ ] Include any required environment variables or prerequisites

### 4. Linear Testing Task

- [ ] Create testing task in Linear (DevTemplate project)
- [ ] Include checklist items from TESTING-CHECKLIST.md
- [ ] Link to related issues if applicable

### 5. Documentation (if applicable)

**Location:** `.devcontainer/scripts/setup/features/README.md`

- [ ] Add/update feature entry with description
- [ ] Update feature numbering if needed

### 6. Aliases (if applicable)

**Location:** `.devcontainer/scripts/setup/menu.sh` in `install_aliases()` function

- [ ] Add alias installation logic if the feature has convenience aliases
- [ ] Update alias documentation in TESTING-CHECKLIST.md

## Implementation

When this command is invoked:

1. Display the checklist above
2. Ask which action is being performed (add/remove/modify)
3. Ask for the feature name
4. Walk through each checklist item, confirming completion
5. Offer to create the Linear task automatically if LINEAR_API_KEY is available
6. Summarize what was done

## Quick Reference

### Files to touch when ADDING a feature:
```
.devcontainer/scripts/setup/features/{feature-name}.sh  (create)
.devcontainer/scripts/setup/menu.sh                     (add to check + categories)
docs/TESTING-CHECKLIST.md                               (add test cases)
Linear                                                  (create task)
```

### Files to touch when REMOVING a feature:
```
.devcontainer/scripts/setup/features/{feature-name}.sh  (delete)
.devcontainer/scripts/setup/menu.sh                     (remove from check + categories)
docs/TESTING-CHECKLIST.md                               (remove test cases)
```

### Files to touch when MODIFYING a feature:
```
.devcontainer/scripts/setup/features/{feature-name}.sh  (update)
.devcontainer/scripts/setup/menu.sh                     (update if check logic changed)
docs/TESTING-CHECKLIST.md                               (update if tests changed)
```

## Example: Adding a New Feature

```bash
# 1. Create installer
vim .devcontainer/scripts/setup/features/my-feature.sh

# 2. Test syntax
bash -n .devcontainer/scripts/setup/features/my-feature.sh

# 3. Make executable
chmod +x .devcontainer/scripts/setup/features/my-feature.sh

# 4. Add to menu.sh (check_system_installed + categories array x2)
vim .devcontainer/scripts/setup/menu.sh

# 5. Test menu syntax
bash -n .devcontainer/scripts/setup/menu.sh

# 6. Add to testing checklist
vim docs/TESTING-CHECKLIST.md

# 7. Create Linear task (or use this command to auto-create)
```
