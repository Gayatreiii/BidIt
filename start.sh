#!/bin/bash
# BidIt Railway startup script
set -e

echo "=== BidIt Railway Startup ==="
echo "[startup] Date: $(date)"
echo "[startup] User: $(whoami)"
echo "[startup] PWD: $(pwd)"
echo "[startup] PORT: ${PORT:-8080}"
echo "[startup] Python: $(python3 --version 2>&1)"
echo "[startup] Memory: $(free -h 2>/dev/null || echo 'N/A')"

# Install unzip if missing (Railway runtime may not have it)
if ! command -v unzip &> /dev/null; then
    echo "[startup] Installing unzip..."
    DEBIAN_FRONTEND=noninteractive apt-get update -qq && apt-get install -y -qq unzip curl
    echo "[startup] unzip installed."
else
    echo "[startup] unzip available: $(which unzip)"
fi

# Locate or install bun
if [ -f "$HOME/.bun/bin/bun" ]; then
    export BUN_INSTALL="$HOME/.bun"
elif [ -f "/root/.bun/bin/bun" ]; then
    export BUN_INSTALL="/root/.bun"
fi

if [ -n "$BUN_INSTALL" ]; then
    export PATH="$BUN_INSTALL/bin:$PATH"
    echo "[startup] Bun found: $BUN_INSTALL/bin/bun ($(bun --version))"
else
    echo "[startup] Bun not found, installing..."
    curl -fsSL https://bun.sh/install | bash
    export BUN_INSTALL="$HOME/.bun"
    export PATH="$BUN_INSTALL/bin:$PATH"
    echo "[startup] Bun installed: $(bun --version)"
fi

echo "[startup] Environment ready. Starting Reflex..."
echo "[startup] Command: reflex run --env prod --backend-port ${PORT:-8080} --backend-host 0.0.0.0"

exec reflex run --env prod --backend-port "${PORT:-8080}" --backend-host 0.0.0.0
