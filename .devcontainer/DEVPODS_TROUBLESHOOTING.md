# DevPods Troubleshooting Guide

## Common Error: "error parsing workspace info: rerun as root"

This error occurs when DevPods cannot properly parse or access the workspace configuration. It's a DevPods agent-level issue, not a Docker issue.

## Testing Order (Start Simple)

### 1. Test with Minimal Configuration
Try the simplest possible configuration first:
```bash
# Use the minimal config
cp .devcontainer/devcontainer.minimal.json .devcontainer/devcontainer.json
```

This uses a Microsoft-provided base image with minimal customization.

### 2. Test with Root-level devcontainer.json
Some DevPods versions look for devcontainer.json at the repository root:
```bash
# Copy to root (already done)
cp devcontainer.json .
```

### 3. Test with DevPods Fix Configuration
If minimal doesn't work, try the DevPods-specific fix:
```bash
cp .devcontainer/devcontainer.devpods-fix.json .devcontainer/devcontainer.json
cp .devcontainer/Dockerfile.devpods-fix .devcontainer/Dockerfile
```

## DevPods-Specific Settings to Check

### In DevPods UI/CLI:
1. **Provider Settings**:
   - Ensure the DigitalOcean droplet has sufficient resources (2GB+ RAM)
   - Check that Docker is pre-installed on the droplet

2. **Workspace Settings**:
   - Try setting "Source" to the HTTPS git URL instead of SSH
   - Disable "Use BuildKit" if enabled
   - Set "DevContainer Path" explicitly to `.devcontainer/devcontainer.json`

3. **SSH Settings**:
   - Ensure SSH key is properly configured
   - Try using password authentication as a test

## Manual Testing on DigitalOcean

If DevPods continues to fail, test manually on a DigitalOcean droplet:

```bash
# SSH into your droplet
ssh root@your-droplet-ip

# Clone the repository
git clone https://github.com/Steve-Klingele/tana_clipper.git
cd tana_clipper
git checkout feature/multi-platform-devcontainer

# Install DevPods agent manually
curl -L https://github.com/loft-sh/devpod/releases/latest/download/devpod-linux-amd64 -o devpod
chmod +x devpod
sudo mv devpod /usr/local/bin/

# Try to start the workspace manually
devpod up . --devcontainer-path .devcontainer/devcontainer.minimal.json
```

## Alternative: Use Docker Directly

If DevPods continues to fail, bypass it and use Docker directly:

```bash
# On the DigitalOcean droplet
docker build -f .devcontainer/Dockerfile.devpods-fix -t tana-clipper .
docker run -it -v $(pwd):/workspace tana-clipper
```

## Configuration Hierarchy

1. **devcontainer.minimal.json** - Simplest, uses pre-built image
2. **devcontainer.devpods-fix.json** - Custom build with all permission fixes
3. **devcontainer.universal.json** - Cross-platform compatible
4. **devcontainer.devpods.json** - Original DevPods attempt

## Known DevPods Issues

1. **Workspace Parsing**: DevPods sometimes fails to parse complex devcontainer.json files
2. **Permission Escalation**: DevPods agent may need root to set up the environment
3. **Path Resolution**: DevPods may look in different locations for devcontainer.json
4. **BuildKit Compatibility**: Disable BuildKit if builds fail
5. **Volume Mounts**: Complex mount configurations can cause issues

## Debugging Steps

1. **Check DevPods Logs**:
   ```bash
   devpod logs <workspace-name>
   ```

2. **Check Docker on Droplet**:
   ```bash
   docker version
   docker info
   ```

3. **Check Disk Space**:
   ```bash
   df -h
   ```

4. **Check Memory**:
   ```bash
   free -m
   ```

## If All Else Fails

Use GitHub Codespaces or VS Code Remote Containers locally. The original configuration works perfectly in those environments.

## Contact Support

- DevPods Issues: https://github.com/loft-sh/devpod/issues
- This Project: https://github.com/Steve-Klingele/tana_clipper/issues