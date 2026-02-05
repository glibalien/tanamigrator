#!/bin/bash
# Description: Docker CLI configured to use host Docker daemon (Docker-outside-of-Docker)
set -e

check_installed() {
    if command -v docker &> /dev/null; then
        # Check if we can actually connect to Docker
        if docker ps &> /dev/null; then
            return 0
        fi
    fi
    return 1
}

install() {
    # Check if already installed
    if check_installed; then
        echo ""
        echo -e "\033[0;33m⚠ Docker CLI is already installed and connected\033[0m"
        echo "  $(docker --version)"
        echo ""
        echo "Options:"
        echo "  1) Reinstall Docker CLI"
        echo "  2) Skip (keep current installation)"
        echo ""
        read -p "Enter choice (1-2): " choice

        case $choice in
            1)
                echo ""
                echo "Reinstalling Docker CLI..."
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

    echo "Installing Docker CLI (Docker-outside-of-Docker)..."
    echo ""

    # Check environment compatibility
    if [ -n "$CODESPACES" ]; then
        echo -e "\033[0;31mNOT COMPATIBLE:\033[0m This feature doesn't work in GitHub Codespaces"
        echo "  Codespaces doesn't provide access to the host Docker daemon."
        echo ""
        echo "  Alternatives:"
        echo "  - Use GitHub Actions for Docker builds"
        echo "  - Use docker-in-docker feature (if available)"
        return 1
    fi

    # Check if Docker socket is mounted
    if [ ! -S /var/run/docker.sock ]; then
        echo -e "\033[0;31mERROR:\033[0m Docker socket not found at /var/run/docker.sock"
        echo ""
        echo "  This feature requires the Docker socket to be mounted."
        echo ""
        echo "  ╭─────────────────────────────────────────────────────────────╮"
        echo "  │ To enable Docker socket mounting:                          │"
        echo "  ╰─────────────────────────────────────────────────────────────╯"
        echo ""
        echo "  1. Open: .devcontainer/devcontainer.json"
        echo ""
        echo "  2. Find the \"mounts\" section (around line 43-58)"
        echo ""
        echo "  3. Uncomment this line (remove the // at the start):"
        echo "     // \"source=/var/run/docker.sock,target=/var/run/docker.sock,type=bind\""
        echo ""
        echo "  4. Add a comma to the line above it if needed"
        echo ""
        echo "  5. Rebuild your devcontainer:"
        echo "     - Press F1 or Ctrl+Shift+P"
        echo "     - Type: \"Dev Containers: Rebuild Container\""
        echo "     - Press Enter"
        echo ""
        echo "  6. Run this setup menu again"
        echo ""
        echo "  Note: This line is already in your devcontainer.json,"
        echo "        just commented out for safety."
        echo ""
        return 1
    fi

    # Install Docker CLI and docker-compose
    echo "Installing Docker CLI..."
    curl -fsSL https://get.docker.com | sudo sh

    # Add current user to docker group
    sudo usermod -aG docker ${USER}

    # Fix permissions on Docker socket
    sudo chown ${USER}:docker /var/run/docker.sock 2>/dev/null || true
    sudo chmod 666 /var/run/docker.sock 2>/dev/null || true

    # Test Docker access
    if docker ps &> /dev/null; then
        echo ""
        echo -e "\033[0;32m✓ Docker CLI configured successfully!\033[0m"
        echo "  Docker version: $(docker --version)"
        echo "  Docker Compose version: $(docker compose version)"
        echo ""
        echo "  You can now use Docker commands to:"
        echo "  - Build images: docker build ."
        echo "  - Run containers: docker run ..."
        echo "  - Use docker-compose: docker compose up"
        echo ""
        echo "  NOTE: If commands fail, try opening a new terminal."
        return 0
    else
        echo ""
        echo -e "\033[0;33mWARNING:\033[0m Docker socket exists but cannot execute commands."
        echo "  Try one of the following:"
        echo "  1. Open a new terminal/shell"
        echo "  2. Run: newgrp docker"
        echo "  3. Restart your devcontainer"
        return 1
    fi
}

install
