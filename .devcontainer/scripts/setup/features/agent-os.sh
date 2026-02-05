#!/bin/bash
# Description: Agent OS - Standards-driven development framework for AI coding agents
set -e

INSTALL_DIR="${HOME}/agent-os"

check_installed() {
    if [ -d "$INSTALL_DIR" ] && [ -f "$INSTALL_DIR/config.yml" ]; then
        return 0
    fi
    return 1
}

install() {
    echo ""
    echo "Agent OS - Standards-driven development for AI agents"
    echo "======================================================"
    echo ""
    echo "Agent OS helps you:"
    echo "  - Discover and document coding standards from your codebase"
    echo "  - Deploy standards contextually during development"
    echo "  - Shape better specs for spec-driven development"
    echo ""
    echo "Works with: Claude Code, Cursor, Antigravity"
    echo ""

    # Check if already installed
    if check_installed; then
        echo -e "\033[0;33m⚠ Agent OS is already installed at ${INSTALL_DIR}\033[0m"
        echo ""
        echo "Options:"
        echo "  1) Update to latest version"
        echo "  2) Reinstall (removes existing installation)"
        echo "  3) Skip (keep current installation)"
        echo ""
        read -p "Enter choice (1-3): " choice

        case $choice in
            1)
                echo ""
                echo "Updating Agent OS..."
                cd "$INSTALL_DIR"
                # Re-clone to get latest (since .git was removed during install)
                cd ~
                rm -rf "$INSTALL_DIR"
                git clone https://github.com/buildermethods/agent-os.git && rm -rf "${INSTALL_DIR}/.git"
                ;;
            2)
                echo ""
                echo "Reinstalling Agent OS..."
                rm -rf "$INSTALL_DIR"
                git clone https://github.com/buildermethods/agent-os.git ~/agent-os && rm -rf "${INSTALL_DIR}/.git"
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
        echo "Installing Agent OS to ${INSTALL_DIR}..."
        echo ""

        # Clone the repository
        git clone https://github.com/buildermethods/agent-os.git ~/agent-os

        # Remove .git directory as recommended
        rm -rf "${INSTALL_DIR}/.git"
    fi

    # Verify installation
    if check_installed; then
        echo ""
        echo -e "\033[0;32m✓ Agent OS installed successfully!\033[0m"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Installation location: ${INSTALL_DIR}"
        echo ""
        echo "Directory structure:"
        echo "  ~/agent-os/profiles/   - Reusable standards sets"
        echo "  ~/agent-os/scripts/    - Installation scripts"
        echo "  ~/agent-os/commands/   - Slash commands"
        echo "  ~/agent-os/config.yml  - Configuration"
        echo ""
        echo "Next step - Install in your project:"
        echo "  cd /path/to/your/project"
        echo "  ~/agent-os/scripts/project-install.sh"
        echo ""
        echo "Options:"
        echo "  --profile <name>   Install with a specific profile"
        echo "  --commands-only    Update commands only"
        echo ""
        echo "Documentation: https://buildermethods.com/agent-os"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        return 0
    else
        echo ""
        echo -e "\033[0;31m✗ Failed to install Agent OS\033[0m"
        return 1
    fi
}

install
