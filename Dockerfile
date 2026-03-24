# Use Ubuntu 22.04 LTS for rock-solid apt-get mirrors (avoids Debian Trixie timeouts)
# It natively supports ARM64 architecture (Apple Silicon) natively.
FROM ubuntu:22.04

USER root

# Avoid tzdata interactive prompts hanging the build
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install baseline dependencies
# Ubuntu's mirrors are vastly more stable than Debian Testing
RUN apt-get update -y && apt-get install -y --fix-missing \
    openjdk-17-jdk \
    maven \
    nodejs \
    npm \
    curl \
    docker.io \
    build-essential \
    python3-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install cross-platform Miniconda directly from Anaconda servers
RUN curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-$(uname -m).sh \
    && bash Miniconda3-latest-Linux-$(uname -m).sh -b -p /opt/conda \
    && rm Miniconda3-latest-Linux-$(uname -m).sh

ENV PATH="/opt/conda/bin:$PATH"

WORKDIR /app
COPY environment.yml /tmp/environment.yml

# Strip OS-specific build hashes from conda packages to ensure cross-platform compatibility
RUN sed -i '/==/! s/^\([^=]*=[^=]*\)=.*/\1/' /tmp/environment.yml \
    && conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main || true \
    && conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r || true \
    && conda env create -f /tmp/environment.yml

# We setup bash to activate the env_name environment automatically for all subsequent commands
RUN echo "conda activate env_name" >> ~/.bashrc
SHELL ["/bin/bash", "--login", "-c"]

# Note: In docker-compose we will volume mount the workspace over /app anyway, 
# but we COPY the codebase into the image in case it's run stand-alone.
COPY . /app

# The default command uses `conda run` to ensure it executes in the right environment.
CMD ["conda", "run", "--no-capture-output", "-n", "env_name", "streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
