#!/bin/bash
# Description: Context7 MCP server for dynamic documentation injection
set -e

# Source shared helpers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../helpers.sh"

PACKAGE_NAME="@upstash/context7-mcp"

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
        echo -e "\033[0;33m⚠ Context7 MCP server is already installed\033[0m"
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
                echo "Upgrading Context7 MCP server..."
                npm_update_global "$PACKAGE_NAME"
                ;;
            2)
                echo ""
                echo "Reinstalling Context7 MCP server..."
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
        echo "Installing Context7 MCP server..."
        npm_install_global "$PACKAGE_NAME"
    fi

    # Verify installation
    if npm_check_global "$PACKAGE_NAME"; then
        echo ""
        echo -e "\033[0;32m✓ Context7 MCP server installed successfully!\033[0m"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "To use with Claude Code/Desktop, add this configuration:"
        echo ""
        echo "In your MCP config file (e.g., ~/.config/claude-code/mcp.json):"
        echo '{'
        echo '  "mcpServers": {'
        echo '    "context7": {'
        echo '      "command": "npx",'
        echo '      "args": ["-y", "@upstash/context7-mcp@latest"]'
        echo '    }'
        echo '  }'
        echo '}'
        echo ""
        echo "Or for Claude Code CLI, use:"
        echo "  claude mcp add context7 -- npx -y @upstash/context7-mcp"
        echo ""
        echo "Context7 provides:"
        echo "  • Up-to-date, version-specific documentation"
        echo "  • Dynamic documentation injection into prompts"
        echo "  • Support for popular frameworks and libraries"
        echo "  • No API key required (free MCP server)"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        return 0
    else
        echo ""
        echo -e "\033[0;31m✗ Failed to install Context7 MCP server\033[0m"
        return 1
    fi
}

install
