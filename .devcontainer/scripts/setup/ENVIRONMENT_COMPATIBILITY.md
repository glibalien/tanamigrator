# Environment Compatibility Guide

This setup system is designed to work across multiple development environments. Features are designed to detect their environment and provide clear feedback when they're not compatible.

## Supported Environments

### ✅ Local DevContainers
**Status**: Fully Supported

All features work when running devcontainers locally with Docker Desktop or similar.

**Requirements**:
- Docker Desktop or Docker CLI
- VS Code with Dev Containers extension

### ✅ DevPods
**Status**: Fully Supported

All features work in DevPods environments.

**Requirements**:
- DevPods installed
- Docker socket access (for docker-outside feature)

### ⚠️ GitHub Codespaces
**Status**: Partially Supported

Most features work, but some Docker-related features are limited.

**Limitations**:
- ❌ docker-outside-of-docker: Not available (no Docker socket access)
- ✅ 1Password CLI: Works
- ✅ Codex CLI: Works
- ✅ Gemini CLI: Works

**Alternatives for Docker**:
- Use GitHub Actions for Docker builds
- Use pre-built images

### ✅ Gitpod
**Status**: Fully Supported (with configuration)

Most features work in Gitpod.

## Feature Compatibility Matrix

| Feature | Local DevContainer | DevPods | Codespaces | Gitpod |
|---------|-------------------|---------|------------|--------|
| 1Password CLI | ✅ | ✅ | ✅ | ✅ |
| Docker-outside | ✅ | ✅ | ❌ | ⚠️ |
| Codex CLI | ✅ | ✅ | ✅ | ✅ |
| Gemini CLI | ✅ | ✅ | ✅ | ✅ |

**Legend**:
- ✅ Fully supported
- ⚠️ Supported with configuration
- ❌ Not supported

## Environment Detection

The setup menu automatically detects your environment and displays it in the header:

```
╔════════════════════════════════════════════════════════════╗
║        DevContainer Feature Installation Menu             ║
╠════════════════════════════════════════════════════════════╣
║  Environment: GitHub Codespaces                           ║
╚════════════════════════════════════════════════════════════╝
```

Features that aren't compatible with your environment will:
1. Display a clear error message
2. Explain why it's not compatible
3. Suggest alternatives when available

## Feature-Specific Notes

### Docker-outside-of-Docker

**Works in**:
- Local DevContainers (with socket mount)
- DevPods (with socket mount)

**Doesn't work in**:
- GitHub Codespaces (no Docker socket access)

**Requirements**:
Your `devcontainer.json` must include:
```json
{
  "mounts": [
    "source=/var/run/docker.sock,target=/var/run/docker.sock,type=bind"
  ]
}
```

**Codespaces Alternative**:
If you need Docker in Codespaces, consider:
1. Using GitHub Actions for builds
2. Pushing images to a registry
3. Using pre-built images

### 1Password CLI

**Works in**: All environments

**Post-install**:
- Sign in: `eval $(op signin)`
- Or set service account: `export OP_SERVICE_ACCOUNT_TOKEN=<token>`

### AI CLI Tools (Codex, Gemini)

**Works in**: All environments

**Configuration**:
- Requires API keys set as environment variables
- Config persists in mounted volumes

## Adding Docker Socket Mount

If you want to use docker-outside-of-docker, add this to your `devcontainer.json`:

```json
{
  "name": "My Project",
  "build": {
    "dockerfile": "Dockerfile"
  },
  "mounts": [
    "source=/var/run/docker.sock,target=/var/run/docker.sock,type=bind"
  ],
  "runArgs": [],
  ...
}
```

Then rebuild your devcontainer:
1. Press `F1` or `Ctrl+Shift+P`
2. Type "Dev Containers: Rebuild Container"
3. Select and confirm

## Environment Variables

The setup system uses these environment variables for detection:
- `CODESPACES`: Set by GitHub Codespaces
- `GITPOD_WORKSPACE_ID`: Set by Gitpod
- `DEVCONTAINER`: Set to `true` in all environments

## Troubleshooting

### "Feature not compatible with environment"

This means the feature has detected it can't work in your current environment. Read the error message for:
- Why it's not compatible
- What's missing
- Suggested alternatives

### Docker socket permission errors

If docker-outside fails with permission errors:
1. Ensure the Docker socket is mounted
2. Rebuild the devcontainer
3. Open a new terminal
4. Try running: `newgrp docker`

### Feature installs but doesn't work

Some features require additional configuration:
- **1Password**: Needs authentication
- **Codex/Gemini**: Need API keys
- **Docker**: Needs socket mount

Check the feature's post-install instructions.

## Contributing New Features

When adding new features, please:
1. Detect environment compatibility
2. Provide clear error messages for unsupported environments
3. Suggest alternatives when possible
4. Update this compatibility matrix
5. Test in multiple environments if possible

See `features/docker-outside.sh` for an example of environment detection.
