#!/bin/bash
# Description: Z.AI GLM Coding Plan - Use GLM-4.7 models with Claude Code
set -e

CLAUDE_SETTINGS="$HOME/.claude/settings.json"

check_installed() {
    # Check if Claude Code is configured for Z.AI
    if [ -f "$CLAUDE_SETTINGS" ]; then
        if grep -q "api.z.ai" "$CLAUDE_SETTINGS" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

check_claude_installed() {
    command -v claude &> /dev/null
}

backup_settings() {
    if [ -f "$CLAUDE_SETTINGS" ]; then
        cp "$CLAUDE_SETTINGS" "${CLAUDE_SETTINGS}.backup.$(date +%Y%m%d%H%M%S)"
        echo -e "\033[0;32m✓ Backed up existing settings\033[0m"
    fi
}

configure_zai() {
    local api_key=$1

    # Create .claude directory if it doesn't exist
    mkdir -p "$HOME/.claude"

    # Check if settings.json exists and has content
    if [ -f "$CLAUDE_SETTINGS" ] && [ -s "$CLAUDE_SETTINGS" ]; then
        # Use Python to merge settings
        python3 <<EOF
import json

try:
    with open('$CLAUDE_SETTINGS', 'r') as f:
        settings = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    settings = {}

# Ensure env section exists
if 'env' not in settings:
    settings['env'] = {}

# Add Z.AI configuration
settings['env']['ANTHROPIC_AUTH_TOKEN'] = '$api_key'
settings['env']['ANTHROPIC_BASE_URL'] = 'https://api.z.ai/api/anthropic'
settings['env']['API_TIMEOUT_MS'] = '3000000'

with open('$CLAUDE_SETTINGS', 'w') as f:
    json.dump(settings, f, indent=2)

print("Settings updated successfully")
EOF
    else
        # Create new settings file
        cat > "$CLAUDE_SETTINGS" <<EOF
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "$api_key",
    "ANTHROPIC_BASE_URL": "https://api.z.ai/api/anthropic",
    "API_TIMEOUT_MS": "3000000"
  }
}
EOF
    fi
}

reset_to_anthropic() {
    if [ -f "$CLAUDE_SETTINGS" ]; then
        python3 <<EOF
import json

try:
    with open('$CLAUDE_SETTINGS', 'r') as f:
        settings = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    print("No settings to reset")
    exit(0)

if 'env' in settings:
    # Remove Z.AI specific settings
    settings['env'].pop('ANTHROPIC_AUTH_TOKEN', None)
    settings['env'].pop('ANTHROPIC_BASE_URL', None)
    settings['env'].pop('API_TIMEOUT_MS', None)

    # Remove env section if empty
    if not settings['env']:
        del settings['env']

# Remove empty settings file or write updated settings
if not settings:
    import os
    os.remove('$CLAUDE_SETTINGS')
    print("Settings file removed (was empty)")
else:
    with open('$CLAUDE_SETTINGS', 'w') as f:
        json.dump(settings, f, indent=2)
    print("Z.AI configuration removed")
EOF
        echo -e "\033[0;32m✓ Reset to Anthropic (default) configuration\033[0m"
    else
        echo "No settings file found - already using defaults"
    fi
}

install() {
    # Check if Claude Code is installed
    if ! check_claude_installed; then
        echo ""
        echo -e "\033[0;31m✗ Error: Claude Code CLI is not installed.\033[0m"
        echo "Please install Claude Code first using the menu."
        echo ""
        echo "Claude Code is required for Z.AI GLM Coding Plan integration."
        return 1
    fi

    # Check if already configured
    if check_installed; then
        echo ""
        echo -e "\033[0;33m⚠ Z.AI GLM Coding Plan is already configured\033[0m"
        echo ""
        echo "Options:"
        echo "  1) Update API key"
        echo "  2) Reset to Anthropic (default Claude)"
        echo "  3) Run automated helper (npx @z_ai/coding-helper)"
        echo "  4) Skip (keep current configuration)"
        echo ""
        read -p "Enter choice (1-4): " choice

        case $choice in
            1)
                echo ""
                read -p "Enter your new Z.AI API key: " api_key
                if [ -n "$api_key" ]; then
                    backup_settings
                    configure_zai "$api_key"
                    echo -e "\033[0;32m✓ API key updated!\033[0m"
                fi
                return 0
                ;;
            2)
                echo ""
                backup_settings
                reset_to_anthropic
                echo ""
                echo "Claude Code will now use Anthropic's models."
                echo "Restart Claude Code for changes to take effect."
                return 0
                ;;
            3)
                echo ""
                echo "Running Z.AI Coding Tool Helper..."
                npx @z_ai/coding-helper
                return 0
                ;;
            4)
                echo ""
                echo "Keeping current configuration."
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
    echo "Z.AI GLM Coding Plan Setup"
    echo ""
    echo "This configures Claude Code to use Z.AI's GLM-4.7 models."
    echo ""
    echo "Model Mapping:"
    echo "  • Opus  → GLM-4.7"
    echo "  • Sonnet → GLM-4.7"
    echo "  • Haiku  → GLM-4.5-Air"
    echo ""
    echo "Pricing: Starting at \$3/month"
    echo "  • Lite: ~120 prompts/5hrs"
    echo "  • Pro:  ~600 prompts/5hrs"
    echo "  • Max:  ~2,400 prompts/5hrs"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Choose setup method:"
    echo "  1) Automated helper (recommended)"
    echo "  2) Manual configuration (enter API key)"
    echo "  3) Skip"
    echo ""
    read -p "Enter choice (1-3): " setup_choice

    case $setup_choice in
        1)
            echo ""
            echo "Running Z.AI Coding Tool Helper..."
            echo ""
            echo "This will guide you through:"
            echo "  • Language selection"
            echo "  • Plan selection"
            echo "  • API key entry"
            echo "  • Tool configuration"
            echo "  • MCP server setup (optional)"
            echo ""
            npx @z_ai/coding-helper

            echo ""
            echo -e "\033[0;32m✓ Z.AI GLM Coding Plan setup complete!\033[0m"
            ;;

        2)
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "Manual Configuration"
            echo ""
            echo "Get your API key from: https://z.ai/model-api"
            echo "(Subscribe to a Coding Plan first if you haven't)"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            read -p "Enter your Z.AI API key (or press Enter to skip): " api_key

            if [ -n "$api_key" ]; then
                backup_settings
                configure_zai "$api_key"

                echo ""
                echo -e "\033[0;32m✓ Z.AI GLM Coding Plan configured!\033[0m"
                echo ""
                echo "Configuration saved to: $CLAUDE_SETTINGS"
                echo ""
                echo "To verify: Run 'claude' and check /status"
                echo ""
                echo "To reset to Anthropic later:"
                echo "  Run this setup again and choose 'Reset to Anthropic'"
            else
                echo ""
                echo "Skipped. You can configure later by running this setup again."
            fi
            ;;

        3)
            echo ""
            echo "Skipping Z.AI GLM Coding Plan setup."
            echo ""
            echo "You can configure later using:"
            echo "  • Automated: npx @z_ai/coding-helper"
            echo "  • Manual: Edit ~/.claude/settings.json"
            echo ""
            echo "Documentation: https://docs.z.ai/devpack/overview"
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
    echo "Included MCP Servers (configure via coding-helper):"
    echo "  • Vision Understanding"
    echo "  • Web Search"
    echo "  • Web Reader"
    echo "  • Zread"
    echo ""
    echo "Restart Claude Code for changes to take effect."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    return 0
}

install
