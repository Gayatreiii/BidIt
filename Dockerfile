FROM python:3.12-slim

# Install system dependencies
# NOTE: Changing base to python:3.12-slim forces a full cache bust on Railway's builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    unzip \
    curl \
    nginx \
    supervisor \
    gettext-base \
    && rm -rf /var/lib/apt/lists/*

# Install bun
RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="/root/.bun/bin:$PATH"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN reflex init

# Pre-build frontend at Docker build time (eliminates 90-second startup delay)
RUN reflex export --frontend-only --no-zip 2>&1 || echo "WARNING: export failed, nginx will serve empty dir"

RUN chmod +x /app/deploy/start.sh

EXPOSE 8080

CMD ["/bin/bash", "/app/deploy/start.sh"]
