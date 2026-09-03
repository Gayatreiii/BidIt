import reflex as rx

config = rx.Config(
    app_name="bidup_ui",
    api_url="http://localhost:8001",
    backend_port=8001,
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
    ]
)

