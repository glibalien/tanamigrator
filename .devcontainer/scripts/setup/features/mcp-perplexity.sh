#!/bin/bash
# Description: Perplexity MCP server for AI-powered web search
set -e

# Source shared helpers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../helpers.sh"

PACKAGE_NAME="@perplexity-ai/mcp-server"
BROWSER_INSTALL_DIR="/usr/local/lib/perplexity-mcp"

check_installed() {
    # Check for API-based installation
    if npm_check_global "$PACKAGE_NAME"; then
        return 0
    fi
    # Check for browser-based installation
    if [ -d "$BROWSER_INSTALL_DIR" ]; then
        return 0
    fi
    return 1
}

install() {
    # Check if already installed
    if check_installed; then
        echo ""
        echo -e "\033[0;33m⚠ Perplexity MCP server is already installed\033[0m"
        if npm_check_global "$PACKAGE_NAME"; then
            echo "  Type: API-based"
        elif [ -d "$BROWSER_INSTALL_DIR" ]; then
            echo "  Type: Browser automation"
        fi
        echo ""
        echo "Options:"
        echo "  1) Upgrade/Reinstall"
        echo "  2) Skip (keep current installation)"
        echo ""
        read -p "Enter choice (1-2): " choice

        case $choice in
            1)
                echo ""
                # Clean up existing installations
                if sudo -n true 2>/dev/null; then
                    sudo npm uninstall -g "$PACKAGE_NAME" 2>/dev/null || true
                    sudo rm -rf "$BROWSER_INSTALL_DIR" 2>/dev/null || true
                else
                    npm uninstall -g "$PACKAGE_NAME" 2>/dev/null || true
                    rm -rf "$BROWSER_INSTALL_DIR" 2>/dev/null || true
                fi
                ;;
            2)
                echo ""
                echo "Keeping current installation."
                return 0
                ;;
            *)
                echo "Invalid choice. Skipping."
                return 0
                ;;
        esac
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Perplexity MCP Server Installation"
    echo ""
    echo "Choose installation method:"
    echo "  1) Official API-based (requires Perplexity API key)"
    echo "  2) Browser automation (no API key required, uses Puppeteer)"
    echo "  3) Skip installation"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    read -p "Enter choice (1-3): " install_choice

    case $install_choice in
        1)
            echo ""
            echo "Installing Official Perplexity MCP Server (API-based)..."

            # Install the package globally for verification
            npm_install_global "$PACKAGE_NAME"

            echo ""
            echo -e "\033[0;32m✓ Perplexity MCP server installed!\033[0m"
            echo ""

            # Prompt for API key configuration
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "Get your API key at: https://www.perplexity.ai/settings/api"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            read -p "Enter your Perplexity API key (or press Enter to skip): " api_key

            if [ -n "$api_key" ]; then
                add_env_to_profiles "PERPLEXITY_API_KEY" "$api_key" "# Perplexity MCP server configuration"
                echo -e "\033[0;32m✓ API key added to ~/.bashrc and ~/.zshrc\033[0m"
            else
                echo "Skipped. Set PERPLEXITY_API_KEY in your MCP config or shell profile later."
            fi

            echo ""
            echo "To use with Claude Code/Desktop, add to your MCP config:"
            echo '  "perplexity": {'
            echo '    "command": "npx",'
            echo '    "args": ["-y", "@perplexity-ai/mcp-server"],'
            echo '    "env": { "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}" }'
            echo '  }'
            ;;

        2)
            echo ""
            echo "Installing Perplexity MCP Server (Browser automation)..."
            echo ""
            echo "This requires Bun runtime. Checking..."

            if ! command -v bun &> /dev/null; then
                echo "Installing Bun runtime..."
                curl -fsSL https://bun.sh/install | bash
                export PATH="$HOME/.bun/bin:$PATH"
            fi

            # Clone and build
            cd /tmp
            git clone https://github.com/wysh3/perplexity-mcp-zerver.git
            cd perplexity-mcp-zerver
            bun install
            bun run build

            # Move to a permanent location
            if sudo -n true 2>/dev/null; then
                sudo mkdir -p "$BROWSER_INSTALL_DIR"
                sudo cp -r ./* "$BROWSER_INSTALL_DIR/"
            else
                mkdir -p ~/.local/lib/perplexity-mcp
                cp -r ./* ~/.local/lib/perplexity-mcp/
                BROWSER_INSTALL_DIR=~/.local/lib/perplexity-mcp
            fi
            cd /tmp
            rm -rf perplexity-mcp-zerver

            echo ""
            echo -e "\033[0;32m✓ Perplexity MCP server (browser automation) installed!\033[0m"
            echo ""
            echo "To use with Claude Code/Desktop, add this configuration:"
            echo ""
            echo "In your MCP config file (e.g., ~/.config/claude-code/mcp.json):"
            echo '{'
            echo '  "mcpServers": {'
            echo '    "perplexity": {'
            echo '      "command": "bun",'
            echo '      "args": ["run", "/usr/local/lib/perplexity-mcp/index.ts"]'
            echo '    }'
            echo '  }'
            echo '}'
            ;;

        3)
            echo ""
            echo "Skipping Perplexity MCP installation."
            echo ""
            echo "You can install it later using one of these methods:"
            echo "  • API-based: npm install -g @perplexity-ai/mcp-server"
            echo "  • Browser automation: See https://github.com/wysh3/perplexity-mcp-zerver"
            return 0
            ;;

        *)
            echo ""
            echo "Invalid choice. Skipping installation."
            return 1
            ;;
    esac

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    return 0
}

install
