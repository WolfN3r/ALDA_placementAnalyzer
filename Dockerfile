# Base image with n8n and Python (Debian)
FROM naskio/n8n-python:latest-debian

# Fix deprecated Debian Buster repositories
RUN sed -i 's|http://deb.debian.org/debian|http://archive.debian.org/debian|g' /etc/apt/sources.list && \
    sed -i 's|http://security.debian.org/debian-security|http://archive.debian.org/debian-security|g' /etc/apt/sources.list && \
    apt-get update && apt-get install -y \
    build-essential \
    curl \
    zlib1g-dev \
    libssl-dev \
    libreadline-dev \
    libbz2-dev \
    libsqlite3-dev && \
    rm -rf /var/lib/apt/lists/*

# Pyenv setup
ENV PYENV_ROOT="/root/.pyenv"
ENV PATH="$PYENV_ROOT/bin:$PATH"
RUN curl https://pyenv.run | bash

# Default Python version (can override with build ARG)
ARG PYTHON_VERSION=3.12.3
RUN pyenv install $PYTHON_VERSION && pyenv global $PYTHON_VERSION

# Working directory
WORKDIR /home/node

# Copy and install Python requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Global install of Python node for n8n
RUN npm install -g n8n-nodes-python

# Run n8n as root
USER root
ENTRYPOINT ["n8n"]
CMD ["start"]