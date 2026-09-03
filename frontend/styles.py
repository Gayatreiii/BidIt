# BidUp Design System Constants
BG_COLOR = "#16161a"
CARD_BG = "#1f1f24"
CARD_HOVER = "#26262c"
CARD_BORDER = "#2e2e38"

TEXT_HEADLINE = "#fffffe"
TEXT_MUTED = "#94a1b2"
TEXT_SECONDARY = "#72757e"

ACCENT_COLOR = "#7f5af0"      # Violet
ACCENT_HOVER = "#6b46e5"
ACCENT_LIGHT = "rgba(127, 90, 240, 0.15)"

POSITIVE_COLOR = "#2cb67d"    # Green
POSITIVE_LIGHT = "rgba(44, 182, 125, 0.15)"

ALERT_COLOR = "#ef4565"       # Red
ALERT_LIGHT = "rgba(239, 69, 101, 0.15)"

STROKE_MAIN = "#010101"

# Common UI component styles
CARD_STYLE = {
    "background_color": CARD_BG,
    "border_radius": "12px",
    "border": f"1px solid {CARD_BORDER}",
    "padding": "1.5rem",
    "box_shadow": "0 4px 20px rgba(0, 0, 0, 0.25)"
}

INPUT_STYLE = {
    "background_color": "#16161a",
    "border": f"1px solid {CARD_BORDER}",
    "color": TEXT_HEADLINE,
    "border_radius": "8px",
    "_focus": {
        "border_color": ACCENT_COLOR,
        "box_shadow": f"0 0 0 1px {ACCENT_COLOR}"
    }
}

PRIMARY_BUTTON_STYLE = {
    "background_color": ACCENT_COLOR,
    "color": TEXT_HEADLINE,
    "font_weight": "600",
    "border_radius": "8px",
    "padding": "0.6rem 1.4rem",
    "_hover": {
        "background_color": ACCENT_HOVER,
        "cursor": "pointer"
    }
}

SECONDARY_BUTTON_STYLE = {
    "background_color": "transparent",
    "border": f"1px solid {CARD_BORDER}",
    "color": TEXT_HEADLINE,
    "font_weight": "500",
    "border_radius": "8px",
    "_hover": {
        "background_color": "#26262c",
        "border_color": ACCENT_COLOR
    }
}
