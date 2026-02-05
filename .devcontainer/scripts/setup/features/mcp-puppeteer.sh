#!/bin/bash
# Description: Puppeteer MCP server for browser automation and web scraping
set -e

# Source shared helpers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../helpers.sh"

PACKAGE_NAME="@modelcontextprotocol/server-puppeteer"

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
        echo -e "\033[0;33m⚠ Puppeteer MCP server is already installed\033[0m"
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
                echo "Upgrading Puppeteer MCP server..."
                npm_update_global "$PACKAGE_NAME"
                ;;
            2)
                echo ""
                echo "Reinstalling Puppeteer MCP server..."
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
        echo "Installing Puppeteer MCP server..."
        npm_install_global "$PACKAGE_NAME"
    fi

    # Verify installation
    if npm_check_global "$PACKAGE_NAME"; then
        echo ""
        echo -e "\033[0;32m✓ Puppeteer MCP server installed successfully!\033[0m"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "To use with Claude Code/Desktop, add this configuration:"
        echo ""
        echo "In your MCP config file (e.g., ~/.config/claude-code/mcp.json):"
        echo '{'
        echo '  "mcpServers": {'
        echo '    "puppeteer": {'
        echo '      "command": "npx",'
        echo '      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]'
        echo '    }'
        echo '  }'
        echo '}'
        echo ""
        echo "This enables browser automation capabilities for:"
        echo "  • Web scraping"
        echo "  • Screenshot capture"
        echo "  • Form filling and interaction"
        echo "  • Page navigation"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        return 0
    else
        echo ""
        echo -e "\033[0;31m✗ Failed to install Puppeteer MCP server\033[0m"
        return 1
    fi
}

install
