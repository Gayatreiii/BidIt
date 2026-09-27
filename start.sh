#!/bin/bash
# BidIt Railway startup script
# This ensures unzip and bun are available at runtime before starting Reflex

set -e

echo "=== BidIt Railway Startup ==="

# Install unzip at runtime (Railway's runtime container doesn't have it by default)
if ! command -v unzip &> /dev/null; then
    echo "[startup] Installing unzip..."
    apt-get update -qq && apt-get install -y -qq unzip curl
    echo "[startup] unzip installed."
else
    echo "[startup] unzip already available."
fi

# Add bun to PATH wherever it may have been installed
if [ -f "$HOME/.bun/bin/bun" ]; then
    export BUN_INSTALL="$HOME/.bun"
elif [ -f "/root/.bun/bin/bun" ]; then
    export BUN_INSTALL="/root/.bun"
fi

if [ -n "$BUN_INSTALL" ]; then
    export PATH="$BUN_INSTALL/bin:$PATH"
    echo "[startup] Bun found at $BUN_INSTALL/bin/bun"
else
    echo "[startup] Bun not found, installing via curl..."
    curl -fsSL https://bun.sh/install | bash
    export BUN_INSTALL="$HOME/.bun"
    export PATH="$BUN_INSTALL/bin:$PATH"
    echo "[startup] Bun installed."
fi

echo "[startup] unzip: $(which unzip)"
echo "[startup] bun: $(which bun 2>/dev/null || echo 'not in PATH')"
echo "[startup] PORT: ${PORT:-8080}"
echo "[startup] Starting Reflex..."

exec reflex run --env prod --backend-port "${PORT:-8080}" --backend-host 0.0.0.0
