FROM python:3.11-slim

# Install system dependencies: unzip/curl (for bun), nginx (reverse proxy), supervisor (process manager), gettext-base (for envsubst)
RUN apt-get update && apt-get install -y --no-install-recommends \
    unzip \
    curl \
    nginx \
    supervisor \
    gettext-base \
    && rm -rf /var/lib/apt/lists/*

# Install bun (JavaScript runtime for Reflex frontend)
RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="/root/.bun/bin:$PATH"

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

# Initialize Reflex project structure
RUN reflex init

# Pre-build the frontend as static files (so nginx can serve them at runtime without rebuild delay)
# RAILWAY_PUBLIC_DOMAIN is available at build time, configuring WebSocket URL in the compiled JS
RUN reflex export --frontend-only --no-zip || true

# Make deploy scripts executable
RUN chmod +x /app/deploy/start.sh

EXPOSE 8080

# Launch: start.sh sets up nginx config with $PORT then runs supervisord
CMD ["/bin/bash", "/app/deploy/start.sh"]
