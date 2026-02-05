# DevTemplate

[![Version](https://img.shields.io/badge/version-1.4.0-blue.svg)](./CHANGELOG.md)

A pre-configured VS Code devcontainer template for AI-assisted software development. Provides a consistent, reproducible development environment with modern tooling and optional AI coding assistants.

## What's Included

### Base Environment (Installed by Default)

| Component | Description |
|-----------|-------------|
| **Node.js 20** | JavaScript/TypeScript runtime |
| **Zsh + Oh My Zsh** | Enhanced shell with Powerlevel10k theme |
| **Git + Delta** | Version control with beautiful diffs |
| **GitHub CLI** | GitHub operations from terminal |
| **FZF** | Fuzzy finder for files and history |
| **Claude Code CLI** | Anthropic's AI coding assistant (auto-installed) |

### VS Code Extensions

- **Claude Code** (`anthropic.claude-code`) - AI pair programming
- **ESLint** - JavaScript/TypeScript linting
- **Prettier** - Code formatting

### Persistent Volumes

Configuration persists across container rebuilds:
- `~/.claude` - Claude Code settings
- `~/.codex` - OpenAI Codex settings
- `~/.gemini` - Google Gemini settings
- `~/.config/gh` - GitHub CLI auth
- `~/.aws` - AWS credentials
- `~/.ssh` - SSH keys
- `~/.docker` - Docker config
- Command history

## Quick Start

### New Projects

1. **Clone this template** to your repository
2. **Open in VS Code** with Dev Containers extension
3. **Rebuild container** when prompted
4. **Run `claude`** to authenticate with Claude Code

The container automatically installs Claude Code CLI on first creation.

### Adopt in Existing Projects

Add devtemplate to an existing project using git subtree:

```bash
# If you have an existing .devcontainer, remove and commit first:
rm -rf .devcontainer
git add -A && git commit -m "Remove existing .devcontainer for devtemplate adoption"

# Add devtemplate as a subtree
git subtree add --prefix=.devcontainer https://github.com/Steve-Klingele/devtemplate.git dist --squash
```

**Update to latest version:**
```bash
git subtree pull --prefix=.devcontainer https://github.com/Steve-Klingele/devtemplate.git dist --squash
```

Or use the `/sync-devtemplate` command in Claude Code.

See [docs/ADOPTION-GUIDE.md](./docs/ADOPTION-GUIDE.md) for detailed instructions including handling customizations.

## Optional Features

Run the interactive setup menu to install additional tools:

```bash
./.devcontainer/scripts/setup/menu.sh
```

### Available Features

#### AI Coding Assistants
| Feature | Command | Description |
|---------|---------|-------------|
| Claude Code | `claude` / `claude-dev` | Anthropic's AI assistant (pre-installed) |
| OpenAI Codex | `codex` / `codex-dev` | OpenAI's coding assistant |
| Google Gemini | `gemini` / `gemini-dev` | Google's AI assistant |
| Z.AI GLM | `glm` | Zhipu's GLM-4.5 assistant |
| Agent-Browser | `agent-browser` | Vercel's headless browser for AI agents |
| SpecStory | `specstory` / `claude-ss` | Auto-save AI conversations |

#### MCP Servers (Model Context Protocol)
| Feature | Description |
|---------|-------------|
| Perplexity | AI-powered web search and research |
| Puppeteer | Browser automation and web scraping |
| Linear | Project management integration |
| Context7 | Dynamic documentation injection |
| OpenMemory | AI memory persistence |
| Archon | Local AI agent management |

#### Orchestration Tools
| Feature | Description |
|---------|-------------|
| BMAD v6 | Agent-as-Code framework |
| SpecKit | Spec-driven development toolkit |
| CodeMachine | Multi-agent autonomous platform |
| Linear Agent Harness | Autonomous coding via Linear issues |
| Vibe Kanban | Multi-agent task orchestration (`vk`) |
| Auto-Claude | Autonomous multi-agent coding (`ac`) |

#### Infrastructure
| Feature | Description |
|---------|-------------|
| 1Password CLI | Secret management |
| Docker-outside-of-Docker | Use host Docker daemon |

## Script Commands

### Setup Menu
```bash
# Interactive feature installation
./.devcontainer/scripts/setup/menu.sh

# Direct feature installation
bash ./.devcontainer/scripts/setup/features/<feature-name>.sh

# Check installed features
cat ./.devcontainer/scripts/setup/manifest.json
```

### Shell Aliases

Install aliases for all installed services via menu option `A`:
```bash
./.devcontainer/scripts/setup/menu.sh
# Then press 'A' to install aliases
```

**Available aliases:**
```bash
# Claude Code
claude          # Standard mode (asks for permissions)
claude-dev      # Development mode (skips permission prompts)

# SpecStory (auto-save conversations)
claude-ss       # Claude via SpecStory
claude-dev-ss   # Claude dev mode via SpecStory

# Other tools
vk              # Vibe Kanban
ac              # Auto-Claude
linear-agent    # Linear Agent Harness
```

## Directory Structure

```
.devcontainer/
├── README.md               # This documentation
├── CHANGELOG.md            # Version history
├── VERSION                 # Current version number
├── Dockerfile              # Container image definition
├── devcontainer.json       # VS Code devcontainer config
└── scripts/
    └── setup/
        ├── menu.sh         # Interactive setup menu
        ├── manifest.json   # Installed features tracker
        └── features/       # Individual feature scripts
            ├── claude-code.sh
            ├── codex-cli.sh
            ├── gemini-cli.sh
            └── ...
```

## Customization

### Add Custom Features

1. Create a script in `.devcontainer/scripts/setup/features/`
2. Follow the template format (see `features/README.md`)
3. Make executable: `chmod +x your-feature.sh`
4. Run via menu or directly

### Modify Base Image

Edit `.devcontainer/Dockerfile` to add system packages or change the base image.

### Change Default Settings

Edit `.devcontainer/devcontainer.json` to modify:
- VS Code extensions
- Editor settings
- Volume mounts
- Environment variables

## Requirements

- VS Code with Dev Containers extension
- Docker Desktop (or compatible Docker runtime)
- For Docker-in-Docker: Docker socket access enabled

## Version

Current version: **1.4.0** (see [CHANGELOG.md](./CHANGELOG.md))

Check installed version:
```bash
cat .devcontainer/VERSION
```

## Testing

See [docs/TESTING-CHECKLIST.md](../docs/TESTING-CHECKLIST.md) for the full testing checklist.

## License

MIT
