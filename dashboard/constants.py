"""Shared constants: file paths, palette tokens, and status vocabularies.

Palette and status semantics per CLAUDE.md Section 4:
brass = verified/passed, garnet = high-risk/deficiency,
amber = medium-risk, slate-green = low-risk/on-track.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RISK_REGISTER_CSV = REPO_ROOT / "risk-register" / "risk-register.csv"
CONTROL_CATALOG_CSV = REPO_ROOT / "controls" / "control-catalog.csv"
IDENTITY_INVENTORY_CSV = REPO_ROOT / "data" / "identity_inventory.csv"

CISO_ASSISTANT_BASE_URL = "https://localhost:8443"

# Mirrors scripts/risk_scoring.py's definition of a closed Finding.
CLOSED_FINDING_STATUSES = {"resolved", "closed", "dismissed", "deprecated"}

PRIVILEGED_ROLE_CATEGORIES = {"Admin", "Privileged"}
STALE_REVIEW_DAYS = 90

BG = "#F2F3F5"
INK = "#161B2E"
BRASS = "#B08D57"
GARNET = "#7A2E2E"
AMBER = "#C08A2E"
SLATE_GREEN = "#3F6B4F"
GRID_LINE = "#D5D8DE"

# BRASS and AMBER are light enough that, measured against WCAG 2.1's contrast
# formula, neither reaches 4.5:1 as TEXT on the app's light background or on
# white chart fills (verified: ~2.7:1-3.1:1). They stay as-is for FILLS
# (bubble/bar backgrounds, swatches), where that's not a text-contrast case.
# These darkened variants are for anything rendered as text/ink/border on a
# light background instead -- same hue, ~4.5-5.6:1 measured against both
# BG and white.
AMBER_TEXT = "#866120"
BRASS_TEXT = "#7B633D"

# Used for exactly one thing: the docket rail's selected-item fill background
# (white text/icon on top, 7.74:1). Not a replacement for anything above --
# SLATE_GREEN keeps its existing low-risk-band meaning elsewhere.
FOREST_GREEN = "#2D5C3E"

RISK_BAND_COLOR = {
    "Critical": GARNET,
    "High": GARNET,
    "Medium": AMBER,
    "Low": SLATE_GREEN,
}
RISK_BAND_RANK = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}

REQUIREMENT_RESULT_COLOR = {
    "non_compliant": GARNET,
    "partially_compliant": AMBER,
    "compliant": BRASS,
}
# Text color to use ON TOP of the REQUIREMENT_RESULT_COLOR fill above (e.g. the
# control-verdict bar's in-segment label) -- white passes on garnet, but fails
# WCAG AA on amber/brass, so those two segments need dark text instead.
REQUIREMENT_RESULT_TEXT_ON_FILL = {
    "non_compliant": "white",
    "partially_compliant": INK,
    "compliant": INK,
}
REQUIREMENT_RESULT_LABEL = {
    "non_compliant": "Non-compliant",
    "partially_compliant": "Partially compliant",
    "compliant": "Compliant",
}

# Used only for stamp ink/text (never a large fill), so the text-safe
# darkened variants are used directly for medium severity.
FINDING_SEVERITY_COLOR = {
    "critical": GARNET,
    "high": GARNET,
    "medium": AMBER_TEXT,
    "low": SLATE_GREEN,
    "info": SLATE_GREEN,
    "undefined": INK,
}


def risk_band_ink(band):
    return RISK_BAND_COLOR.get(band, INK)


def requirement_result_ink(result):
    return REQUIREMENT_RESULT_COLOR.get(result, INK)


def finding_severity_ink(severity):
    return FINDING_SEVERITY_COLOR.get((severity or "").lower(), INK)


def text_on_fill(fill_hex):
    """WCAG-AA-safe text color for a given fill color from this palette."""
    return INK if fill_hex in (AMBER, BRASS) else "white"


def kpi_accent(is_good):
    """Left-border accent for a KPI tile: on-track vs. concerning (2-tier only --
    no third "bad" band for KPI tiles). AMBER_TEXT, not plain AMBER, since plain
    AMBER measures only ~2.7:1 against this background -- below even the 3:1
    WCAG non-text-contrast floor for a meaningful UI indicator."""
    return SLATE_GREEN if is_good else AMBER_TEXT
