#!/bin/bash
# Description: Auto-Claude - Autonomous multi-agent coding framework for planning, building, and validating software
set -e

INSTALL_DIR="${HOME}/.local/share/auto-claude"

check_installed() {
    if [ -d "$INSTALL_DIR" ] && [ -f "$INSTALL_DIR/apps/backend/run.py" ]; then
        return 0
    fi
    return 1
}

install() {
    # Check prerequisites
    if ! command -v python3 &> /dev/null; then
        echo -e "\033[0;31m✗ Python 3 is required but not installed\033[0m"
        return 1
    fi

    if ! command -v claude &> /dev/null; then
        echo ""
        echo -e "\033[0;33m⚠ Claude Code CLI is recommended but not installed\033[0m"
        echo "  Install with: sudo npm install -g @anthropic-ai/claude-code"
        echo ""
        read -p "Continue anyway? (y/n): " continue_choice
        if [[ ! "$continue_choice" =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi

    # Check if already installed
    if check_installed; then
        echo ""
        echo -e "\033[0;33m⚠ Auto-Claude is already installed\033[0m"
        echo "  Location: $INSTALL_DIR"
        echo ""
        echo "Options:"
        echo "  1) Update to latest version (git pull)"
        echo "  2) Reinstall (fresh clone)"
        echo "  3) Skip (keep current installation)"
        echo ""
        read -p "Enter choice (1-3): " choice

        case $choice in
            1)
                echo ""
                echo "Updating Auto-Claude..."
                cd "$INSTALL_DIR"
                git pull origin main
                cd apps/backend
                if command -v uv &> /dev/null; then
                    uv pip install -r requirements.txt
                else
                    source .venv/bin/activate
                    pip install -r requirements.txt
                fi
                ;;
            2)
                echo ""
                echo "Reinstalling Auto-Claude..."
                rm -rf "$INSTALL_DIR"
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
    fi

    # Clone repository if not exists
    if [ ! -d "$INSTALL_DIR" ]; then
        echo ""
        echo "Auto-Claude - Autonomous Multi-Agent Coding Framework"
        echo "======================================================"
        echo ""
        echo "Cloning Auto-Claude repository..."
        git clone https://github.com/AndyMik90/Auto-Claude.git "$INSTALL_DIR"
    fi

    # Set up Python environment
    echo ""
    echo "Setting up Python environment..."
    cd "$INSTALL_DIR/apps/backend"

    if command -v uv &> /dev/null; then
        echo "Using uv for virtual environment..."
        uv venv
        uv pip install -r requirements.txt
    else
        # Ensure python3-venv is installed (required for venv module)
        if ! python3 -c "import ensurepip" &> /dev/null; then
            echo "Installing python3-venv package..."
            PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
            sudo apt-get update -qq && sudo apt-get install -y -qq python3-venv python${PYTHON_VERSION}-venv 2>/dev/null || sudo apt-get install -y -qq python3-venv
        fi

        echo "Using standard Python venv..."
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt
    fi

    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            echo "Created .env from .env.example"
        else
            cat > .env << 'EOF'
# Auto-Claude Configuration
# Get your token by running: claude setup-token
CLAUDE_CODE_OAUTH_TOKEN=

# Optional settings
# AUTO_BUILD_MODEL=claude-opus-4-5-20251101
# DEFAULT_BRANCH=main
# DEBUG=false
# GRAPHITI_ENABLED=true
EOF
            echo "Created default .env file"
        fi
    fi

    # Add aliases and functions to shell profiles
    AUTOCLAUDE_FUNC='
# Auto-Claude functions
export AUTO_CLAUDE_DIR="'"$INSTALL_DIR"'"

auto-claude() {
    cd "$AUTO_CLAUDE_DIR/apps/backend"
    if [ -f .venv/bin/activate ]; then
        source .venv/bin/activate
    fi
    python run.py "$@"
}

auto-claude-spec() {
    cd "$AUTO_CLAUDE_DIR/apps/backend"
    if [ -f .venv/bin/activate ]; then
        source .venv/bin/activate
    fi
    python runners/spec_runner.py "$@"
}

alias ac="auto-claude"
alias ac-spec="auto-claude-spec"
alias ac-list="auto-claude --list"
'

    for profile in ~/.zshrc ~/.bashrc; do
        if [ -f "$profile" ]; then
            if ! grep -q 'AUTO_CLAUDE_DIR=' "$profile" 2>/dev/null; then
                echo "" >> "$profile"
                echo "$AUTOCLAUDE_FUNC" >> "$profile"
            fi
        fi
    done

    echo ""
    echo -e "\033[0;32m✓ Auto-Claude installed successfully!\033[0m"
    echo "  Location: $INSTALL_DIR"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Setup Required:"
    echo "  1. Get your OAuth token:  claude setup-token"
    echo "  2. Add token to config:   nano $INSTALL_DIR/apps/backend/.env"
    echo "     Set: CLAUDE_CODE_OAUTH_TOKEN=your-token-here"
    echo ""
    echo "Commands (restart shell or source profile first):"
    echo "  ac-spec --interactive     - Create a spec interactively"
    echo "  ac-spec --task \"desc\"     - Create spec from description"
    echo "  ac-list                   - List available specs"
    echo "  ac --spec 001             - Run build for spec 001"
    echo "  ac --spec 001 --review    - Review changes"
    echo "  ac --spec 001 --merge     - Merge changes to main"
    echo ""
    echo "Aliases:"
    echo "  ac        - Run auto-claude (python run.py)"
    echo "  ac-spec   - Run spec runner"
    echo "  ac-list   - List specs"
    echo ""
    echo "Controls during execution:"
    echo "  Ctrl+C (once)  - Pause and add instructions"
    echo "  Ctrl+C (twice) - Exit immediately"
    echo ""
    echo "Documentation: https://github.com/AndyMik90/Auto-Claude"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Prompt for OAuth token setup
    echo ""
    read -p "Would you like to set up OAuth token now? (y/n): " setup_token

    if [[ "$setup_token" =~ ^[Yy]$ ]]; then
        if command -v claude &> /dev/null; then
            echo ""
            echo "Running 'claude setup-token'..."
            echo "Copy the token and add it to: $INSTALL_DIR/apps/backend/.env"
            echo ""
            claude setup-token
        else
            echo ""
            echo "Claude Code CLI not found. Install it first:"
            echo "  sudo npm install -g @anthropic-ai/claude-code"
            echo "Then run: claude setup-token"
        fi
    fi

    return 0
}

install
