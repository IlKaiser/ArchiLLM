FROM continuumio/miniconda3:latest

# Install system dependencies required for OpenHands agents and compilation
# - Java 17 + Maven for Spring Boot
# - Node.js + npm for React/Vite
# - Docker.io so OpenHands has access to Docker CLI if needed for sandboxing
RUN apt-get update && apt-get install -y --fix-missing \
    default-jdk \
    maven \
    nodejs \
    npm \
    curl \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the environment requirements and setup the conda environment first
# This uses Docker layer caching smartly
COPY environment.yml /tmp/environment.yml
RUN sed -i '/==/! s/^\([^=]*=[^=]*\)=.*/\1/' /tmp/environment.yml \
    && conda env create -f /tmp/environment.yml

# We setup bash to activate the env_name environment automatically for all subsequent commands
RUN echo "conda activate env_name" >> ~/.bashrc
SHELL ["/bin/bash", "--login", "-c"]

# Note: In docker-compose we will volume mount the workspace over /app anyway, 
# but we COPY the codebase into the image in case it's run stand-alone.
COPY . /app

# The default command uses `conda run` to ensure it executes in the right environment.
CMD ["conda", "run", "--no-capture-output", "-n", "env_name", "streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
