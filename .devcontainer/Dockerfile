FROM mcr.microsoft.com/devcontainers/python:3.11

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Python virtual env with all project deps
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python requirements
COPY requirements-dev.txt /tmp/requirements-dev.txt
RUN pip install --no-cache-dir -r /tmp/requirements-dev.txt

# Install AWS CDK globally
RUN npm install -g aws-cdk@latest
