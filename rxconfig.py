import reflex as rx
import os

# Production: use Railway public domain
# Local dev: use localhost:8001 (matching backend_port below)
_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
_api_url = f"https://{_domain}" if _domain else "http://localhost:8001"

config = rx.Config(
    app_name="bidup_ui",
    api_url=_api_url,
    backend_port=8001,
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
