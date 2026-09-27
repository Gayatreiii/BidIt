#!/bin/bash
set -e

echo "=== BidIt Railway Startup ==="

# Ensure unzip is available (needed by Reflex to install bun)
if ! command -v unzip &> /dev/null; then
    echo "Installing unzip..."
    apt-get update -qq && apt-get install -y -qq unzip
fi

# Add bun to PATH if installed
if [ -f "$HOME/.bun/bin/bun" ]; then
    export PATH="$HOME/.bun/bin:$PATH"
    echo "Bun found at $HOME/.bun/bin/bun"
elif [ -f "/root/.bun/bin/bun" ]; then
    export PATH="/root/.bun/bin:$PATH"
    echo "Bun found at /root/.bun/bin/bun"
else
    echo "Bun not found, installing..."
    curl -fsSL https://bun.sh/install | bash
    export PATH="$HOME/.bun/bin:$PATH"
fi

echo "unzip: $(which unzip)"
echo "bun: $(which bun)"
echo "PORT: ${PORT:-8080}"

exec reflex run --env prod --backend-port "${PORT:-8080}" --backend-host 0.0.0.0
