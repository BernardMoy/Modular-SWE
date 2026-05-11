FROM python:3.12.3-slim

# Install required packages 
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl build-essential && rm -rf /var/lib/apt/lists/*

# Install uv (then uv pip install... + run tests) 
RUN pip install uv 

# Copy requirements + install requirements from system (not venv) 
COPY requirements.txt /tmp/requirements.txt
RUN uv pip install --system -r /tmp/requirements.txt

# Install nodejs 
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g @anthropic-ai/claude-code