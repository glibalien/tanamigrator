# DevContainer Setup Scripts

Modular, interactive installation system for optional devcontainer features and tools.

## Quick Start

After your devcontainer is built and running:

```bash
./.devcontainer/scripts/setup/menu.sh
```

This launches an interactive menu where you can select which features to install.

## Why This System?

This template is designed to be flexible. Not every project needs every tool, so instead of bloating the base devcontainer with everything, you can:

1. **Start with a minimal devcontainer** - fast build times
2. **Add tools as needed** - install only what you need for your project
3. **Update anytime** - re-run the menu to add more tools later
4. **Track installations** - manifest system tracks what's installed

## Features

See [features/README.md](./features/README.md) for detailed information about available features.

Currently available:
- **CLI Tools**: 1Password, Agent-Browser, Auto-Claude, Claude Code, Codex, Gemini, SpecStory, Vibe Kanban, Z.AI GLM
- **MCP Servers**: Archon, Context7, Linear, OpenMemory, Perplexity, Puppeteer
- **Orchestration**: BMAD v6, CodeMachine, Linear Agent Harness, SpecKit
- **Infrastructure**: Docker-outside-of-Docker

## How It Works

### Directory Structure
```
.devcontainer/scripts/setup/
├── menu.sh              # Interactive menu (run this!)
├── manifest.json        # Tracks installed features
└── features/            # Individual feature scripts
    ├── README.md        # Feature documentation
    ├── 1password-cli.sh
    ├── docker-outside.sh
    ├── codex-cli.sh
    └── gemini-cli.sh
```

### Installation Flow

1. Run `./scripts/setup/menu.sh`
2. Menu displays available features with installation status
3. Select a feature to install (or "Install All")
4. Script runs the feature installation
5. Manifest is updated to track installation
6. Return to menu to install more features

### Manifest System

The `manifest.json` file tracks:
```json
{
  "installed": {
    "1password-cli": "2024-12-14T10:30:00Z",
    "docker-outside": "2024-12-14T10:31:00Z"
  },
  "last_updated": "2024-12-14T10:31:00Z"
}
```

This allows the menu to show `[INSTALLED]` status and prevents accidental re-installation.

## Adding Your Own Features

Want to add a custom feature? It's easy!

1. Create a new script in `features/` directory
2. Follow the template in `features/README.md`
3. Make it executable: `chmod +x features/your-feature.sh`
4. Run the menu - it will automatically appear!

## Examples

### Install a single feature
```bash
# From the menu
./.devcontainer/scripts/setup/menu.sh
# Select option 1 for 1Password CLI

# Or directly
bash ./.devcontainer/scripts/setup/features/1password-cli.sh
```

### Install all features
```bash
# From the menu
./.devcontainer/scripts/setup/menu.sh
# Select "Install All Features" option
```

### Check what's installed
```bash
cat ./.devcontainer/scripts/setup/manifest.json
```

## Integration with DevContainer

### Optional: Auto-run on container creation

If you want the menu to run automatically on first container creation:

Add to `devcontainer.json`:
```json
{
  "postCreateCommand": "bash ./.devcontainer/scripts/setup/menu.sh"
}
```

### Optional: Add as a VS Code task

Create `.vscode/tasks.json`:
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Setup Features",
      "type": "shell",
      "command": "./.devcontainer/scripts/setup/menu.sh",
      "problemMatcher": []
    }
  ]
}
```

Then run via: `Terminal > Run Task > Setup Features`

## Best Practices

1. **Review before installing** - Check what each feature does
2. **Install incrementally** - Start with what you need now
3. **Document project needs** - Note which features your project requires
4. **Update as needed** - Re-run menu anytime to add more tools

## Troubleshooting

**Menu doesn't show features:**
- Check that feature scripts are in `features/` directory
- Ensure scripts are executable (`chmod +x`)
- Verify scripts have proper description header

**Installation fails:**
- Check error messages for specific issues
- Some features require devcontainer configuration (see features/README.md)
- Try running the feature script directly for verbose output

**Manifest issues:**
- Delete `manifest.json` to reset tracking
- File will be recreated on next menu run
