import reflex as rx
import os

# Use Railway's public domain to configure WebSocket connections from the browser.
# RAILWAY_PUBLIC_DOMAIN is injected by Railway at both build-time and runtime.
# Locally: omit api_url so Reflex uses its default (http://localhost:8000).
_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")

_config_kwargs = dict(
    app_name="bidup_ui",
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

# Only set api_url in production (Railway injects RAILWAY_PUBLIC_DOMAIN)
if _domain:
    _config_kwargs["api_url"] = f"https://{_domain}"

config = rx.Config(**_config_kwargs)
