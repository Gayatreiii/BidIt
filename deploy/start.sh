#!/bin/bash
set -e

PORT=${PORT:-8080}
export PORT

echo "[BidIt] Starting production server on port $PORT"
echo "[BidIt] Setting up nginx config..."

# Substitute $PORT into nginx config template
envsubst '${PORT}' < /app/deploy/nginx.conf.template > /etc/nginx/sites-available/default

# Ensure nginx includes sites-enabled
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

echo "[BidIt] Launching supervisord (nginx + reflex backend)..."
exec /usr/bin/supervisord -n -c /app/deploy/supervisord.conf
