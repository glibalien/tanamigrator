#!/bin/bash
# Description: Vercel Agent-Browser - Headless browser automation CLI for AI agents
set -e

check_installed() {
    if command -v agent-browser &> /dev/null; then
        return 0
    fi
    return 1
}

install() {
    # Check if already installed
    if check_installed; then
        local current_version=$(agent-browser --version 2>/dev/null || echo 'unknown')
        echo ""
        echo -e "\033[0;33m⚠ Agent-Browser is already installed\033[0m"
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
                echo "Upgrading Agent-Browser..."
                if sudo -n true 2>/dev/null; then
                    sudo npm update -g agent-browser
                else
                    npm update -g agent-browser
                fi
                ;;
            2)
                echo ""
                echo "Reinstalling Agent-Browser..."
                if sudo -n true 2>/dev/null; then
                    sudo npm install -g agent-browser
                else
                    npm install -g agent-browser
                fi
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
        echo "Installing Agent-Browser..."
        # Check if passwordless sudo is available
        if sudo -n true 2>/dev/null; then
            sudo npm install -g agent-browser
        else
            echo "Note: sudo not available, installing to user directory..."
            npm config set prefix ~/.local
            npm install -g agent-browser
            export PATH="$HOME/.local/bin:$PATH"
        fi
    fi

    # Install Chromium browser with system dependencies (Linux)
    echo ""
    echo "Installing Chromium browser and dependencies..."
    if [[ "$(uname)" == "Linux" ]]; then
        # Check if passwordless sudo is available for installing system deps
        if sudo -n true 2>/dev/null; then
            agent-browser install --with-deps
        else
            echo "Note: Installing without system dependencies (sudo not available)"
            echo "You may need to install Chromium dependencies manually later."
            agent-browser install
        fi
    else
        agent-browser install
    fi

    # Verify installation
    if command -v agent-browser &> /dev/null; then
        echo ""
        echo -e "\033[0;32m✓ Agent-Browser installed successfully!\033[0m"
        echo "  Version: $(agent-browser --version 2>/dev/null || echo 'installed')"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Quick Start Commands:"
        echo "  agent-browser open <url>    - Navigate to a website"
        echo "  agent-browser snapshot      - Get page accessibility tree"
        echo "  agent-browser click @e2     - Click element by reference"
        echo "  agent-browser type @e3 text - Type into an element"
        echo "  agent-browser screenshot    - Take a screenshot"
        echo ""
        echo "Example workflow:"
        echo "  agent-browser open example.com"
        echo "  agent-browser snapshot"
        echo "  agent-browser click @e5"
        echo ""
        echo "Documentation: https://github.com/vercel-labs/agent-browser"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        return 0
    else
        echo ""
        echo -e "\033[0;31m✗ Failed to install Agent-Browser\033[0m"
        return 1
    fi
}

install
