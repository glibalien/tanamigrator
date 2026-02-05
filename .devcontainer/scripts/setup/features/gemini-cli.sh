#!/bin/bash
# Description: Google Gemini AI CLI tool for code generation and assistance
set -e

# Source shared helpers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../helpers.sh"

PACKAGE_NAME="@google/generative-ai-cli"

check_installed() {
    if command -v gemini &> /dev/null; then
        return 0
    fi
    return 1
}

install() {
    # Check if already installed
    if check_installed; then
        local current_version=$(gemini --version 2>/dev/null || echo 'unknown')
        echo ""
        echo -e "\033[0;33m⚠ Gemini CLI is already installed\033[0m"
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
                echo "Upgrading Gemini CLI..."
                npm_update_global "$PACKAGE_NAME"
                ;;
            2)
                echo ""
                echo "Reinstalling Gemini CLI..."
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
        echo "Installing Gemini CLI..."
        npm_install_global "$PACKAGE_NAME"
    fi

    # Create config directory if it doesn't exist
    mkdir -p ~/.gemini

    # Verify installation
    if command -v gemini &> /dev/null; then
        echo ""
        echo -e "\033[0;32m✓ Gemini CLI installed successfully!\033[0m"
        echo "  Version: $(gemini --version 2>/dev/null || echo 'installed')"
        echo ""

        # Prompt for API key configuration
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Get your API key from: https://makersuite.google.com/app/apikey"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        read -p "Enter your Google API key (or press Enter to skip): " api_key

        if [ -n "$api_key" ]; then
            add_env_to_profiles "GOOGLE_API_KEY" "$api_key" "# Google Gemini CLI configuration"
            echo -e "\033[0;32m✓ API key added to ~/.bashrc and ~/.zshrc\033[0m"
        else
            echo "Skipped. Configure later with: export GOOGLE_API_KEY=your_key"
        fi

        echo ""
        echo "Usage: gemini --help"
        return 0
    else
        echo ""
        echo -e "\033[0;31m✗ Failed to install Gemini CLI\033[0m"
        return 1
    fi
}

install
