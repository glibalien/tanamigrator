---
created: 2025-09-25T13:06
updated: 2025-11-12T08:39
---
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a Claude Code development environment configured with VS Code devcontainer support. The repository primarily serves as a development sandbox with Claude Code integration.

## Development Environment

### Container Setup
- Built on Node.js 20 base image
- Includes Claude Code CLI (@anthropic-ai/claude-code)
- Pre-configured with essential development tools: git, gh (GitHub CLI), fzf, zsh, vim, nano
- Network tools available: iptables, ipset, iproute2, dnsutils

### VS Code Configuration
- Extensions automatically installed:
  - anthropic.claude-code
  - dbaeumer.vscode-eslint
  - esbenp.prettier-vscode
  - eamodio.gitlens
- Auto-formatting enabled on save with Prettier
- ESLint fixes applied on save
- Default shell: zsh

### Working with Claude Code

To run Claude Code in the container:
```bash
claude --dangerously-skip-permissions
```

Alias available for convenience:
```bash
claude-dev
```

### Persistent Storage

The following directories are persisted across container rebuilds:
- `/commandhistory` - Shell command history
- `/home/node/.claude` - Claude configuration
- `/home/node/.config/gh` - GitHub CLI configuration
- `/home/node/.aws` - AWS CLI configuration
- `/home/node/.config/gcloud` - Google Cloud configuration
- `/home/node/.docker` - Docker configuration
- `/home/node/.ssh` - SSH keys and configuration

## Key Environment Variables

- `NODE_OPTIONS`: --max-old-space-size=4096
- `CLAUDE_CONFIG_DIR`: /home/node/.claude
- `DEVCONTAINER`: true
- `EDITOR`: nano
- `VISUAL`: nano
- `SHELL`: /bin/zsh

## Git Configuration

- Main branch: `master`
- Repository initialized with basic devcontainer setup