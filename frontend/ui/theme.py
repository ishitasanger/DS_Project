"""Ocean Sunset visual theme for the Virtual Storage Allocation Simulator.

The application uses a clean white base with rich ocean/ sunset accents.
Dark surfaces always pair with white text; light surfaces use dark ink.
"""

# Exact Ocean Sunset reference colours, from deep ocean to warm sunset.
OCEAN_SUNSET = [
    "#001219",  # deep ink
    "#005F73",  # deep ocean teal
    "#0A9396",  # vivid teal
    "#94D2BD",  # seafoam
    "#E9D8A6",  # warm sand
    "#EE9B00",  # golden amber
    "#CA6702",  # burnt orange
    "#BB3E03",  # rust
    "#AE2012",  # vermilion
    "#9B2226",  # deep red
]
RAINBOW = OCEAN_SUNSET

# Main surfaces: white is the dominant background.
CANVAS_BG        = "#FFFFFF"
TILE_BG          = "#FFFFFF"
TEXT_PRIMARY     = "#001219"
TEXT_SECONDARY   = "#36515A"
ACTION_COLOR     = "#005F73"
ACTION_HOVER     = "#0A9396"
DANGER_COLOR     = "#AE2012"
INSIGHT_BG       = "#E5F4EF"

# Dark hero panel with a teal highlight; all text on it is white.
HERO_DARK        = "#001219"
HERO_LIGHT       = "#005F73"
HERO_TEXT        = "#FFFFFF"

# Borders and depth on the white canvas.
SHADOW_COLOR     = "#E5ECEB"
TILE_RADIUS      = 16
TILE_GAP         = 18
TILE_BORDER      = 1
TILE_BORDER_CLR  = "#C9D9D8"

# Process blocks alternate saturated dark colours and lighter tones.
# Text colour is selected for contrast on each fill.
PROCESS_COLORS = [
    ("#005F73", "#FFFFFF"),
    ("#0A9396", "#001219"),
    ("#94D2BD", "#001219"),
    ("#E9D8A6", "#001219"),
    ("#EE9B00", "#001219"),
    ("#CA6702", "#001219"),
    ("#BB3E03", "#FFFFFF"),
    ("#AE2012", "#FFFFFF"),
    ("#9B2226", "#FFFFFF"),
    ("#003B46", "#FFFFFF"),
    ("#0A6B78", "#FFFFFF"),
    ("#D98A3A", "#001219"),
]

FREE_FILL        = "#F5F8F8"
FREE_OUTLINE     = "#607D83"
FREE_DASH        = (6, 4)

# Distinct strategy colours from the same palette.
STRATEGY_COLORS = {
    "first": "#005F73",
    "next":  "#EE9B00",
    "best":  "#0A9396",
    "worst": "#9B2226",
}
STRATEGY_LINES = {
    "first": "-",
    "next":  "--",
    "best":  "-.",
    "worst": ":",
}
STRATEGY_MARKERS = {
    "first": "o",
    "next":  "s",
    "best":  "^",
    "worst": "D",
}
STRATEGY_HATCHES = {
    "first": "",
    "next":  "//",
    "best":  "..",
    "worst": "xx",
}

# Heat-map colours remain light enough for dark labels.
FRAG_HEATMAP = [
    (20,  "#94D2BD", TEXT_PRIMARY),
    (40,  "#E9D8A6", TEXT_PRIMARY),
    (60,  "#EE9B00", TEXT_PRIMARY),
    (80,  "#D98A3A", TEXT_PRIMARY),
    (101, "#F0B7A8", TEXT_PRIMARY),
]
UTIL_HEATMAP = [
    (50,  "#E9D8A6", TEXT_PRIMARY),
    (85,  "#94D2BD", TEXT_PRIMARY),
    (101, "#0A9396", "#FFFFFF"),
]

FAIL_FRAG_COLOR  = "#AE2012"
FAIL_NOSPACE_CLR = "#9B2226"
DONUT_OCCUPIED   = "#005F73"
DONUT_FREE       = "#EE9B00"
TREND_LINE_CLR   = "#0A9396"
TREND_BAND_LOW   = "#94D2BD"
TREND_BAND_MOD   = "#E9D8A6"
TREND_BAND_HIGH  = "#F0B7A8"

STATUS_LOW = {
    "dot":  "#0A9396",
    "text": "#005F73",
    "tint": "#E5F4EF",
}
STATUS_MODERATE = {
    "dot":  "#EE9B00",
    "text": "#704300",
    "tint": "#FFF2D5",
}
STATUS_HIGH = {
    "dot":  "#AE2012",
    "text": "#9B2226",
    "tint": "#FCE8E5",
}

FONT_FAMILY      = "Segoe UI"
FONT_SIZE_HERO   = 30
FONT_SIZE_LARGE  = 20
FONT_SIZE_NORMAL = 11
FONT_SIZE_SMALL  = 10

FOCUS_HIGHLIGHT_WIDTH = 3
FOCUS_HIGHLIGHT_COLOR = "#0A9396"
MIN_WINDOW_WIDTH      = 1100
MIN_WINDOW_HEIGHT     = 700
