#!/bin/bash
# Description: 1Password CLI for secret management and authentication
set -e

# Source shared helpers
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../helpers.sh"

check_installed() {
    if command -v op &> /dev/null; then
        return 0
    fi
    return 1
}

install() {
    # Check if already installed
    if check_installed; then
        local current_version=$(op --version 2>/dev/null || echo 'unknown')
        echo ""
        echo -e "\033[0;33m⚠ 1Password CLI is already installed\033[0m"
        echo "  Current version: $current_version"
        echo ""
        echo "Options:"
        echo "  1) Upgrade to latest version"
        echo "  2) Reinstall"
        echo "  3) Skip (keep current installation)"
        echo ""
        read -p "Enter choice (1-3): " choice

        case $choice in
            1|2)
                echo ""
                echo "Removing existing installation..."
                if sudo -n true 2>/dev/null; then
                    sudo rm -f /usr/local/bin/op
                else
                    rm -f ~/.local/bin/op 2>/dev/null || true
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
    fi

    echo "Installing 1Password CLI..."

    # Detect architecture
    ARCH=$(dpkg --print-architecture)

    # Map architecture names to 1Password naming
    case "$ARCH" in
        amd64) OP_ARCH="amd64" ;;
        arm64) OP_ARCH="arm64" ;;
        i386) OP_ARCH="386" ;;
        armhf) OP_ARCH="arm" ;;
        *)
            echo -e "\033[0;31m✗ Unsupported architecture: $ARCH\033[0m"
            return 1
            ;;
    esac

    # Get latest version from GitHub API
    echo "Fetching latest 1Password CLI version..."
    VERSION=$(curl -s https://app-updates.agilebits.com/check/1/0/CLI2/en/2000000 | grep -o '"version":"[^"]*' | cut -d'"' -f4)

    if [ -z "$VERSION" ]; then
        echo "Failed to fetch latest version, using direct download..."
        # Fallback to direct download
        cd /tmp
        curl -sSfLo op.zip "https://cache.agilebits.com/dist/1P/op2/pkg/v2.30.0/op_linux_${OP_ARCH}_v2.30.0.zip"
    else
        echo "  Latest version: $VERSION"
        cd /tmp
        curl -sSfLo op.zip "https://cache.agilebits.com/dist/1P/op2/pkg/v${VERSION}/op_linux_${OP_ARCH}_v${VERSION}.zip"
    fi

    # Install unzip if not available
    if ! command -v unzip &> /dev/null; then
        if sudo -n true 2>/dev/null; then
            sudo apt-get update -qq && sudo apt-get install -y -qq unzip
        else
            echo "Error: unzip is required but sudo is not available to install it"
            return 1
        fi
    fi

    # Extract and install
    unzip -q op.zip
    if sudo -n true 2>/dev/null; then
        sudo mv op /usr/local/bin/
        sudo chmod +x /usr/local/bin/op
    else
        echo "Note: sudo not available, installing to ~/.local/bin..."
        mkdir -p ~/.local/bin
        mv op ~/.local/bin/
        chmod +x ~/.local/bin/op
        add_to_path "$HOME/.local/bin"
    fi

    # Cleanup
    rm -f op.zip

    # Verify installation
    if command -v op &> /dev/null; then
        echo ""
        echo -e "\033[0;32m✓ 1Password CLI installed successfully!\033[0m"
        echo "  Version: $(op --version)"
        echo ""

        # Prompt for authentication
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Would you like to authenticate with 1Password now?"
        echo ""
        echo "Choose authentication method:"
        echo "  1) Sign in with account (interactive)"
        echo "  2) Use service account token"
        echo "  3) Skip (configure later)"
        echo ""
        read -p "Enter choice (1-3): " auth_choice

        case $auth_choice in
            1)
                echo ""
                echo "Please enter your 1Password account details..."
                echo ""
                read -p "Enter your sign-in address (my.1password.com): " signin_address

                # Default to my.1password.com if empty
                signin_address=${signin_address:-my.1password.com}

                echo ""
                read -p "Enter your email address: " email_address

                if [ -z "$email_address" ]; then
                    echo ""
                    echo -e "\033[0;33mEmail address is required. Skipping authentication.\033[0m"
                    echo "You can authenticate later by running:"
                    echo "  eval \$(op signin)"
                else
                    echo ""
                    echo "Signing in to $signin_address..."
                    eval "$(op account add --address $signin_address --email $email_address --signin)"

                    if [ $? -eq 0 ]; then
                        echo ""
                        echo -e "\033[0;32m✓ Successfully authenticated with 1Password!\033[0m"
                        echo ""
                        echo "Note: This session will expire. To sign in again, run:"
                        echo "  eval \$(op signin)"
                    else
                        echo ""
                        echo -e "\033[0;33mAuthentication failed or was cancelled.\033[0m"
                        echo "You can authenticate later by running:"
                        echo "  eval \$(op signin)"
                    fi
                fi
                ;;
            2)
                echo ""
                echo "To use a service account token:"
                echo "  1. Get your token from: https://my.1password.com/developer"
                echo "  2. Add to your shell profiles (~/.bashrc and ~/.zshrc):"
                echo "     export OP_SERVICE_ACCOUNT_TOKEN=<your-token>"
                echo "  3. Reload your shell: source ~/.bashrc (or ~/.zshrc)"
                echo ""
                read -p "Would you like to set the token now? (y/n): " set_token

                if [[ $set_token =~ ^[Yy]$ ]]; then
                    read -sp "Enter your service account token: " token
                    echo ""

                    if [ -n "$token" ]; then
                        add_env_to_profiles "OP_SERVICE_ACCOUNT_TOKEN" "\"$token\"" "# 1Password service account token"

                        echo ""
                        echo -e "\033[0;32m✓ Service account token configured!\033[0m"
                        echo "  Added to ~/.bashrc and ~/.zshrc for persistence"
                        echo "  Testing connection..."

                        if op account list &>/dev/null; then
                            echo -e "\033[0;32m✓ Successfully authenticated with 1Password!\033[0m"
                        else
                            echo -e "\033[0;33m⚠ Token set but connection test failed.\033[0m"
                            echo "  Please verify your token is correct."
                        fi
                    fi
                fi
                ;;
            3)
                echo ""
                echo "Skipping authentication. You can authenticate later with:"
                echo "  • Interactive: eval \$(op signin)"
                echo "  • Service account: export OP_SERVICE_ACCOUNT_TOKEN=<token>"
                echo ""
                echo "Documentation: https://developer.1password.com/docs/cli"
                ;;
            *)
                echo ""
                echo "Invalid choice. Skipping authentication."
                echo ""
                echo "To authenticate later, run:"
                echo "  eval \$(op signin)"
                ;;
        esac

        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        return 0
    else
        echo ""
        echo -e "\033[0;31m✗ Failed to install 1Password CLI\033[0m"
        return 1
    fi
}

install
