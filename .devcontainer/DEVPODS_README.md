# Multi-Platform Devcontainer Configuration for Tana Clipper

This directory contains multiple devcontainer configurations optimized for different platforms including GitHub Codespaces, DevPods, VS Code, and other container-based development environments.

## Files

### Configuration Files
- `Dockerfile` - Standard Dockerfile (works across all platforms)
- `devcontainer.json` - Standard devcontainer configuration (works everywhere)
- `Dockerfile.devpods` - DevPods-optimized Dockerfile (for specific DevPods features)
- `devcontainer.devpods.json` - DevPods-specific configuration
- `devcontainer.minimal.json` - Minimal configuration for basic testing

## Key Differences in DevPods Configuration

### Permission Handling
- Added `NOPASSWD` sudoers entry for the node user to avoid permission issues
- Moved git-delta installation before USER switch to avoid sudo issues
- Added `|| true` to npm install commands to handle potential failures gracefully
- Added explicit permission fixes in postCreateCommand

### Network Capabilities
- Removed `--cap-add=NET_ADMIN` and `--cap-add=NET_RAW` flags that can cause issues on some providers
- These are typically not needed unless you're doing low-level network operations

### Volume Mounts
- Simplified volume mounts to only essential ones to avoid permission conflicts
- DevPods handles workspace mounting differently than Codespaces

### Environment Variables
- Added `DEVPODS=true` environment variable for detection
- Maintained existing environment setup for consistency

## Standard Configuration

The main `Dockerfile` and `devcontainer.json` files now work across all platforms:

### Features
- **Cross-platform compatibility**: Works in Codespaces, DevPods, VS Code, and more
- **Graceful fallbacks**: NPM installs won't fail if packages don't exist
- **Smart permission handling**: Proper ownership and sudo configuration
- **Conditional features**: Only enables features if they're available

### When to Use Standard Config
- Default choice for most environments
- Works in GitHub Codespaces, VS Code, and most other platforms
- Only use DevPods-specific config if you need special DevPods features

## Platform-Specific Usage

### GitHub Codespaces
The standard `Dockerfile` and `devcontainer.json` work great in Codespaces. No changes needed.

### DevPods with DigitalOcean (or other cloud providers)

#### Option 1: Use Standard Configuration (Recommended)
The main configuration files now work with DevPods! No changes needed.

#### Option 2: Use DevPods-specific Configuration
Only if you need special DevPods features:
1. In DevPods UI, specify the config path: `.devcontainer/devcontainer.devpods.json`

#### Option 3: Minimal Configuration for Testing
If you encounter any issues, try the minimal config:
1. In DevPods UI, specify: `.devcontainer/devcontainer.minimal.json`

### VS Code Remote Containers (Local Development)
The standard configuration works perfectly.

### Other Platforms (GitPod, Coder, etc.)
The standard configuration should work across all platforms.

## Troubleshooting

### Permission Errors
If you still encounter permission errors:
1. The postCreateCommand includes `sudo chown -R node:node /workspace` to fix ownership
2. Git safe directory is configured to avoid repository access issues

### NPM Install Failures
The npm global installs have `|| true` appended to prevent build failures if packages don't exist yet. These packages may need to be installed manually after container creation.

### Network Issues
If you need network admin capabilities for specific operations:
1. You can add them back to `runArgs` in devcontainer.json
2. Or run specific commands with sudo inside the container

## Testing the Configurations

### Test Universal Configuration
```bash
docker build -f .devcontainer/Dockerfile.universal -t tana-clipper-universal .
docker run -it --rm -v $(pwd):/workspace tana-clipper-universal
```

### Test DevPods Configuration
```bash
docker build -f .devcontainer/Dockerfile.devpods -t tana-clipper-devpods .
docker run -it --rm -v $(pwd):/workspace tana-clipper-devpods
```

### Test Original Configuration
```bash
docker build -f .devcontainer/Dockerfile -t tana-clipper .
docker run -it --rm -v $(pwd):/workspace tana-clipper
```

## Comparison Table

| Platform | Recommended Config | Why |
|----------|-------------------|-----|
| GitHub Codespaces | Standard | Works perfectly |
| DevPods + DigitalOcean | Standard | Now works with all fixes |
| VS Code Local | Standard | Works perfectly |
| GitPod | Standard | Works across platforms |
| Other Platforms | Standard | Universal compatibility |

## Quick Decision Guide

1. **Default choice** → Use standard config (Dockerfile + devcontainer.json)
2. **DevPods with special features** → Use devcontainer.devpods.json
3. **Having any issues** → Try devcontainer.minimal.json

## Known Limitations

1. Some AI CLI tools (Claude, Codex, Gemini) may not exist as public npm packages
2. MCP Chrome DevTools server requires Chrome/Chromium to be useful
3. Network admin capabilities are disabled by default for security