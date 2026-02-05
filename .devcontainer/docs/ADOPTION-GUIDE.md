# DevTemplate Adoption Guide

This guide explains how to add the devtemplate to your project using git subtree, enabling you to receive updates via the `/sync-devtemplate` command.

## Prerequisites

- Git installed
- A git repository for your project (can be new or existing)
- No uncommitted changes in your working tree

---

## Option A: New Project (No Existing .devcontainer)

If your project doesn't have a `.devcontainer/` directory yet, adoption is straightforward.

### Steps

1. **Navigate to your project root:**
   ```bash
   cd /path/to/your-project
   ```

2. **Ensure you have a clean working tree:**
   ```bash
   git status
   # Should show no uncommitted changes
   ```

3. **Add the devtemplate as a subtree:**
   ```bash
   git subtree add --prefix=.devcontainer https://github.com/Steve-Klingele/devtemplate.git dist --squash
   ```

4. **Verify the installation:**
   ```bash
   ls .devcontainer/
   # Should show: Dockerfile, devcontainer.json, scripts/, etc.
   ```

5. **Continue to [Post-Adoption Setup](#post-adoption-setup)**

---

## Option B: Existing Project (Has .devcontainer)

If your project already has a `.devcontainer/` directory, you'll need to remove it first and migrate any customizations.

### Step 1: Document Your Customizations

Before removing your existing `.devcontainer/`, note any customizations you want to preserve:

```bash
# Review your current setup
cat .devcontainer/devcontainer.json
cat .devcontainer/Dockerfile
ls -la .devcontainer/
```

**Common customizations to preserve:**
- Custom VS Code extensions in `devcontainer.json`
- Additional packages installed in `Dockerfile`
- Environment variables
- Port forwarding settings
- Mount configurations

**Tip:** Copy your existing `.devcontainer/` to a temporary location for reference:
```bash
cp -r .devcontainer /tmp/devcontainer-backup
```

### Step 2: Remove Existing .devcontainer

```bash
# Remove the directory
rm -rf .devcontainer

# Commit the removal
git add -A
git commit -m "Remove existing .devcontainer in preparation for devtemplate adoption"
```

> **Important:** You must commit the removal before adding the subtree. Git subtree requires a clean merge base.

### Step 3: Add the DevTemplate Subtree

```bash
git subtree add --prefix=.devcontainer https://github.com/Steve-Klingele/devtemplate.git dist --squash
```

This creates a new commit that adds the devtemplate contents to `.devcontainer/`.

### Step 4: Re-apply Customizations

If you had customizations from Step 1, re-apply them now:

#### Custom VS Code Extensions

Edit `.devcontainer/devcontainer.json` and add your extensions to the `customizations.vscode.extensions` array:

```json
{
  "customizations": {
    "vscode": {
      "extensions": [
        // ... existing extensions ...
        "your.custom-extension"
      ]
    }
  }
}
```

#### Custom Dockerfile Packages

Edit `.devcontainer/Dockerfile` and add packages to the appropriate `apt-get install` section, or add a new `RUN` command at the end:

```dockerfile
# Add your custom packages
RUN apt-get update && apt-get install -y \
    your-package \
    another-package \
    && rm -rf /var/lib/apt/lists/*
```

#### Environment Variables

Add to `.devcontainer/devcontainer.json`:

```json
{
  "containerEnv": {
    "YOUR_VAR": "value"
  }
}
```

### Step 5: Commit Customizations

```bash
git add .devcontainer/
git commit -m "Add project-specific devcontainer customizations"
```

### Step 6: Continue to [Post-Adoption Setup](#post-adoption-setup)

---

## Post-Adoption Setup

After adding the devtemplate subtree, set up project-specific directories.

### 1. Create Project Directories

```bash
# Create work sessions directory for Obsidian-compatible notes
mkdir -p docs/work-sessions

# Create SpecStory directory for AI conversation tracking
mkdir -p .specstory/history
cat > .specstory/.project.json << EOF
{
  "project_name": "$(basename $(pwd))"
}
EOF
```

### 2. Update .gitignore (if needed)

Ensure your `.gitignore` includes:

```gitignore
# Environment and secrets
.env
.env.local

# Local IDE settings
.claude/settings.local.json
```

### 3. Install Development Tools (Optional)

Run the installation menu to install additional tools:

```bash
./.devcontainer/scripts/setup/menu.sh
```

### 4. Rebuild Your Devcontainer

If using VS Code or a devcontainer-compatible IDE:
- **VS Code:** Press `Cmd/Ctrl+Shift+P` → "Dev Containers: Rebuild Container"
- **DevPod:** `devpod up . --recreate`

---

## Updating the DevTemplate

Once adopted, use the `/sync-devtemplate` command in Claude Code to pull updates:

```
/sync-devtemplate
```

Or manually:

```bash
git subtree pull --prefix=.devcontainer https://github.com/Steve-Klingele/devtemplate.git dist --squash
```

---

## Troubleshooting

### "Working tree has modifications" error

Commit or stash your changes before running subtree commands:

```bash
git stash push -u -m "Temporary stash for subtree operation"
# Run subtree command
git stash pop
```

### "prefix '.devcontainer' already exists" error

This means `.devcontainer/` exists and isn't tracked as a subtree. Follow [Option B](#option-b-existing-project-has-devcontainer) to remove and re-add it.

### Merge conflicts during subtree pull

If you've modified files that were also updated upstream:

1. Resolve conflicts manually in the affected files
2. `git add` the resolved files
3. `git commit` to complete the merge

### Subtree history issues

If you encounter persistent subtree issues, you can reset and re-add:

```bash
# Remove subtree tracking (keeps files)
git rm -r .devcontainer
git commit -m "Remove devtemplate subtree for re-initialization"

# Re-add fresh
git subtree add --prefix=.devcontainer https://github.com/Steve-Klingele/devtemplate.git dist --squash
```

---

## What's Included

The devtemplate provides:

| Component | Description |
|-----------|-------------|
| `Dockerfile` | Development container with Node.js, Python, and common tools |
| `devcontainer.json` | VS Code devcontainer configuration |
| `scripts/setup/menu.sh` | Interactive tool installation menu |
| `scripts/setup/features/` | Individual tool installers (Claude Code, MCP servers, etc.) |
| `PROJECT-SETUP-GUIDE.md` | Instructions for AI assistants setting up new projects |

---

## Related Documentation

- [PROJECT-SETUP-GUIDE.md](../PROJECT-SETUP-GUIDE.md) - Detailed project-specific setup instructions
- [CHANGELOG.md](../CHANGELOG.md) - Version history and changes
- [DevTemplate Repository](https://github.com/Steve-Klingele/devtemplate) - Source repository
