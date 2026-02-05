#!/bin/bash
# Shared helper functions for feature installers

# Add or update an environment variable in both shell profiles
# Usage: add_env_to_profiles "VAR_NAME" "value" "# Comment for the section"
add_env_to_profiles() {
    local var_name=$1
    local var_value=$2
    local comment=${3:-"# Added by devtemplate installer"}

    for profile in "$HOME/.bashrc" "$HOME/.zshrc"; do
        if [ -f "$profile" ]; then
            if ! grep -q "export ${var_name}=" "$profile" 2>/dev/null; then
                echo "" >> "$profile"
                echo "$comment" >> "$profile"
                echo "export ${var_name}=${var_value}" >> "$profile"
            else
                sed -i "s|export ${var_name}=.*|export ${var_name}=${var_value}|" "$profile"
            fi
        fi
    done

    # Export for current session
    export "${var_name}=${var_value}"
}

# Add a line to both shell profiles if not present
# Usage: add_line_to_profiles "line to add" "grep pattern to check"
add_line_to_profiles() {
    local line=$1
    local pattern=${2:-$1}

    for profile in "$HOME/.bashrc" "$HOME/.zshrc"; do
        if [ -f "$profile" ]; then
            if ! grep -q "$pattern" "$profile" 2>/dev/null; then
                echo "$line" >> "$profile"
            fi
        fi
    done
}

# Add to PATH in both shell profiles
# Usage: add_to_path "/new/path"
add_to_path() {
    local new_path=$1

    for profile in "$HOME/.bashrc" "$HOME/.zshrc"; do
        if [ -f "$profile" ]; then
            if ! grep -q "PATH.*${new_path}" "$profile" 2>/dev/null; then
                echo "" >> "$profile"
                echo "# Added by devtemplate installer" >> "$profile"
                echo "export PATH=\"${new_path}:\$PATH\"" >> "$profile"
            fi
        fi
    done

    # Update current session
    export PATH="${new_path}:$PATH"
}

# ============================================================================
# NPM Install Helpers with sudo fallback
# ============================================================================

# Install npm package globally with sudo fallback to user directory
# Usage: npm_install_global "package-name"
npm_install_global() {
    local package=$1
    if sudo -n true 2>/dev/null; then
        sudo npm install -g "$package"
    else
        echo "Note: sudo not available, installing to user directory..."
        npm config set prefix ~/.local 2>/dev/null || true
        npm install -g "$package"
        add_to_path "$HOME/.local/bin"
    fi
}

# Update npm package globally with sudo fallback
# Usage: npm_update_global "package-name"
npm_update_global() {
    local package=$1
    if sudo -n true 2>/dev/null; then
        sudo npm update -g "$package"
    else
        npm update -g "$package"
    fi
}

# Check if npm package is installed globally
# Usage: npm_check_global "package-name"
npm_check_global() {
    local package=$1
    if sudo -n true 2>/dev/null; then
        sudo npm list -g "$package" &> /dev/null
    else
        npm list -g "$package" &> /dev/null
    fi
}

# ============================================================================
# Installed Features Summary Management
# ============================================================================

FEATURES_SUMMARY_FILE="${FEATURES_SUMMARY_FILE:-.devcontainer/INSTALLED-FEATURES.md}"

# Initialize the installed features summary if it doesn't exist
# Usage: init_features_summary
init_features_summary() {
    local summary_file="$FEATURES_SUMMARY_FILE"

    if [ ! -f "$summary_file" ]; then
        cat > "$summary_file" << 'EOF'
# Installed Features

This document is automatically updated when features are installed or removed via the DevTemplate setup menu.

**Last Updated:** Never

---

## Summary

| Feature | Category | Installed | Status |
|---------|----------|-----------|--------|

---

## Feature Details

<!-- Feature entries are added below this line -->
EOF
    fi
}

# Add a feature to the installed features summary
# Usage: add_feature_to_summary "feature-name" "category" "description" "version" "install_location" "commands" "env_vars" "notes"
add_feature_to_summary() {
    local feature_name=$1
    local category=$2
    local description=$3
    local version=${4:-"N/A"}
    local install_location=${5:-"N/A"}
    local commands=${6:-"N/A"}
    local env_vars=${7:-"None"}
    local notes=${8:-""}

    local summary_file="$FEATURES_SUMMARY_FILE"
    local timestamp=$(date +"%Y-%m-%d %H:%M")
    local date_only=$(date +"%Y-%m-%d")

    # Initialize if needed
    init_features_summary

    # Use Python for reliable file manipulation (avoids sed escaping issues)
    python3 << PYEOF
import re
import sys

feature_name = """${feature_name}"""
category = """${category}"""
description = """${description}"""
version = """${version}"""
install_location = """${install_location}"""
commands = """${commands}"""
env_vars = """${env_vars}"""
notes = """${notes}"""
timestamp = """${timestamp}"""
date_only = """${date_only}"""
summary_file = """${summary_file}"""

with open(summary_file, 'r') as f:
    content = f.read()

# Update last updated timestamp
content = re.sub(r'\*\*Last Updated:\*\*.*', f'**Last Updated:** {timestamp}', content)

# Check if feature exists in table
table_row = f"| {feature_name} |"
if table_row in content:
    # Update existing row - mark as installed
    content = re.sub(
        rf'\| {re.escape(feature_name)} \|[^|]*\|[^|]*\|[^|]*\|',
        f'| {feature_name} | {category} | {date_only} | ✓ Installed |',
        content
    )
else:
    # Add new row after table header
    table_header = "| Feature | Category | Installed | Status |\n|---------|----------|-----------|--------|"
    new_row = f"| {feature_name} | {category} | {date_only} | ✓ Installed |"
    content = content.replace(table_header, f"{table_header}\n{new_row}")

# Check if detailed section exists
detail_header = f"### {feature_name}"
if detail_header not in content:
    # Add new detailed section at the end
    detail_section = f'''

### {feature_name}

**Description:** {description}
**Category:** {category}
**Installed:** {timestamp}
**Version:** {version}

| Property | Value |
|----------|-------|
| Install Location | \`{install_location}\` |
| Commands | \`{commands}\` |
| Environment Variables | {env_vars} |

'''
    if notes:
        detail_section += f"**Notes:** {notes}\n\n"
    detail_section += "---"
    content += detail_section

with open(summary_file, 'w') as f:
    f.write(content)
PYEOF
}

# Remove a feature from the installed features summary
# Usage: remove_feature_from_summary "feature-name"
remove_feature_from_summary() {
    local feature_name=$1
    local summary_file="$FEATURES_SUMMARY_FILE"
    local timestamp=$(date +"%Y-%m-%d %H:%M")

    if [ ! -f "$summary_file" ]; then
        return 0
    fi

    python3 << PYEOF
import re

feature_name = """${feature_name}"""
timestamp = """${timestamp}"""
summary_file = """${summary_file}"""

with open(summary_file, 'r') as f:
    content = f.read()

# Update last updated timestamp
content = re.sub(r'\*\*Last Updated:\*\*.*', f'**Last Updated:** {timestamp}', content)

# Update status in table to "Removed"
content = re.sub(
    rf'\| {re.escape(feature_name)} \|[^|]*\|[^|]*\|[^|]*\|',
    f'| {feature_name} | - | - | ✗ Removed |',
    content
)

with open(summary_file, 'w') as f:
    f.write(content)
PYEOF
}

# Get feature metadata - to be called by individual feature scripts
# This allows features to define their own metadata
# Usage: get_feature_metadata "feature-name"
# Returns: Sets global variables FEATURE_* with metadata
declare_feature_metadata() {
    export FEATURE_NAME=$1
    export FEATURE_CATEGORY=$2
    export FEATURE_DESCRIPTION=$3
    export FEATURE_VERSION=$4
    export FEATURE_LOCATION=$5
    export FEATURE_COMMANDS=$6
    export FEATURE_ENV_VARS=$7
    export FEATURE_NOTES=$8
}

# Rebuild the installed features summary by scanning for installed features
# This is called from menu.sh which has the FEATURE_META and check functions
# Usage: rebuild_features_summary (called from menu.sh context)
rebuild_features_summary() {
    echo "Scanning for installed features..."
    init_features_summary

    # This function expects to be called from menu.sh context where
    # FEATURE_META and check_system_installed are defined
    local count=0

    for feature_name in "${!FEATURE_META[@]}"; do
        if check_system_installed "$feature_name" 2>/dev/null; then
            IFS='|' read -r category description location commands env_vars <<< "${FEATURE_META[$feature_name]}"
            local version=$(get_feature_version "$feature_name" 2>/dev/null || echo "installed")
            add_feature_to_summary "$feature_name" "$category" "$description" "$version" "$location" "$commands" "$env_vars"
            echo "  ✓ Found: $feature_name"
            ((count++))
        fi
    done

    echo ""
    echo "Summary updated with $count installed feature(s)."
    echo "See: .devcontainer/INSTALLED-FEATURES.md"
}
