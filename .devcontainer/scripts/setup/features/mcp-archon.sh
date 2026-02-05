#!/bin/bash
# Description: Archon MCP server for local AI agent management (via Tailscale)
set -e

ARCHON_HOST="${ARCHON_HOST:-100.113.222.71}"
ARCHON_PORT="${ARCHON_PORT:-8051}"

check_installed() {
    # Check if archon is configured in Claude MCP
    if command -v claude &> /dev/null; then
        if claude mcp list 2>/dev/null | grep -q "archon"; then
            return 0
        fi
    fi
    return 1
}

install() {
    # Check if claude CLI is available
    if ! command -v claude &> /dev/null; then
        echo ""
        echo -e "\033[0;31m✗ Error: Claude Code CLI is not installed.\033[0m"
        echo "Please install Claude Code first using the menu."
        return 1
    fi

    # Check if already installed
    if check_installed; then
        echo ""
        echo -e "\033[0;33m⚠ Archon MCP server is already configured\033[0m"
        echo ""
        echo "Options:"
        echo "  1) Reconfigure with new settings"
        echo "  2) Skip (keep current configuration)"
        echo ""
        read -p "Enter choice (1-2): " choice

        case $choice in
            1)
                echo ""
                echo "Removing existing configuration..."
                claude mcp remove archon 2>/dev/null || true
                ;;
            2)
                echo ""
                echo "Keeping current configuration."
                return 0
                ;;
            *)
                echo "Invalid choice. Skipping."
                return 0
                ;;
        esac
    fi

    ARCHON_URL="http://${ARCHON_HOST}:${ARCHON_PORT}/mcp"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Archon MCP Server Configuration"
    echo ""
    echo "Default URL: ${ARCHON_URL}"
    echo ""
    echo "Options:"
    echo "  1) Use default (Tailscale: ${ARCHON_HOST}:${ARCHON_PORT})"
    echo "  2) Enter custom host/port"
    echo "  3) Skip"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    read -p "Enter choice (1-3): " install_choice

    case $install_choice in
        1)
            # Use defaults
            ;;
        2)
            read -p "Enter Archon host [${ARCHON_HOST}]: " custom_host
            read -p "Enter Archon port [${ARCHON_PORT}]: " custom_port
            ARCHON_HOST="${custom_host:-$ARCHON_HOST}"
            ARCHON_PORT="${custom_port:-$ARCHON_PORT}"
            ARCHON_URL="http://${ARCHON_HOST}:${ARCHON_PORT}/mcp"
            ;;
        3)
            echo "Skipping Archon MCP configuration."
            return 0
            ;;
        *)
            echo "Invalid choice. Skipping."
            return 1
            ;;
    esac

    echo ""
    echo "Adding Archon MCP server..."
    claude mcp add --transport http archon "${ARCHON_URL}"

    echo ""
    echo -e "\033[0;32m✓ Archon MCP server configured!\033[0m"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Server URL: ${ARCHON_URL}"
    echo ""
    echo "Ensure your Archon service is running and accessible via Tailscale."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    return 0
}

install
