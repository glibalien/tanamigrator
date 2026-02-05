#!/bin/bash
# Description: SpecStory CLI - Auto-save AI conversations for Claude Code, Codex, Gemini
set -e

check_installed() {
    if command -v specstory &> /dev/null; then
        return 0
    fi
    return 1
}

install_via_homebrew() {
    echo "Installing SpecStory via Homebrew..."
    brew tap specstoryai/tap
    brew install specstory
}

install_via_binary() {
    echo "Installing SpecStory via binary download..."

    # Detect architecture
    ARCH=$(uname -m)
    OS=$(uname -s)

    case "$ARCH" in
        x86_64)
            ARCH_NAME="x86_64"
            ;;
        aarch64|arm64)
            ARCH_NAME="arm64"
            ;;
        *)
            echo "Unsupported architecture: $ARCH"
            return 1
            ;;
    esac

    case "$OS" in
        Linux)
            OS_NAME="Linux"
            EXT="tar.gz"
            ;;
        Darwin)
            OS_NAME="Darwin"
            EXT="zip"
            ;;
        *)
            echo "Unsupported OS: $OS"
            return 1
            ;;
    esac

    # Get latest release URL
    DOWNLOAD_URL=$(curl -s https://api.github.com/repos/specstoryai/getspecstory/releases/latest | \
        grep "browser_download_url.*SpecStoryCLI_${OS_NAME}_${ARCH_NAME}\.${EXT}" | \
        cut -d '"' -f 4)

    if [ -z "$DOWNLOAD_URL" ]; then
        echo "Could not find download URL for ${OS_NAME}_${ARCH_NAME}"
        return 1
    fi

    echo "Downloading from: $DOWNLOAD_URL"

    # Download and extract
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"

    if [ "$EXT" = "tar.gz" ]; then
        curl -sL "$DOWNLOAD_URL" | tar xz
    else
        curl -sL "$DOWNLOAD_URL" -o specstory.zip
        unzip -q specstory.zip
    fi

    # Install binary
    if [ -f "specstory" ]; then
        sudo mv specstory /usr/local/bin/
        sudo chmod +x /usr/local/bin/specstory
    else
        echo "Binary not found in archive"
        cd - > /dev/null
        rm -rf "$TEMP_DIR"
        return 1
    fi

    cd - > /dev/null
    rm -rf "$TEMP_DIR"
}

install() {
    # Check if already installed
    if check_installed; then
        local current_version=$(specstory --version 2>/dev/null || echo 'unknown')
        echo ""
        echo -e "\033[0;33m⚠ SpecStory CLI is already installed\033[0m"
        echo "  Current version: $current_version"
        echo ""
        echo "Options:"
        echo "  1) Upgrade to latest version"
        echo "  2) Reinstall current version"
        echo "  3) Skip (keep current installation)"
        echo ""
        read -p "Enter choice (1-3): " choice

        case $choice in
            1|2)
                echo ""
                if command -v brew &> /dev/null; then
                    brew upgrade specstory 2>/dev/null || brew install specstory
                else
                    install_via_binary
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
        echo "SpecStory CLI - Auto-save AI conversations"
        echo "==========================================="
        echo ""
        echo "Installation method:"
        echo "  1) Homebrew (recommended if available)"
        echo "  2) Binary download (universal)"
        echo ""

        if command -v brew &> /dev/null; then
            read -p "Enter choice (1-2) [1]: " method
            method=${method:-1}
        else
            echo "Homebrew not detected, using binary download..."
            method=2
        fi

        case $method in
            1)
                install_via_homebrew
                ;;
            2)
                install_via_binary
                ;;
            *)
                install_via_binary
                ;;
        esac
    fi

    # Verify installation
    if command -v specstory &> /dev/null; then
        echo ""
        echo -e "\033[0;32m✓ SpecStory CLI installed successfully!\033[0m"
        echo "  Version: $(specstory --version 2>/dev/null || echo 'installed')"

        # Check for compatible agents
        echo ""
        echo "Checking for compatible AI agents..."
        specstory check 2>/dev/null || true

        # Add aliases to shell profiles
        # Note: Use -c flag with quoted command for custom invocations
        ALIAS_CLAUDE='alias claude-ss="specstory run claude"'
        ALIAS_CLAUDE_DEV='alias claude-dev-ss="specstory run claude -c \"claude --dangerously-skip-permissions\""'
        ALIAS_CODEX='alias codex-ss="specstory run codex"'
        ALIAS_GEMINI='alias gemini-ss="specstory run gemini"'

        for profile in ~/.zshrc ~/.bashrc; do
            if [ -f "$profile" ]; then
                if ! grep -q 'alias claude-ss=' "$profile" 2>/dev/null; then
                    echo "" >> "$profile"
                    echo "# SpecStory aliases for auto-saved sessions" >> "$profile"
                    echo "# Use -c \"command\" for custom invocations" >> "$profile"
                    echo "$ALIAS_CLAUDE" >> "$profile"
                    echo "$ALIAS_CLAUDE_DEV" >> "$profile"
                    echo "$ALIAS_CODEX" >> "$profile"
                    echo "$ALIAS_GEMINI" >> "$profile"
                fi
            fi
        done

        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Usage:"
        echo "  specstory check                    - Show installed AI agents"
        echo "  specstory run claude               - Launch Claude Code with auto-save"
        echo "  specstory run -c \"claude --flag\"   - Custom command with flags"
        echo "  specstory run codex                - Launch Codex with auto-save"
        echo "  specstory run gemini               - Launch Gemini with auto-save"
        echo ""
        echo "Aliases added (restart shell or source profile):"
        echo "  claude-ss      - Shortcut for 'specstory run claude'"
        echo "  claude-dev-ss  - Dev mode (skips permission prompts)"
        echo "  codex-ss       - Shortcut for 'specstory run codex'"
        echo "  gemini-ss      - Shortcut for 'specstory run gemini'"
        echo ""
        echo "Sessions saved to: .specstory/history/ (in your project)"
        echo ""
        echo "Optional cloud sync: Run 'specstory login' to enable"
        echo "Documentation: https://docs.specstory.com/"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        return 0
    else
        echo ""
        echo -e "\033[0;31m✗ Failed to install SpecStory CLI\033[0m"
        return 1
    fi
}

install
