#!/bin/bash
# Description: BMAD v6 - Agent-as-Code framework for AI-driven development
set -e

check_installed() {
    # Check for npm installation
    if command -v bmad &> /dev/null; then
        return 0
    fi
    # Check for pip installation
    if pip show bmad-method &> /dev/null 2>&1; then
        return 0
    fi
    return 1
}

install() {
    # Check if already installed
    if check_installed; then
        echo ""
        echo -e "\033[0;33m⚠ BMAD is already installed\033[0m"
        if command -v bmad &> /dev/null; then
            echo "  Type: npm/npx"
        else
            echo "  Type: pip"
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
                echo "Proceeding with reinstallation..."
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
    echo "BMAD v6 Installation"
    echo ""
    echo "Choose installation method:"
    echo "  1) Node.js/NPX (Alpha - Recommended)"
    echo "  2) Python (pip)"
    echo "  3) Skip installation"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    read -p "Enter choice (1-3): " install_choice

    case $install_choice in
        1)
            echo ""
            echo "Installing BMAD v6 Alpha via NPX..."
            echo ""

            # Check Node.js version
            NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
            if [ "$NODE_VERSION" -lt 20 ]; then
                echo -e "\033[0;31m✗ Error: Node.js v20+ is required (you have v$NODE_VERSION)\033[0m"
                return 1
            fi

            # Install BMAD v6 Alpha
            npx bmad-method@alpha install

            echo ""
            echo -e "\033[0;32m✓ BMAD v6 Alpha installed successfully!\033[0m"
            echo ""
            echo "To initialize a workspace:"
            echo "  bmad init"
            echo ""
            echo "This will:"
            echo "  • Set up the guided workflow system"
            echo "  • Create .bmad/ directory structure"
            echo "  • Configure IDE integration"
            echo "  • Activate the Analyst agent"
            ;;

        2)
            echo ""
            echo "Installing BMAD v6 via pip..."
            echo ""

            pip install bmad-method==6.0.0a0

            echo ""
            echo -e "\033[0;32m✓ BMAD v6 installed successfully!\033[0m"
            echo ""
            echo "To initialize a workspace:"
            echo "  bmad init"
            ;;

        3)
            echo ""
            echo "Skipping BMAD v6 installation."
            echo ""
            echo "You can install it later using:"
            echo "  • NPX (Alpha): npx bmad-method@alpha install"
            echo "  • NPX (Stable v4): npx bmad-method install"
            echo "  • pip: pip install bmad-method==6.0.0a0"
            echo ""
            echo "Documentation: https://bmadcodes.com/v6-alpha/"
            return 0
            ;;

        *)
            echo ""
            echo "Invalid choice. Skipping installation."
            return 1
            ;;
    esac

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "BMAD v6 Key Features:"
    echo "  • Agent-as-Code for deterministic planning"
    echo "  • Scale-adaptive intelligence"
    echo "  • Visual workflow management"
    echo "  • First-class observability and replay"
    echo "  • 90% reduction in token usage vs traditional approaches"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    return 0
}

install
