# Use a lightweight Python base image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:/root/.cargo/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock README.md ./

# Install dependencies using uv
# Use --no-install-project to bypass building the project itself (which requires full source)
RUN uv sync --frozen --no-install-project

# Copy the rest of the application code
COPY . .

# Final sync to install the project (scripts and package metadata)
RUN uv sync --frozen

# Ensure start.sh is executable
RUN chmod +x start.sh

# Expose the port (Railway will set the PORT environment variable)
EXPOSE 8000

# Run the unified startup script
CMD ["bash", "start.sh"]
