FROM node:20

ARG TZ
ENV TZ="$TZ"

# Configure system timezone (requires TZ build arg from devcontainer.json)
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ARG CLAUDE_CODE_VERSION=latest
ARG CODEX_VERSION=latest

# Install basic development tools and iptables/ipset
RUN apt-get update && apt-get install -y --no-install-recommends \
  less \
  git \
  procps \
  sudo \
  fzf \
  zsh \
  man-db \
  unzip \
  gnupg2 \
  gh \
  iptables \
  ipset \
  iproute2 \
  dnsutils \
  aggregate \
  jq \
  nano \
  vim \
  locales \
  curl \
  wget \
  ca-certificates \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Configure locales
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
  locale-gen
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

# Ensure default node user has access to /usr/local/share
RUN mkdir -p /usr/local/share/npm-global && \
  chown -R node:node /usr/local/share

ARG USERNAME=node

# Configure passwordless sudo for node user (required for feature installations)
RUN echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} && \
  chmod 0440 /etc/sudoers.d/${USERNAME}

# Persist bash history
RUN SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
  && mkdir /commandhistory \
  && touch /commandhistory/.bash_history \
  && chown -R $USERNAME /commandhistory

# Set environment variable to help with orientation
ENV DEVCONTAINER=true

# Install git-delta before switching user
ARG GIT_DELTA_VERSION=0.18.2
RUN ARCH=$(dpkg --print-architecture) && \
  wget "https://github.com/dandavison/delta/releases/download/${GIT_DELTA_VERSION}/git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" && \
  dpkg -i "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" && \
  rm "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb"

# Create workspace and config directories with proper permissions
RUN mkdir -p /workspace \
  /home/node/.claude \
  /home/node/.codex \
  /home/node/.gemini \
  /home/node/.glm \
  /home/node/.config/gh \
  /home/node/.config/gcloud \
  /home/node/.config/claude-code \
  /home/node/.aws \
  /home/node/.docker \
  /home/node/.ssh \
  /home/node/.cache \
  /home/node/.npm && \
  chown -R node:node /workspace /home/node && \
  chmod 700 /home/node/.ssh && \
  chmod -R 755 /workspace

WORKDIR /workspace

# Switch to non-root user
USER node

# Set up npm global directory
ENV NPM_CONFIG_PREFIX=/usr/local/share/npm-global
ENV PATH=$PATH:/usr/local/share/npm-global/bin

# Set the default shell to zsh
ENV SHELL=/bin/zsh

# Set the default editor
ENV EDITOR=nano
ENV VISUAL=nano

# Install zsh-in-docker
ARG ZSH_IN_DOCKER_VERSION=1.2.0
RUN sh -c "$(wget -O- https://github.com/deluan/zsh-in-docker/releases/download/v${ZSH_IN_DOCKER_VERSION}/zsh-in-docker.sh)" -- \
  -p git \
  -p fzf \
  -a "source /usr/share/doc/fzf/examples/key-bindings.zsh" \
  -a "source /usr/share/doc/fzf/examples/completion.zsh" \
  -a "export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
  -x

# Install ccusage for Claude Code usage tracking
RUN sudo npm install -g ccusage || true

# Add CLI aliases for convenience (only if commands exist)
RUN echo '# CLI Aliases' >> /home/node/.zshrc && \
  echo 'command -v claude >/dev/null 2>&1 && alias claude-dev="claude --dangerously-skip-permissions"' >> /home/node/.zshrc && \
  echo 'command -v codex >/dev/null 2>&1 && alias codex-dev="codex --dangerously-bypass-approvals-and-sandbox"' >> /home/node/.zshrc && \
  echo 'command -v gemini >/dev/null 2>&1 && alias gemini-dev="gemini --yolo"' >> /home/node/.zshrc
