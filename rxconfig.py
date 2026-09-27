import reflex as rx
import os

# Use Railway's public domain to configure WebSocket connections from the browser.
# RAILWAY_PUBLIC_DOMAIN is injected by Railway at both build-time and runtime.
# nginx proxies /_event WebSocket from the public port to reflex backend (port 8001).
_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
_api_url = f"https://{_domain}" if _domain else "http://localhost:8001"

config = rx.Config(
    app_name="bidup_ui",
    api_url=_api_url,
    cors_allowed_origins=["*"],
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(
                appearance="light",
                has_background=True,
                radius="medium",
                accent_color="violet",
            )
        ),
    ],
)
