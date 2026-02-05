#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FEATURES_DIR="${SCRIPT_DIR}/features"
MANIFEST_FILE="${SCRIPT_DIR}/manifest.json"

# Source helpers for feature summary management
source "${SCRIPT_DIR}/helpers.sh"

# Feature metadata: category, description, location, commands, env_vars
# Format: FEATURE_META[name]="category|description|location|commands|env_vars"
declare -A FEATURE_META
FEATURE_META=(
    ["1password-cli"]="Core Tools|1Password CLI for secret management|/usr/local/bin/op|op|OP_SERVICE_ACCOUNT_TOKEN"
    ["docker-outside"]="Core Tools|Docker-outside-of-Docker for host Docker access|/var/run/docker.sock|docker|None"
    ["claude-code"]="AI CLI Tools|Anthropic Claude Code CLI for AI-powered coding|npm global|claude, claude-dev|ANTHROPIC_API_KEY"
    ["codex-cli"]="AI CLI Tools|OpenAI Codex CLI coding assistant|npm global|codex|OPENAI_API_KEY"
    ["gemini-cli"]="AI CLI Tools|Google Gemini CLI assistant|npm global|gemini|GOOGLE_API_KEY"
    ["z-ai"]="AI CLI Tools|Z.AI GLM Coding Plan (Claude Code backend)|~/.claude/settings.json|claude (via GLM)|ANTHROPIC_AUTH_TOKEN"
    ["agent-browser"]="AI CLI Tools|Vercel headless browser for AI agents|npm global|agent-browser|None"
    ["specstory"]="AI CLI Tools|Auto-save AI conversations|/usr/local/bin/specstory|specstory, claude-ss|None"
    ["mcp-archon"]="MCP Servers|Local AI agent management MCP|Claude MCP config|claude mcp|None"
    ["mcp-context7"]="MCP Servers|Dynamic documentation injection MCP|npm global|npx @upstash/context7-mcp|None"
    ["mcp-linear"]="MCP Servers|Linear project management MCP|npm global|npx linear-mcp-server|LINEAR_API_KEY"
    ["mcp-openmemory"]="MCP Servers|AI memory persistence MCP|npm global|npx openmemory|OPENMEMORY_API_KEY"
    ["mcp-perplexity"]="MCP Servers|AI-powered web search MCP|npm global|npx @perplexity-ai/mcp-server|PERPLEXITY_API_KEY"
    ["mcp-puppeteer"]="MCP Servers|Browser automation MCP|npm global|npx @modelcontextprotocol/server-puppeteer|None"
    ["bmad-v6"]="Orchestration|Agent-as-Code framework|pip install|bmad|None"
    ["codemachine"]="Orchestration|Multi-agent autonomous platform|local install|codemachine, cm|None"
    ["speckit"]="Orchestration|Spec-driven development toolkit|uvx|uvx specify|None"
    ["linear-agent-harness"]="Orchestration|Autonomous coding via Linear issues|~/.local/share/linear-agent-harness|linear-agent|CLAUDE_CODE_OAUTH_TOKEN"
    ["vibe-kanban"]="Orchestration|Multi-agent task orchestration|npm global or ~/.local|vibe-kanban, vk|None"
    ["auto-claude"]="Orchestration|Autonomous multi-agent coding|~/.local/share/auto-claude|ac, ac-spec, ac-list|CLAUDE_CODE_OAUTH_TOKEN"
    ["agent-os"]="Orchestration|Standards-driven AI development framework|~/agent-os|~/agent-os/scripts/*|None"
    ["ccusage"]="AI CLI Tools|Claude Code usage and cost tracking CLI|npm global|ccusage|None"
)

# Initialize manifest if it doesn't exist
init_manifest() {
    if [ ! -f "$MANIFEST_FILE" ]; then
        echo '{"installed": {}, "last_updated": ""}' > "$MANIFEST_FILE"
    fi
}

# Check if a feature is actually installed on the system
check_system_installed() {
    local feature=$1

    case $feature in
        "claude-code")
            command -v claude &> /dev/null && return 0 || return 1
            ;;
        "codex-cli")
            command -v codex &> /dev/null && return 0 || return 1
            ;;
        "gemini-cli")
            command -v gemini &> /dev/null && return 0 || return 1
            ;;
        "z-ai")
            # Check if Claude Code is configured for Z.AI
            [ -f "$HOME/.claude/settings.json" ] && grep -q "api.z.ai" "$HOME/.claude/settings.json" 2>/dev/null && return 0 || return 1
            ;;
        "1password-cli")
            command -v op &> /dev/null && return 0 || return 1
            ;;
        "docker-outside")
            command -v docker &> /dev/null && docker ps &> /dev/null && return 0 || return 1
            ;;
        "mcp-context7")
            npm list -g @upstash/context7-mcp &> /dev/null && return 0 || return 1
            ;;
        "mcp-linear")
            npm list -g linear-mcp-server &> /dev/null && return 0 || return 1
            ;;
        "mcp-openmemory")
            npm list -g openmemory &> /dev/null && return 0 || return 1
            ;;
        "mcp-perplexity")
            npm list -g @perplexity-ai/mcp-server &> /dev/null && return 0
            [ -d "/usr/local/lib/perplexity-mcp" ] && return 0
            return 1
            ;;
        "mcp-puppeteer")
            npm list -g @modelcontextprotocol/server-puppeteer &> /dev/null && return 0 || return 1
            ;;
        "mcp-archon")
            command -v claude &> /dev/null && claude mcp list 2>/dev/null | grep -q "archon" && return 0 || return 1
            ;;
        "bmad-v6")
            command -v bmad &> /dev/null && return 0
            pip show bmad-method &> /dev/null 2>&1 && return 0
            return 1
            ;;
        "codemachine")
            command -v codemachine &> /dev/null || command -v cm &> /dev/null && return 0 || return 1
            ;;
        "speckit")
            command -v uvx &> /dev/null && return 0 || return 1
            ;;
        "linear-agent-harness")
            [ -d "${HOME}/.local/share/linear-agent-harness" ] && return 0 || return 1
            ;;
        "agent-browser")
            command -v agent-browser &> /dev/null && return 0 || return 1
            ;;
        "specstory")
            command -v specstory &> /dev/null && return 0 || return 1
            ;;
        "vibe-kanban")
            command -v vibe-kanban &> /dev/null && return 0
            npm list -g vibe-kanban &> /dev/null && return 0
            return 1
            ;;
        "auto-claude")
            [ -d "${HOME}/.local/share/auto-claude" ] && [ -f "${HOME}/.local/share/auto-claude/apps/backend/run.py" ] && return 0 || return 1
            ;;
        "agent-os")
            [ -d "${HOME}/agent-os" ] && [ -f "${HOME}/agent-os/config.yml" ] && return 0 || return 1
            ;;
        "ccusage")
            command -v ccusage &> /dev/null && return 0 || return 1
            ;;
        *)
            return 1
            ;;
    esac
}

# Mark feature as installed
mark_installed() {
    local feature=$1
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local temp_file=$(mktemp)

    # Update manifest using Python for JSON manipulation
    # Write to temp file first to avoid reading from truncated file
    python3 <<EOF > "$temp_file"
import json

with open('$MANIFEST_FILE', 'r') as f:
    manifest = json.load(f)

manifest['installed']['$feature'] = '$timestamp'
manifest['last_updated'] = '$timestamp'

print(json.dumps(manifest, indent=2))
EOF

    # Move temp file to manifest
    mv "$temp_file" "$MANIFEST_FILE"
}

# Detect environment
detect_environment() {
    local env="Unknown"

    if [ -n "$CODESPACES" ]; then
        env="GitHub Codespaces"
    elif [ -n "$GITPOD_WORKSPACE_ID" ]; then
        env="Gitpod"
    elif [ -f "/.dockerenv" ] || [ -f "/run/.containerenv" ]; then
        if [ -S "/var/run/docker.sock" ]; then
            env="DevContainer (Docker Available)"
        else
            env="DevContainer"
        fi
    fi

    echo "$env"
}

# Display header
show_header() {
    clear
    local environment=$(detect_environment)

    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║        DevContainer Feature Installation Menu             ║${NC}"
    echo -e "${BLUE}╠════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${BLUE}║  Environment: ${environment}$(printf '%*s' $((46-${#environment})) '')║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}Legend: ${GREEN}[✓ INSTALLED]${NC} ${YELLOW}[○ NOT INSTALLED]${NC}"
    echo ""
}

# List available features
list_features() {
    echo -e "${YELLOW}Available Features:${NC}"
    echo ""

    local index=1
    declare -a feature_files

    # Define categories and their features
    declare -A categories
    categories=(
        ["Core Tools"]="1password-cli docker-outside"
        ["AI CLI Tools"]="claude-code codex-cli gemini-cli z-ai agent-browser specstory ccusage"
        ["MCP Servers"]="mcp-archon mcp-context7 mcp-linear mcp-openmemory mcp-perplexity mcp-puppeteer"
        ["Orchestration"]="bmad-v6 codemachine speckit linear-agent-harness vibe-kanban auto-claude agent-os"
    )

    # Display features by category
    for category in "Core Tools" "AI CLI Tools" "MCP Servers" "Orchestration"; do
        echo -e "${BLUE}${category}:${NC}"

        for feature_name in ${categories[$category]}; do
            local feature_file="$FEATURES_DIR/${feature_name}.sh"

            if [ -f "$feature_file" ]; then
                local status=""

                if check_system_installed "$feature_name"; then
                    status="${GREEN}[✓ INSTALLED]${NC}"
                else
                    status="${YELLOW}[○ NOT INSTALLED]${NC}"
                fi

                # Get description from feature file
                local description=$(grep "^# Description:" "$feature_file" | sed 's/# Description: //')

                printf "  %2d. %-25s %b\n" "$index" "$feature_name" "$status"
                echo -e "      ${description}"
                echo ""

                feature_files[$index]=$feature_file
                ((index++))
            fi
        done
    done

    echo -e "${BLUE}─────────────────────────────────────────────────────────────${NC}"
    echo -e "  ${index}. Install All Features"
    echo -e "  A. Install/Update Shell Aliases"
    echo -e "  R. Rebuild Installed Features Summary"
    echo -e "  0. Exit"
    echo -e "${BLUE}─────────────────────────────────────────────────────────────${NC}"
    echo ""
}

# Get version for installed feature
get_feature_version() {
    local feature_name=$1
    local version="N/A"

    case $feature_name in
        "claude-code") version=$(claude --version 2>/dev/null | head -1 || echo "installed") ;;
        "codex-cli") version=$(codex --version 2>/dev/null | head -1 || echo "installed") ;;
        "gemini-cli") version=$(gemini --version 2>/dev/null | head -1 || echo "installed") ;;
        "specstory") version=$(specstory --version 2>/dev/null | head -1 || echo "installed") ;;
        "agent-browser") version=$(agent-browser --version 2>/dev/null | head -1 || echo "installed") ;;
        "1password-cli") version=$(op --version 2>/dev/null | head -1 || echo "installed") ;;
        "docker-outside") version=$(docker --version 2>/dev/null | head -1 || echo "installed") ;;
        "vibe-kanban") version=$(vibe-kanban --version 2>/dev/null | head -1 || echo "installed") ;;
        *) version="installed" ;;
    esac

    echo "$version"
}

# Install a feature
install_feature() {
    local feature_file=$1
    local feature_name=$(basename "$feature_file" .sh)

    echo -e "${BLUE}Installing ${feature_name}...${NC}"

    # Source the feature file and run install
    if bash "$feature_file"; then
        mark_installed "$feature_name"

        # Update installed features summary
        if [ -n "${FEATURE_META[$feature_name]}" ]; then
            IFS='|' read -r category description location commands env_vars <<< "${FEATURE_META[$feature_name]}"
            local version=$(get_feature_version "$feature_name")
            add_feature_to_summary "$feature_name" "$category" "$description" "$version" "$location" "$commands" "$env_vars"
        fi

        echo -e "${GREEN}✓ ${feature_name} installed successfully!${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to install ${feature_name}${NC}"
        return 1
    fi
}

# Install all features
install_all() {
    echo -e "${BLUE}Installing all features...${NC}"
    echo ""

    local success_count=0
    local fail_count=0
    local skip_count=0

    for feature_file in "$FEATURES_DIR"/*.sh; do
        if [ -f "$feature_file" ]; then
            local feature_name=$(basename "$feature_file" .sh)

            # Check if already installed
            if check_system_installed "$feature_name"; then
                echo -e "${CYAN}Skipping ${feature_name} (already installed)${NC}"
                ((skip_count++))
            else
                if install_feature "$feature_file"; then
                    ((success_count++))
                else
                    ((fail_count++))
                fi
            fi
            echo ""
        fi
    done

    echo -e "${BLUE}─────────────────────────────────────────────────────────────${NC}"
    echo -e "${GREEN}Successfully installed: ${success_count}${NC}"
    if [ $skip_count -gt 0 ]; then
        echo -e "${CYAN}Skipped (already installed): ${skip_count}${NC}"
    fi
    if [ $fail_count -gt 0 ]; then
        echo -e "${RED}Failed: ${fail_count}${NC}"
    fi
}

# Add alias to shell profiles if not already present
add_alias_to_profiles() {
    local alias_name=$1
    local alias_cmd=$2
    local added=0

    for profile in ~/.zshrc ~/.bashrc; do
        if [ -f "$profile" ]; then
            if ! grep -q "alias ${alias_name}=" "$profile" 2>/dev/null; then
                echo "alias ${alias_name}=\"${alias_cmd}\"" >> "$profile"
                added=1
            fi
        fi
    done

    return $added
}

# Install aliases for installed services
install_aliases() {
    echo -e "${BLUE}Installing aliases for installed services...${NC}"
    echo ""

    local added_count=0
    local skipped_count=0

    # Claude Code aliases
    if check_system_installed "claude-code"; then
        echo -e "${CYAN}Claude Code:${NC}"
        if add_alias_to_profiles "claude-dev" "claude --dangerously-skip-permissions"; then
            echo -e "  ${GREEN}✓ Added: claude-dev${NC}"
            ((added_count++))
            alias claude-dev="claude --dangerously-skip-permissions" 2>/dev/null
        else
            echo -e "  ${YELLOW}○ Already exists: claude-dev${NC}"
            ((skipped_count++))
        fi
        echo ""
    fi

    # SpecStory aliases (requires specstory installed)
    if check_system_installed "specstory"; then
        echo -e "${CYAN}SpecStory:${NC}"

        if add_alias_to_profiles "claude-ss" "specstory run claude"; then
            echo -e "  ${GREEN}✓ Added: claude-ss${NC}"
            ((added_count++))
        else
            echo -e "  ${YELLOW}○ Already exists: claude-ss${NC}"
            ((skipped_count++))
        fi

        # Use single quotes to preserve the escaped quotes
        if ! grep -q 'alias claude-dev-ss=' ~/.zshrc 2>/dev/null && ! grep -q 'alias claude-dev-ss=' ~/.bashrc 2>/dev/null; then
            for profile in ~/.zshrc ~/.bashrc; do
                if [ -f "$profile" ]; then
                    echo 'alias claude-dev-ss="specstory run claude -c \"claude --dangerously-skip-permissions\""' >> "$profile"
                fi
            done
            echo -e "  ${GREEN}✓ Added: claude-dev-ss${NC}"
            ((added_count++))
        else
            echo -e "  ${YELLOW}○ Already exists: claude-dev-ss${NC}"
            ((skipped_count++))
        fi

        if add_alias_to_profiles "codex-ss" "specstory run codex"; then
            echo -e "  ${GREEN}✓ Added: codex-ss${NC}"
            ((added_count++))
        else
            echo -e "  ${YELLOW}○ Already exists: codex-ss${NC}"
            ((skipped_count++))
        fi

        if add_alias_to_profiles "gemini-ss" "specstory run gemini"; then
            echo -e "  ${GREEN}✓ Added: gemini-ss${NC}"
            ((added_count++))
        else
            echo -e "  ${YELLOW}○ Already exists: gemini-ss${NC}"
            ((skipped_count++))
        fi
        echo ""
    fi

    # Auto-Claude aliases
    if check_system_installed "auto-claude"; then
        echo -e "${CYAN}Auto-Claude:${NC}"
        if add_alias_to_profiles "ac" "auto-claude"; then
            echo -e "  ${GREEN}✓ Added: ac${NC}"
            ((added_count++))
        else
            echo -e "  ${YELLOW}○ Already exists: ac${NC}"
            ((skipped_count++))
        fi

        if add_alias_to_profiles "ac-spec" "auto-claude-spec"; then
            echo -e "  ${GREEN}✓ Added: ac-spec${NC}"
            ((added_count++))
        else
            echo -e "  ${YELLOW}○ Already exists: ac-spec${NC}"
            ((skipped_count++))
        fi

        if add_alias_to_profiles "ac-list" "auto-claude --list"; then
            echo -e "  ${GREEN}✓ Added: ac-list${NC}"
            ((added_count++))
        else
            echo -e "  ${YELLOW}○ Already exists: ac-list${NC}"
            ((skipped_count++))
        fi
        echo ""
    fi

    # Linear Agent Harness alias
    if check_system_installed "linear-agent-harness"; then
        echo -e "${CYAN}Linear Agent Harness:${NC}"
        local HARNESS_DIR="${HOME}/.local/share/linear-agent-harness"
        local HARNESS_CMD="${HARNESS_DIR}/venv/bin/python ${HARNESS_DIR}/autonomous_agent_demo.py"

        if ! grep -q 'alias linear-agent=' ~/.zshrc 2>/dev/null && ! grep -q 'alias linear-agent=' ~/.bashrc 2>/dev/null; then
            for profile in ~/.zshrc ~/.bashrc; do
                if [ -f "$profile" ]; then
                    echo "alias linear-agent='${HARNESS_CMD}'" >> "$profile"
                fi
            done
            echo -e "  ${GREEN}✓ Added: linear-agent${NC}"
            ((added_count++))
        else
            echo -e "  ${YELLOW}○ Already exists: linear-agent${NC}"
            ((skipped_count++))
        fi
        echo ""
    fi

    # Vibe Kanban alias
    if check_system_installed "vibe-kanban"; then
        echo -e "${CYAN}Vibe Kanban:${NC}"
        if add_alias_to_profiles "vk" "vibe-kanban"; then
            echo -e "  ${GREEN}✓ Added: vk${NC}"
            ((added_count++))
        else
            echo -e "  ${YELLOW}○ Already exists: vk${NC}"
            ((skipped_count++))
        fi
        echo ""
    fi

    # Summary
    echo -e "${BLUE}─────────────────────────────────────────────────────────────${NC}"
    if [ $added_count -gt 0 ]; then
        echo -e "${GREEN}Added: ${added_count} alias(es)${NC}"
        echo -e "${YELLOW}Note: Run 'source ~/.bashrc' or 'source ~/.zshrc' to activate${NC}"
    fi
    if [ $skipped_count -gt 0 ]; then
        echo -e "${CYAN}Already configured: ${skipped_count} alias(es)${NC}"
    fi
    if [ $added_count -eq 0 ] && [ $skipped_count -eq 0 ]; then
        echo -e "${YELLOW}No installed services with aliases found.${NC}"
        echo -e "Install services first, then run this option to add aliases."
    fi
}

# Main menu loop
main() {
    init_manifest

    while true; do
        show_header
        list_features

        # Build feature array in the same grouped order as list_features
        declare -a features
        declare -A categories
        categories=(
            ["Core Tools"]="1password-cli docker-outside"
            ["AI CLI Tools"]="claude-code codex-cli gemini-cli z-ai agent-browser specstory ccusage"
            ["MCP Servers"]="mcp-archon mcp-context7 mcp-linear mcp-openmemory mcp-perplexity mcp-puppeteer"
            ["Orchestration"]="bmad-v6 codemachine speckit linear-agent-harness vibe-kanban auto-claude agent-os"
        )

        local index=1
        for category in "Core Tools" "AI CLI Tools" "MCP Servers" "Orchestration"; do
            for feature_name in ${categories[$category]}; do
                local feature_file="$FEATURES_DIR/${feature_name}.sh"
                if [ -f "$feature_file" ]; then
                    features[$index]=$feature_file
                    ((index++))
                fi
            done
        done

        local install_all_option=$index

        read -p "Select a feature to install (0-${install_all_option}, A, R): " choice

        if [ "$choice" = "0" ]; then
            echo -e "${GREEN}Goodbye!${NC}"
            break
        elif [ "$choice" = "A" ] || [ "$choice" = "a" ]; then
            echo ""
            install_aliases
            echo ""
            read -p "Press Enter to continue..."
        elif [ "$choice" = "R" ] || [ "$choice" = "r" ]; then
            echo ""
            rebuild_features_summary
            echo ""
            read -p "Press Enter to continue..."
        elif [ "$choice" = "$install_all_option" ]; then
            echo ""
            install_all
            echo ""
            read -p "Press Enter to continue..."
        elif [ "$choice" -ge 1 ] 2>/dev/null && [ "$choice" -lt "$install_all_option" ]; then
            echo ""
            install_feature "${features[$choice]}"
            echo ""
            read -p "Press Enter to continue..."
        else
            echo -e "${RED}Invalid selection${NC}"
            sleep 1
        fi
    done
}

main
