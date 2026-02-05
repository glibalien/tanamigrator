#!/bin/bash
# Description: GitHub SpecKit - Spec-driven development toolkit for AI agents
set -e

check_installed() {
    # Check if uv/uvx is available (SpecKit uses uvx to run)
    if command -v uvx &> /dev/null; then
        return 0
    fi
    return 1
}

install() {
    # Check if already installed
    if check_installed; then
        echo ""
        echo -e "\033[0;33m⚠ SpecKit dependencies (uv/uvx) are already installed\033[0m"
        echo ""
        echo "Options:"
        echo "  1) Upgrade uv and initialize a new project"
        echo "  2) Just initialize a new SpecKit project"
        echo "  3) Skip"
        echo ""
        read -p "Enter choice (1-3): " choice

        case $choice in
            1)
                echo ""
                echo "Upgrading uv..."
                curl -LsSf https://astral.sh/uv/install.sh | sh
                export PATH="$HOME/.cargo/bin:$PATH"
                ;;
            2)
                # Continue to project initialization
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
        echo "Installing GitHub SpecKit..."

        # Install uv (Python package installer that provides uvx)
        echo "Installing uv (Python package installer)..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "SpecKit Installation"
    echo ""
    echo "SpecKit is a toolkit for spec-driven development that works with:"
    echo "  • GitHub Copilot"
    echo "  • Claude Code"
    echo "  • Gemini CLI"
    echo "  • Other AI coding assistants"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    read -p "Do you want to initialize a SpecKit project? (y/n): " init_project

    if [[ $init_project =~ ^[Yy]$ ]]; then
        read -p "Enter project name: " project_name

        if [ -z "$project_name" ]; then
            echo ""
            echo -e "\033[0;33mNo project name provided. Skipping initialization.\033[0m"
            echo ""
            echo "You can initialize a project later with:"
            echo "  uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME>"
            return 0
        fi

        echo ""
        echo "Initializing SpecKit project: $project_name"
        echo ""

        uvx --from git+https://github.com/github/spec-kit.git specify init "$project_name"

        echo ""
        echo -e "\033[0;32m✓ SpecKit project initialized successfully!\033[0m"
        echo ""
        echo "Project created at: ./$project_name"
        echo ""
        echo "Next steps:"
        echo "  1. cd $project_name"
        echo "  2. Use /specify to create specifications"
        echo "  3. Use /plan to generate implementation plans"
        echo "  4. Use /tasks to break down into actionable tasks"
        echo ""
        echo "SpecKit follows a spec-driven workflow:"
        echo "  Spec → Plan → Code → Test → Validate"

    else
        echo ""
        echo -e "\033[0;32m✓ SpecKit tools are ready via uvx.\033[0m"
        echo ""
        echo "To initialize a project later:"
        echo "  uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME>"
        echo ""
        echo "Documentation: https://github.com/github/spec-kit"
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    return 0
}

install
