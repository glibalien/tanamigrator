# Changelog

All notable changes to DevTemplate will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-01-22

### Added
- **ccusage integration**: Claude Code usage and cost tracking
  - Auto-installed in devcontainer during build
  - Available in feature menu for existing containers
  - Work session summaries now include token counts and costs
- **Usage stats in work sessions**: Frontmatter includes `input_tokens`, `output_tokens`, `cost`
- **Usage section**: Work session template has dedicated usage table

## [1.3.4] - 2026-01-22

### Added
- **Work session duration tracking**: Frontmatter now includes `duration` field (e.g., `2h 15m`)

### Fixed
- **All npm-based installers**: Added sudo fallback using helper functions
  - codex-cli, gemini-cli, mcp-context7, mcp-linear, mcp-openmemory, mcp-perplexity, mcp-puppeteer
- **Installed features summary**: Rewrote using Python to fix sed escaping errors with markdown tables

## [1.3.3] - 2026-01-22

### Added
- **Installed features summary**: Auto-generated `INSTALLED-FEATURES.md` tracks all installed features with metadata
- **Menu option R**: Rebuild/sync features summary by scanning for installed features
- **NPM helper functions**: `npm_install_global`, `npm_update_global`, `npm_check_global` with sudo fallback

### Fixed
- **1Password CLI installer**: Added passwordless sudo check with fallback to `~/.local/bin`
- **Agent-Browser installer**: Added passwordless sudo check for npm install and Chromium deps

## [1.3.2] - 2026-01-22

### Added
- **Agent-OS installer**: Standards-driven development framework for AI coding agents (Builder Methods)
- **devtemplate-feature-checklist command**: Development-only command ensuring consistency when adding/modifying features
- **Peacock VS Code extension**: Auto-installed for workspace color customization

### Fixed
- **Timezone configuration**: Dockerfile now properly sets system timezone (was only setting TZ env var)
- **Auto-Claude installer**: Added `python3-venv` package installation before creating virtual environment
- **Vibe Kanban installer**: Falls back to local install if passwordless sudo unavailable
- **Dual shell support**: Environment variables now written to both `~/.bashrc` and `~/.zshrc`
- **Work session template**: Added stronger language requiring Obsidian frontmatter format

## [1.3.1] - 2026-01-21

### Added
- **Dist branch sync workflow**: GitHub Action that auto-syncs a clean `dist` branch for downstream repos
  - Extracts only `.devcontainer/` contents using `git subtree split`
  - Removes dev-only documentation (specs, strategy docs, task files)
  - Triggers on `.devcontainer/` changes or manual dispatch
  - Downstream repos can pull with: `git subtree pull --prefix=.devcontainer <repo> dist --squash`

## [1.3.0] - 2026-01-19

### Added
- **4 new AI tools** added to installation menu:
  - Agent-Browser: Vercel's headless browser automation CLI for AI agents
  - SpecStory: Auto-save AI conversations with session history
  - Vibe Kanban: Multi-agent task orchestration platform
  - Auto-Claude: Autonomous multi-agent coding framework
- **Shell Aliases Installer** (menu option `A`):
  - Installs convenience aliases for installed services
  - Supports: `claude-dev`, `claude-ss`, `claude-dev-ss`, `codex-ss`, `gemini-ss`, `ac`, `ac-spec`, `ac-list`, `linear-agent`, `vk`
  - Detects installed services and only adds relevant aliases
  - Skips existing aliases, shows summary
- **PROJECT-SETUP-GUIDE.md**: Instructions for LLMs on setting up project-specific files
- **CLAUDE.md**: Project instructions file for Claude Code (auto-read)
- **SpecStory integration**: `specstory sync` imports existing Claude Code sessions
- Testing checklist updated with alias installation tests

### Changed
- Menu now shows 20 features across 4 categories
- Improved menu prompt to show alias option: `(0-N, A for aliases)`

## [1.2.0] - 2025-12-27

### Added
- Z.AI GLM Coding Plan integration
  - Configures Claude Code to use GLM-4.7 models as backend
  - Automated setup via `npx @z_ai/coding-helper`
  - Manual configuration option with API key
  - Reset to Anthropic (default) option
  - Backs up settings before changes
- Installation detection for all feature scripts
  - Scripts now check if service is already installed before reinstalling
  - Offers upgrade/reinstall/skip options when service exists
- Real-time installation status in setup menu
  - Shows `[✓ INSTALLED]` or `[○ NOT INSTALLED]` for each feature
  - Checks actual system state, not just manifest
- Claude Code install script now prompts for authentication after install
- Aliases now available immediately without terminal refresh
- Added Claude Code, Archon MCP, and Linear Agent Harness to menu

### Changed
- Z.AI integration now uses GLM Coding Plan instead of standalone CLI
  - Model mapping: Opus/Sonnet → GLM-4.7, Haiku → GLM-4.5-Air
  - Configuration stored in `~/.claude/settings.json`
  - Requires Claude Code as prerequisite
- Moved README.md, CHANGELOG.md, and VERSION to `.devcontainer/` folder
  - Prevents conflicts when using template in projects with their own root files
- Added start commands to testing checklist for all services
- Added manual install instructions for Claude Code in testing checklist
- "Install All" now skips already-installed features

## [1.1.0] - 2025-12-26

### Added
- Interactive API key prompts for all services requiring authentication
- API keys automatically saved to shell profile (~/.bashrc or ~/.zshrc)
- Testing checklist document (`docs/TESTING-CHECKLIST.md`)
- Version tracking with VERSION file and CHANGELOG
- Chat history documentation system (`docs/chat-history/`)

### Changed
- Z.AI GLM CLI now installs to `/opt/glm-4.5-cli` (permanent location)
- Improved installation success messages with color coding

### Fixed
- Z.AI GLM CLI installation failure caused by npm link symlinks breaking when temp directory was deleted

### Services with API Key Prompts
- OpenAI Codex CLI (`OPENAI_API_KEY`)
- Google Gemini CLI (`GOOGLE_API_KEY`)
- Z.AI GLM CLI (`GLM_API_KEY`)
- Linear MCP Server (`LINEAR_API_KEY`)
- OpenMemory MCP Server (`OPENMEMORY_API_KEY`)
- Perplexity MCP Server (`PERPLEXITY_API_KEY`)

## [1.0.0] - 2025-12-26

### Added
- Initial release
- Base devcontainer with Node.js 20, Zsh, Oh My Zsh, Git, Delta, GitHub CLI, FZF
- Claude Code CLI auto-installation
- Interactive feature installation menu
- Feature scripts for AI CLI tools (Codex, Gemini, Z.AI GLM)
- Feature scripts for MCP servers (Context7, Linear, OpenMemory, Perplexity, Puppeteer)
- Feature scripts for orchestration tools (BMAD v6, CodeMachine, SpecKit)
- Feature scripts for infrastructure (1Password CLI, Docker-outside-of-Docker)
- Persistent volumes for configuration
- Installation manifest tracking
