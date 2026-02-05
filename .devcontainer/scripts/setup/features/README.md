# DevContainer Feature Scripts

This directory contains modular feature installation scripts for the devcontainer environment. Each script can be run independently or through the interactive menu system.

## Available Features

### 1. 1Password CLI (`1password-cli.sh`)
- **Purpose**: Secret management and authentication
- **What it does**: Installs the 1Password CLI tool for secure credential management
- **Use case**: Managing API keys, secrets, and credentials securely
- **Post-install**: Run `eval $(op signin)` or set `OP_SERVICE_ACCOUNT_TOKEN`

### 2. Docker-outside-of-Docker (`docker-outside.sh`)
- **Purpose**: Use host Docker daemon from within the devcontainer
- **What it does**: Installs Docker CLI and configures it to use the host's Docker socket
- **Use case**: Building Docker images, running containers from within devcontainer
- **Requirements**: Devcontainer must mount `/var/run/docker.sock`

### 3. Claude Code CLI (`claude-code.sh`)
- **Purpose**: Anthropic Claude AI-powered coding assistance
- **What it does**: Installs the official Claude Code CLI tool via npm
- **Use case**: AI-assisted coding, code generation, and agentic development
- **Post-install**: Run `claude` and follow authentication prompts
- **Alias**: `claude-dev` (runs with `--dangerously-skip-permissions`)

### 4. OpenAI Codex CLI (`codex-cli.sh`)
- **Purpose**: OpenAI Codex terminal-based coding assistance
- **What it does**: Installs the official OpenAI Codex CLI tool via npm
- **Use case**: AI-assisted coding with ChatGPT Plus/Pro/Enterprise or API key
- **Post-install**: Configure with `codex auth login` or set `OPENAI_API_KEY`

### 5. Gemini CLI (`gemini-cli.sh`)
- **Purpose**: Google Gemini AI assistance
- **What it does**: Installs the Gemini CLI tool via npm
- **Use case**: AI-assisted coding using Google's Gemini model
- **Post-install**: Get API key from https://makersuite.google.com/app/apikey and set `GOOGLE_API_KEY`

### 6. Z.AI GLM CLI (`z-ai.sh`)
- **Purpose**: Z.AI/Zhipu GLM CLI for AI-assisted coding
- **What it does**: Installs the GLM-4.5-CLI tool for terminal-based AI assistance
- **Use case**: AI-assisted coding using Zhipu's GLM-4.5 and GLM-4.5-Air models
- **Post-install**: Set environment variables (GLM_API_KEY, GLM_BASE_URL, GLM_MODEL, GLM_THINKING_MODE)

### 7. Agent-Browser (`agent-browser.sh`)
- **Purpose**: Headless browser automation CLI for AI agents
- **What it does**: Installs Vercel's agent-browser with Chromium for browser control
- **Repo**: https://github.com/vercel-labs/agent-browser
- **Use case**: AI-driven web browsing, scraping, and interaction
- **Commands**: `agent-browser open <url>`, `snapshot`, `click @ref`, `type @ref text`
- **Features**: Fast Rust CLI, accessibility tree snapshots, element references

### 8. SpecStory CLI (`specstory.sh`)
- **Purpose**: Auto-save AI conversations for Claude Code, Codex, Gemini
- **What it does**: Wraps CLI agents to capture every session to searchable markdown
- **Repo**: https://github.com/specstoryai/getspecstory
- **Use case**: Session history, context retrieval, team knowledge sharing
- **Commands**: `specstory run claude`, `specstory run codex`, `specstory check`
- **Custom flags**: `specstory run -c "claude --flag"` (quoted command)
- **Storage**: Local-first in `.specstory/history/`, optional cloud sync
- **Aliases**: `claude-ss`, `claude-dev-ss` (dev mode), `codex-ss`, `gemini-ss`

### 9. Vibe Kanban (`vibe-kanban.sh`)
- **Purpose**: Task orchestration for AI coding agents
- **What it does**: Manage and run multiple AI agents (Claude, Gemini, Codex, Amp) in parallel
- **Repo**: https://github.com/BloopAI/vibe-kanban
- **Use case**: Multi-agent workflows, task monitoring, centralized MCP config
- **Commands**: `vibe-kanban` or `npx vibe-kanban`
- **Features**: Real-time progress, parallel/sequential runs, remote SSH access
- **Alias**: `vk` for quick access

### 10. Auto-Claude (`auto-claude.sh`)
- **Purpose**: Autonomous multi-agent coding framework
- **What it does**: Plans, builds, and validates software using Claude AI agents
- **Repo**: https://github.com/AndyMik90/Auto-Claude
- **Use case**: Autonomous development, parallel builds (up to 12 agents), git worktree isolation
- **Commands**: `ac --spec 001`, `ac-spec --interactive`, `ac-list`
- **Features**: GitHub/GitLab/Linear integration, QA validation, release notes
- **Requirements**: Claude Code CLI, Python 3.9+, `CLAUDE_CODE_OAUTH_TOKEN`
- **Aliases**: `ac`, `ac-spec`, `ac-list`

## MCP Servers (Model Context Protocol)

### 11. Perplexity MCP (`mcp-perplexity.sh`)
- **Purpose**: AI-powered web search and research
- **Options**: API-based (requires key) or browser automation (no key required)
- **Use case**: Real-time web search, reasoning, and research capabilities
- **Configuration**: Add to Claude Code/Desktop MCP config

### 12. Puppeteer MCP (`mcp-puppeteer.sh`)
- **Purpose**: Browser automation and web scraping
- **What it does**: Provides browser control for screenshots, form filling, navigation
- **Use case**: Web scraping, testing, automated interactions
- **Requirements**: Node.js 18+

### 13. Linear MCP (`mcp-linear.sh`)
- **Purpose**: Linear project management integration
- **What it does**: Create/manage issues, view projects, update states
- **Use case**: Project management directly from AI assistant
- **Post-install**: Get API key from https://linear.app/YOUR-TEAM/settings/api

### 14. Context7 MCP (`mcp-context7.sh`)
- **Purpose**: Dynamic documentation injection
- **What it does**: Provides up-to-date, version-specific documentation
- **Use case**: Access current framework/library docs during development
- **Benefits**: Free, no API key required

### 15. OpenMemory MCP (`mcp-openmemory.sh`)
- **Purpose**: AI memory and context persistence
- **What it does**: Maintains memory across conversations with knowledge graphs
- **Use case**: Long-term context retention
- **Note**: Cloud service can be unreliable, consider self-hosting

### 16. Archon MCP (`mcp-archon.sh`)
- **Purpose**: Local Archon AI agent management service
- **What it does**: Configures Claude Code to connect to your Archon instance via Tailscale
- **Use case**: AI agent orchestration and management
- **Default**: Connects to `100.113.222.71:8051` (configurable)
- **Requirements**: Archon service running and accessible via Tailscale

## Orchestration Tools

### 17. BMAD v6 (`bmad-v6.sh`)
- **Purpose**: Agent-as-Code framework for AI-driven development
- **Options**: Node.js (alpha) or Python installation
- **Features**: Deterministic planning, 90% token reduction, visual workflows
- **Use case**: Large-scale AI-assisted development with observability
- **Post-install**: Run `bmad init` to initialize workspace

### 18. GitHub SpecKit (`speckit.sh`)
- **Purpose**: Spec-driven development toolkit
- **What it does**: Structured workflow from spec → plan → code → test
- **Compatible with**: GitHub Copilot, Claude Code, Gemini CLI
- **Use case**: Specification-first development approach
- **Post-install**: Initialize projects with `/specify`, `/plan`, `/tasks`

### 19. CodeMachine (`codemachine.sh`)
- **Purpose**: Multi-agent autonomous development platform
- **What it does**: Orchestrates specialized models for complex workflows
- **Features**: Heterogeneous AI (Gemini+Claude+etc), long-running tasks
- **Status**: ⚠️ Early development, experimental
- **Use case**: Complex multi-day autonomous development tasks

### 20. Linear Agent Harness (`linear-agent-harness.sh`)
- **Purpose**: Autonomous coding agents with Linear project management integration
- **What it does**: Orchestrates Claude Code agents to work through Linear issues
- **Repo**: https://github.com/coleam00/Linear-Coding-Agent-Harness
- **Features**: Two-phase workflow (initializer + coding agents), MCP integration
- **Use case**: Autonomous development driven by Linear issues
- **Alias**: `linear-agent` for quick access
- **Requirements**: Claude Code CLI, Python 3, Linear API key, Claude OAuth token

## Usage

### Interactive Menu
Run the interactive menu to select and install features:
```bash
./scripts/setup/menu.sh
```

### Individual Installation
Install a specific feature directly:
```bash
bash ./scripts/setup/features/1password-cli.sh
```

### Install All Features
From the menu, select the "Install All Features" option to install everything at once.

## Adding New Features

To add a new feature, create a new script in this directory following this template:

```bash
#!/bin/bash
# Description: Brief description of what this feature does
set -e

install() {
    echo "Installing <feature-name>..."

    # Installation steps here

    # Verify installation
    if command -v <command> &> /dev/null; then
        echo "<Feature> installed successfully!"
        echo "Version: $(<command> --version)"
        echo ""
        echo "To configure <feature>:"
        echo "  1. Step 1"
        echo "  2. Step 2"
        return 0
    else
        echo "Failed to install <feature>"
        return 1
    fi
}

install
```

**Important**:
- First line must be shebang: `#!/bin/bash`
- Second line must be description: `# Description: <your description>`
- Script must be executable: `chmod +x <script-name>.sh`
- Must have an `install()` function that returns 0 on success, 1 on failure
- Should include verification and usage instructions

## Tracked Installation

The system maintains a manifest file (`manifest.json`) that tracks:
- Which features are installed
- When they were installed
- Last update timestamp

This allows the menu to show installation status and prevents duplicate installations.

## Feature Requirements

Some features may require specific devcontainer configuration:

### Docker-outside-of-Docker
Add to `devcontainer.json`:
```json
{
  "mounts": [
    "source=/var/run/docker.sock,target=/var/run/docker.sock,type=bind"
  ]
}
```

### Persistent Configurations
For features that save configurations (Codex, Gemini, etc.), ensure you have volume mounts for their config directories:
```json
{
  "mounts": [
    "source=codex-config-${devcontainerId},target=/home/node/.codex,type=volume",
    "source=gemini-config-${devcontainerId},target=/home/node/.gemini,type=volume"
  ]
}
```

## Best Practices

1. **Test features individually** before running "Install All"
2. **Review feature scripts** to understand what they install
3. **Check requirements** - some features need devcontainer configuration
4. **Re-run safely** - scripts should be idempotent where possible
5. **Keep configs in volumes** - use volume mounts for persistent configuration

## Troubleshooting

### Feature installation fails
- Check the error message for specific issues
- Ensure all prerequisites are met (e.g., Docker socket for docker-outside)
- Try running the feature script directly for more verbose output

### Permission issues
- Some installations require `sudo` which is included in scripts
- Docker group changes may require terminal reload

### Configuration not persisting
- Ensure volume mounts are configured in `devcontainer.json`
- Check that config directories are correctly mapped
