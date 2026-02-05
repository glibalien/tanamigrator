#!/bin/bash
# Description: Vibe Kanban - Task orchestration for AI coding agents (Claude, Gemini, Codex)
set -e

check_installed() {
    if command -v vibe-kanban &> /dev/null; then
        return 0
    fi
    # Check if available via npx (not globally installed but cached)
    if npm list -g vibe-kanban &> /dev/null; then
        return 0
    fi
    return 1
}

install() {
    # Check if already installed
    if check_installed; then
        local current_version=$(vibe-kanban --version 2>/dev/null || npm list -g vibe-kanban 2>/dev/null | grep vibe-kanban || echo 'unknown')
        echo ""
        echo -e "\033[0;33m⚠ Vibe Kanban is already installed\033[0m"
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
                echo "Upgrading Vibe Kanban..."
                if sudo -n true 2>/dev/null; then
                    sudo npm update -g vibe-kanban
                else
                    npm update -g vibe-kanban --prefix "$HOME/.local" 2>/dev/null || npm install -g vibe-kanban --prefix "$HOME/.local"
                fi
                ;;
            2)
                echo ""
                echo "Reinstalling Vibe Kanban..."
                if sudo -n true 2>/dev/null; then
                    sudo npm install -g vibe-kanban
                else
                    npm install -g vibe-kanban --prefix "$HOME/.local"
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
        echo ""
        echo "Vibe Kanban - AI Coding Agent Orchestration"
        echo "============================================"
        echo ""
        echo "Installation options:"
        echo "  1) Global install (recommended for frequent use)"
        echo "  2) Use via npx (no install, runs latest each time)"
        echo ""
        read -p "Enter choice (1-2) [1]: " method
        method=${method:-1}

        case $method in
            1)
                echo ""
                echo "Installing Vibe Kanban globally..."
                # Try passwordless sudo first, fall back to user-local install
                if sudo -n true 2>/dev/null; then
                    sudo npm install -g vibe-kanban
                else
                    echo "Sudo requires password. Installing to user directory instead..."
                    mkdir -p "$HOME/.local/bin"
                    npm install -g vibe-kanban --prefix "$HOME/.local"
                    # Ensure ~/.local/bin is in PATH
                    for profile in ~/.zshrc ~/.bashrc; do
                        if [ -f "$profile" ] && ! grep -q 'HOME/.local/bin' "$profile" 2>/dev/null; then
                            echo "" >> "$profile"
                            echo '# User-local npm binaries' >> "$profile"
                            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$profile"
                        fi
                    done
                    export PATH="$HOME/.local/bin:$PATH"
                fi
                ;;
            2)
                echo ""
                echo "Vibe Kanban will be available via: npx vibe-kanban"
                echo "No global installation performed."
                # Pre-cache it for faster first run
                echo "Pre-caching package..."
                npx --yes vibe-kanban --version 2>/dev/null || true
                ;;
            *)
                echo "Installing globally..."
                if sudo -n true 2>/dev/null; then
                    sudo npm install -g vibe-kanban
                else
                    echo "Sudo requires password. Installing to user directory instead..."
                    mkdir -p "$HOME/.local/bin"
                    npm install -g vibe-kanban --prefix "$HOME/.local"
                    export PATH="$HOME/.local/bin:$PATH"
                fi
                ;;
        esac
    fi

    # Verify installation
    if command -v vibe-kanban &> /dev/null || npx vibe-kanban --version &> /dev/null 2>&1; then
        echo ""
        echo -e "\033[0;32m✓ Vibe Kanban installed successfully!\033[0m"

        local version=$(vibe-kanban --version 2>/dev/null || npx vibe-kanban --version 2>/dev/null || echo 'installed')
        echo "  Version: $version"

        # Add alias to shell profiles
        ALIAS_VK='alias vk="vibe-kanban"'

        for profile in ~/.zshrc ~/.bashrc; do
            if [ -f "$profile" ]; then
                if ! grep -q 'alias vk=' "$profile" 2>/dev/null; then
                    echo "" >> "$profile"
                    echo "# Vibe Kanban alias" >> "$profile"
                    echo "$ALIAS_VK" >> "$profile"
                fi
            fi
        done

        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Usage:"
        echo "  vibe-kanban              - Launch the orchestration UI"
        echo "  npx vibe-kanban          - Run without global install"
        echo ""
        echo "Alias added (restart shell or source profile):"
        echo "  vk  - Shortcut for 'vibe-kanban'"
        echo ""
        echo "Features:"
        echo "  • Switch between Claude Code, Gemini, Codex, Amp"
        echo "  • Run multiple agents in parallel or sequence"
        echo "  • Monitor task progress in real-time"
        echo "  • Centralize MCP configurations"
        echo "  • Remote access via SSH"
        echo ""
        echo "Prerequisites:"
        echo "  Authenticate with your coding agent first (e.g., 'claude')"
        echo ""
        echo "Documentation: https://github.com/BloopAI/vibe-kanban"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        return 0
    else
        echo ""
        echo -e "\033[0;31m✗ Failed to install Vibe Kanban\033[0m"
        return 1
    fi
}

install
