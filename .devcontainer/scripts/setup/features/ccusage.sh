#!/bin/bash
# Description: ccusage - Claude Code usage and cost tracking CLI
set -e

# Source shared helpers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../helpers.sh"

PACKAGE_NAME="ccusage"

check_installed() {
    if command -v ccusage &> /dev/null; then
        return 0
    fi
    return 1
}

install() {
    # Check if already installed
    if check_installed; then
        local current_version=$(ccusage --version 2>/dev/null || echo 'unknown')
        echo ""
        echo -e "\033[0;33m⚠ ccusage is already installed\033[0m"
        echo "  Current version: $current_version"
        echo ""
        echo "Options:"
        echo "  1) Upgrade to latest version"
        echo "  2) Reinstall"
        echo "  3) Skip (keep current installation)"
        echo ""
        read -p "Enter choice (1-3): " choice

        case $choice in
            1)
                echo ""
                echo "Upgrading ccusage..."
                npm_update_global "$PACKAGE_NAME"
                ;;
            2)
                echo ""
                echo "Reinstalling ccusage..."
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
        echo "Installing ccusage..."
        npm_install_global "$PACKAGE_NAME"
    fi

    # Verify installation
    if command -v ccusage &> /dev/null; then
        echo ""
        echo -e "\033[0;32m✓ ccusage installed successfully!\033[0m"
        echo "  Version: $(ccusage --version 2>/dev/null || echo 'installed')"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Usage:"
        echo "  ccusage              # Show today's usage"
        echo "  ccusage -d 7         # Show last 7 days"
        echo "  ccusage -m           # Show current month"
        echo "  ccusage --breakdown  # Show per-project breakdown"
        echo ""
        echo "Tracks Claude Code API usage including:"
        echo "  • Input/output tokens"
        echo "  • Estimated costs"
        echo "  • Per-session and per-project breakdowns"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        return 0
    else
        echo ""
        echo -e "\033[0;31m✗ Failed to install ccusage\033[0m"
        return 1
    fi
}

install
