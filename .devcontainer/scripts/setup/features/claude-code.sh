#!/bin/bash
# Description: Anthropic Claude Code CLI for AI-powered coding assistance
set -e

check_installed() {
    if command -v claude &> /dev/null; then
        return 0
    fi
    return 1
}

install() {
    # Check if already installed
    if check_installed; then
        local current_version=$(claude --version 2>/dev/null || echo 'unknown')
        echo ""
        echo -e "\033[0;33m⚠ Claude Code CLI is already installed\033[0m"
        echo "  Current version: $current_version"
        echo ""
        echo "Options:"
        echo "  1) Upgrade to latest version"
        echo "  2) Reinstall current version"
        echo "  3) Skip (keep current installation)"
        echo ""
        read -p "Enter choice (1-3): " choice

        case $choice in
            1)
                echo ""
                echo "Upgrading Claude Code CLI..."
                sudo npm update -g @anthropic-ai/claude-code
                ;;
            2)
                echo ""
                echo "Reinstalling Claude Code CLI..."
                sudo npm install -g @anthropic-ai/claude-code
                ;;
            3)
                echo ""
                echo "Keeping current installation."
                return 0
                ;;
            *)
                echo "Invalid choice. Skipping."
                return 0
                ;;
        esac
    else
        echo "Installing Claude Code CLI..."
        sudo npm install -g @anthropic-ai/claude-code
    fi

    # Create config directory if it doesn't exist
    mkdir -p ~/.claude

    # Verify installation
    if command -v claude &> /dev/null; then
        echo ""
        echo -e "\033[0;32m✓ Claude Code CLI installed successfully!\033[0m"
        echo "  Version: $(claude --version 2>/dev/null || echo 'installed')"

        # Add claude-dev alias to shell profiles
        if ! grep -q 'alias claude-dev=' ~/.zshrc 2>/dev/null; then
            echo "" >> ~/.zshrc
            echo "# Claude Code development alias" >> ~/.zshrc
            echo 'alias claude-dev="claude --dangerously-skip-permissions"' >> ~/.zshrc
        fi
        if ! grep -q 'alias claude-dev=' ~/.bashrc 2>/dev/null; then
            echo "" >> ~/.bashrc
            echo "# Claude Code development alias" >> ~/.bashrc
            echo 'alias claude-dev="claude --dangerously-skip-permissions"' >> ~/.bashrc
        fi

        # Make alias available in current session
        alias claude-dev="claude --dangerously-skip-permissions"
        export -f claude-dev 2>/dev/null || true

        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Aliases configured:"
        echo "  claude      - Standard mode (asks for permissions)"
        echo "  claude-dev  - Development mode (skips permission prompts)"
        echo ""
        echo "Configuration persists in: ~/.claude"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""

        # Prompt for authentication
        echo "Would you like to authenticate now?"
        read -p "Run 'claude' to sign in? (y/n): " auth_choice

        if [[ "$auth_choice" =~ ^[Yy]$ ]]; then
            echo ""
            echo "Starting Claude Code authentication..."
            echo "(Follow the prompts to complete sign-in)"
            echo ""
            claude
        else
            echo ""
            echo "You can authenticate later by running: claude"
        fi

        return 0
    else
        echo ""
        echo -e "\033[0;31m✗ Failed to install Claude Code CLI\033[0m"
        return 1
    fi
}

install
