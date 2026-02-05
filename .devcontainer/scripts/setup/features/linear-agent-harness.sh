#!/bin/bash
# Description: Linear Coding Agent Harness - autonomous agents with Linear integration
set -e

INSTALL_DIR="${HOME}/.local/share/linear-agent-harness"

check_installed() {
    if [ -d "$INSTALL_DIR" ]; then
        return 0
    fi
    return 1
}

install() {
    # Check if already installed
    if check_installed; then
        echo ""
        echo -e "\033[0;33m⚠ Linear Coding Agent Harness is already installed\033[0m"
        echo "  Location: $INSTALL_DIR"
        echo ""
        echo "Options:"
        echo "  1) Update to latest version"
        echo "  2) Reinstall (fresh)"
        echo "  3) Skip (keep current installation)"
        echo ""
        read -p "Enter choice (1-3): " choice

        case $choice in
            1)
                echo ""
                echo "Updating Linear Coding Agent Harness..."
                cd "$INSTALL_DIR"
                git pull
                ./venv/bin/pip install -r requirements.txt
                echo ""
                echo -e "\033[0;32m✓ Updated successfully!\033[0m"
                return 0
                ;;
            2)
                echo ""
                echo "Removing existing installation..."
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

    echo "Installing Linear Coding Agent Harness..."

    # Check prerequisites
    if ! command -v claude &> /dev/null; then
        echo ""
        echo -e "\033[0;31m✗ Error: Claude Code CLI is not installed.\033[0m"
        echo "Please install Claude Code first using the menu."
        return 1
    fi

    if ! command -v python3 &> /dev/null; then
        echo ""
        echo -e "\033[0;31m✗ Error: Python 3 is not installed.\033[0m"
        return 1
    fi

    # Ensure python3-venv is available for virtual environment
    # Need to install the version-specific venv package (e.g., python3.11-venv)
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if command -v apt-get &> /dev/null; then
        # Check if package is actually installed (not just has leftover config files)
        if ! dpkg -s python${PYTHON_VERSION}-venv 2>/dev/null | grep -q "Status: install ok installed"; then
            echo "Installing python${PYTHON_VERSION}-venv..."
            sudo apt-get update -qq && sudo apt-get install -y python${PYTHON_VERSION}-venv
        fi
    elif ! python3 -m venv --help &> /dev/null; then
        echo -e "\033[0;31m✗ Error: python3-venv is not installed and cannot be auto-installed.\033[0m"
        echo "Please install it manually"
        return 1
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Linear Coding Agent Harness"
    echo ""
    echo "Autonomous coding agents integrated with Linear project management."
    echo "Repo: https://github.com/coleam00/Linear-Coding-Agent-Harness"
    echo ""
    echo "This will:"
    echo "  1. Clone the repository"
    echo "  2. Install Python dependencies"
    echo "  3. Configure MCP servers (Linear, Puppeteer)"
    echo "  4. Guide you through API key setup"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    read -p "Continue with installation? (y/n): " confirm

    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "Installation cancelled."
        return 0
    fi

    # Clone repository
    echo ""
    echo "Cloning repository..."
    git clone https://github.com/coleam00/Linear-Coding-Agent-Harness.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"

    # Create virtual environment and install dependencies
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv

    echo "Installing Python dependencies..."
    ./venv/bin/pip install -r requirements.txt

    # Setup MCP servers
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "MCP Server Configuration"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Linear MCP
    echo ""
    read -p "Configure Linear MCP server? (y/n): " setup_linear
    if [[ "$setup_linear" == "y" || "$setup_linear" == "Y" ]]; then
        echo ""
        echo "Get your Linear API key from: https://linear.app/settings/account/security"
        read -p "Enter your Linear API key: " linear_key
        if [ -n "$linear_key" ]; then
            claude mcp add linear -- npx -y @linear/mcp-server --api-key "$linear_key"
            echo -e "\033[0;32m✓ Linear MCP server configured!\033[0m"
        fi
    fi

    # Puppeteer MCP (optional)
    echo ""
    read -p "Configure Puppeteer MCP server for browser automation? (y/n): " setup_puppeteer
    if [[ "$setup_puppeteer" == "y" || "$setup_puppeteer" == "Y" ]]; then
        claude mcp add puppeteer -- npx -y @anthropic-ai/mcp-puppeteer
        echo -e "\033[0;32m✓ Puppeteer MCP server configured!\033[0m"
    fi

    # Claude OAuth token
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Claude OAuth Token Setup"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "The agent harness requires a Claude OAuth token."
    echo ""
    read -p "Run 'claude setup-token' now? (y/n): " setup_oauth
    if [[ "$setup_oauth" == "y" || "$setup_oauth" == "Y" ]]; then
        echo ""
        claude setup-token
        echo ""
        echo "Copy the token above and export it:"
        echo "  export CLAUDE_CODE_OAUTH_TOKEN='your-token'"
        echo ""
        read -p "Enter your OAuth token (or press Enter to skip): " oauth_token
        if [ -n "$oauth_token" ]; then
            # Add to shell profiles
            if ! grep -q "CLAUDE_CODE_OAUTH_TOKEN" ~/.zshrc 2>/dev/null; then
                echo "" >> ~/.zshrc
                echo "# Claude Code OAuth Token" >> ~/.zshrc
                echo "export CLAUDE_CODE_OAUTH_TOKEN='$oauth_token'" >> ~/.zshrc
            else
                sed -i "s|export CLAUDE_CODE_OAUTH_TOKEN=.*|export CLAUDE_CODE_OAUTH_TOKEN='$oauth_token'|" ~/.zshrc
            fi
            if ! grep -q "CLAUDE_CODE_OAUTH_TOKEN" ~/.bashrc 2>/dev/null; then
                echo "" >> ~/.bashrc
                echo "# Claude Code OAuth Token" >> ~/.bashrc
                echo "export CLAUDE_CODE_OAUTH_TOKEN='$oauth_token'" >> ~/.bashrc
            else
                sed -i "s|export CLAUDE_CODE_OAUTH_TOKEN=.*|export CLAUDE_CODE_OAUTH_TOKEN='$oauth_token'|" ~/.bashrc
            fi
            export CLAUDE_CODE_OAUTH_TOKEN="$oauth_token"
            echo -e "\033[0;32m✓ OAuth token configured!\033[0m"
        fi
    else
        echo ""
        echo "To set up later, run: claude setup-token"
        echo "Then export: export CLAUDE_CODE_OAUTH_TOKEN='your-token'"
    fi
    echo ""

    # Create convenience alias (using venv python)
    if ! grep -q 'alias linear-agent=' ~/.zshrc 2>/dev/null; then
        echo "" >> ~/.zshrc
        echo "# Linear Agent Harness" >> ~/.zshrc
        echo "alias linear-agent='${INSTALL_DIR}/venv/bin/python ${INSTALL_DIR}/autonomous_agent_demo.py'" >> ~/.zshrc
    fi
    if ! grep -q 'alias linear-agent=' ~/.bashrc 2>/dev/null; then
        echo "" >> ~/.bashrc
        echo "# Linear Agent Harness" >> ~/.bashrc
        echo "alias linear-agent='${INSTALL_DIR}/venv/bin/python ${INSTALL_DIR}/autonomous_agent_demo.py'" >> ~/.bashrc
    fi

    # Make alias available in current session
    alias linear-agent="${INSTALL_DIR}/venv/bin/python ${INSTALL_DIR}/autonomous_agent_demo.py"

    echo ""
    echo -e "\033[0;32m✓ Linear Coding Agent Harness installed!\033[0m"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Usage:"
    echo "  linear-agent --project-dir ./my_project"
    echo ""
    echo "Options:"
    echo "  --max-iterations N  Limit agent cycles"
    echo "  --model MODEL       Claude model (default: opus-4-5)"
    echo ""
    echo "Required environment variables:"
    echo "  CLAUDE_CODE_OAUTH_TOKEN  (run: claude setup-token)"
    echo "  LINEAR_API_KEY           (or configure via MCP)"
    echo ""
    echo "Install location: ${INSTALL_DIR}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    return 0
}

install
