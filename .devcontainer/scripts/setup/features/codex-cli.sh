#!/bin/bash
# Description: OpenAI Codex CLI for terminal-based coding assistance
set -e

# Source shared helpers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../helpers.sh"

PACKAGE_NAME="@openai/codex"

check_installed() {
    if command -v codex &> /dev/null; then
        return 0
    fi
    return 1
}

install() {
    # Check if already installed
    if check_installed; then
        local current_version=$(codex --version 2>/dev/null || echo 'unknown')
        echo ""
        echo -e "\033[0;33m⚠ OpenAI Codex CLI is already installed\033[0m"
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
                echo "Upgrading OpenAI Codex CLI..."
                npm_update_global "$PACKAGE_NAME"
                ;;
            2)
                echo ""
                echo "Reinstalling OpenAI Codex CLI..."
                npm_install_global "$PACKAGE_NAME"
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
        echo "Installing OpenAI Codex CLI..."
        npm_install_global "$PACKAGE_NAME"
    fi

    # Create config directory if it doesn't exist
    mkdir -p ~/.codex

    # Verify installation
    if command -v codex &> /dev/null; then
        echo ""
        echo -e "\033[0;32m✓ OpenAI Codex CLI installed successfully!\033[0m"
        echo "  Version: $(codex --version 2>/dev/null || echo 'installed')"
        echo ""

        # Prompt for configuration method
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Configure Codex CLI:"
        echo "  1) Enter OpenAI API key"
        echo "  2) Skip (configure later with 'codex auth login' or set OPENAI_API_KEY)"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Get your API key from: https://platform.openai.com/api-keys"
        echo ""
        read -p "Enter choice (1-2): " config_choice

        if [ "$config_choice" = "1" ]; then
            read -p "Enter your OpenAI API key: " api_key
            if [ -n "$api_key" ]; then
                add_env_to_profiles "OPENAI_API_KEY" "$api_key" "# OpenAI Codex CLI configuration"
                echo -e "\033[0;32m✓ API key added to ~/.bashrc and ~/.zshrc\033[0m"
            fi
        else
            echo "Skipped. Configure later with: codex auth login"
        fi

        echo ""
        echo "Usage: codex --help"
        return 0
    else
        echo ""
        echo -e "\033[0;31m✗ Failed to install OpenAI Codex CLI\033[0m"
        return 1
    fi
}

install
