FROM python:3.11-slim

# Install system packages Reflex needs (unzip for bun, curl for bun installer)
RUN apt-get update && apt-get install -y --no-install-recommends \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install bun (JavaScript runtime Reflex uses for frontend)
RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="/root/.bun/bin:$PATH"

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the app source
COPY . .

# Pre-initialize Reflex (downloads bun, sets up .web directory)
RUN reflex init

# Expose the port Railway will assign
EXPOSE 8080

# Start the app
CMD reflex run --env prod --backend-port "${PORT:-8080}" --backend-host 0.0.0.0
