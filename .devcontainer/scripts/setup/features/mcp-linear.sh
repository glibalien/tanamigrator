#!/bin/bash
# Description: Linear MCP server for project management integration
set -e

# Source shared helpers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../helpers.sh"

PACKAGE_NAME="linear-mcp-server"

check_installed() {
    if npm_check_global "$PACKAGE_NAME"; then
        return 0
    fi
    return 1
}

install() {
    # Check if already installed
    if check_installed; then
        echo ""
        echo -e "\033[0;33m⚠ Linear MCP server is already installed\033[0m"
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
                echo "Upgrading Linear MCP server..."
                npm_update_global "$PACKAGE_NAME"
                ;;
            2)
                echo ""
                echo "Reinstalling Linear MCP server..."
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
        echo "Installing Linear MCP server..."
        npm_install_global "$PACKAGE_NAME"
    fi

    # Verify installation
    if npm_check_global "$PACKAGE_NAME"; then
        echo ""
        echo -e "\033[0;32m✓ Linear MCP server installed successfully!\033[0m"
        echo ""

        # Prompt for API key configuration
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Get your Linear API key at:"
        echo "  https://linear.app/settings/account/security"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        read -p "Enter your Linear API key (or press Enter to skip): " api_key

        if [ -n "$api_key" ]; then
            add_env_to_profiles "LINEAR_API_KEY" "$api_key" "# Linear MCP server configuration"
            echo -e "\033[0;32m✓ API key added to ~/.bashrc and ~/.zshrc\033[0m"
        else
            echo "Skipped. Set LINEAR_API_KEY in your MCP config or shell profile later."
        fi

        echo ""
        echo "To use with Claude Code/Desktop, add to your MCP config:"
        echo '  "linear": {'
        echo '    "command": "npx",'
        echo '    "args": ["-y", "linear-mcp-server"],'
        echo '    "env": { "LINEAR_API_KEY": "${LINEAR_API_KEY}" }'
        echo '  }'
        echo ""
        return 0
    else
        echo ""
        echo -e "\033[0;31m✗ Failed to install Linear MCP server\033[0m"
        return 1
    fi
}

install
