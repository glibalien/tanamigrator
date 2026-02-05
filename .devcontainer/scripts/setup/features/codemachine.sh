#!/bin/bash
# Description: CodeMachine - Multi-agent orchestration for autonomous development
set -e

check_installed() {
    if command -v codemachine &> /dev/null || command -v cm &> /dev/null; then
        return 0
    fi
    return 1
}

install() {
    # Check if already installed
    if check_installed; then
        echo ""
        echo -e "\033[0;33m⚠ CodeMachine is already installed\033[0m"
        echo ""
        echo "Options:"
        echo "  1) Reinstall"
        echo "  2) Skip (keep current installation)"
        echo ""
        read -p "Enter choice (1-2): " choice

        case $choice in
            1)
                echo ""
                echo "Proceeding with reinstallation..."
                sudo npm unlink codemachine 2>/dev/null || true
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
    echo "⚠️  CodeMachine is in early development"
    echo ""
    echo "This tool is experimental and not yet production-ready."
    echo "Features may change, break, or be incomplete."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    read -p "Continue with installation? (y/n): " continue_install

    if [[ ! $continue_install =~ ^[Yy]$ ]]; then
        echo ""
        echo "Skipping CodeMachine installation."
        echo ""
        echo "You can install it later from:"
        echo "  https://github.com/moazbuilds/CodeMachine-CLI"
        return 0
    fi

    # Clone the repository
    echo ""
    echo "Cloning CodeMachine repository..."
    cd /tmp
    rm -rf CodeMachine-CLI 2>/dev/null || true
    git clone https://github.com/moazbuilds/CodeMachine-CLI.git
    cd CodeMachine-CLI

    # Install dependencies
    echo ""
    echo "Installing dependencies..."
    npm install

    # Build if necessary
    if [ -f "package.json" ] && grep -q "\"build\":" package.json; then
        echo ""
        echo "Building CodeMachine..."
        npm run build
    fi

    # Install globally
    echo ""
    echo "Installing CodeMachine globally..."
    sudo npm link

    # Cleanup
    cd /tmp
    rm -rf CodeMachine-CLI

    # Verify installation
    if command -v codemachine &> /dev/null || command -v cm &> /dev/null; then
        echo ""
        echo -e "\033[0;32m✓ CodeMachine installed successfully!\033[0m"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "CodeMachine Key Features:"
        echo "  • Multi-agent orchestration with specialized models"
        echo "  • Heterogeneous AI system (Gemini, Claude, etc.)"
        echo "  • Long-running autonomous workflows (hours/days)"
        echo "  • Spec-to-code transformation"
        echo ""
        echo "Usage:"
        echo "  codemachine --help"
        echo ""
        echo "Example workflow:"
        echo "  1. Create a specification file"
        echo "  2. Run: codemachine generate spec.md"
        echo "  3. CodeMachine orchestrates multiple agents to:"
        echo "     • Plan (using Gemini)"
        echo "     • Implement (using Claude)"
        echo "     • Review (using another model)"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        return 0
    else
        echo ""
        echo -e "\033[0;31m✗ Failed to install CodeMachine\033[0m"
        echo ""
        echo "You can try installing manually:"
        echo "  git clone https://github.com/moazbuilds/CodeMachine-CLI.git"
        echo "  cd CodeMachine-CLI"
        echo "  npm install && npm link"
        return 1
    fi
}

install
