"""Bespoke components with no native Streamlit equivalent: the review stamp
and the docket-style ID rail. Per the developing-with-streamlit skill's own
guidance, custom CSS is reserved for exactly this case -- everything else
(colors, fonts, backgrounds) is handled natively via .streamlit/config.toml.

Rail icons use Phosphor Icons (github.com/phosphor-icons/web, MIT), loaded
from jsDelivr -- verified real, free, and containing the exact icon classes
used here (ph-shield, ph-warning, ph-check) by fetching the actual CSS files,
not just the package's marketing page.
"""

import random

import streamlit as st

from constants import FOREST_GREEN, INK

PHOSPHOR_VERSION = "2.1.2"
# st.html() sanitizes with DOMPurify, which strips <link> tags outright (any
# element that can load external resources) -- confirmed by checking zero
# network requests fired for a <link>-based version of this. @import inside an
# actual <style> tag's text content passes through DOMPurify's sanitizer and
# does trigger the request, so that's used here instead.
PHOSPHOR_LINKS = f"""
<style>
@import url("https://cdn.jsdelivr.net/npm/@phosphor-icons/web@{PHOSPHOR_VERSION}/src/regular/style.css");
@import url("https://cdn.jsdelivr.net/npm/@phosphor-icons/web@{PHOSPHOR_VERSION}/src/fill/style.css");
</style>
"""

STAMP_CSS = f"""
<style>
.stamp {{
  display: inline-block;
  border: 3px solid;
  border-radius: 4px;
  padding: 3px 12px;
  font-family: 'IBM Plex Mono', monospace;
  font-weight: 600;
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  box-shadow: inset 0 0 0 1px currentColor;
  white-space: nowrap;
}}
div[class*="st-key-docket_"] button {{
  font-family: 'IBM Plex Mono', monospace;
  background: transparent;
  border: none;
  box-shadow: none;
  color: {INK};
  justify-content: flex-start;
  padding-left: 2px;
}}
div[class*="st-key-docket_"] button:hover {{
  color: #B08D57;
  background: rgba(22, 27, 46, 0.04);
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(22, 27, 46, 0.08);
  transition: background 0.15s ease, box-shadow 0.15s ease;
}}
.rail-icon {{
  font-size: 1rem;
  line-height: 1.6;
  color: {INK};
  opacity: 0.5;
}}
.docket-selected {{
  font-family: 'IBM Plex Mono', monospace;
  color: white;
  background: {FOREST_GREEN};
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 4px;
  display: block;
}}
.docket-selected .ph-fill {{
  color: white;
  opacity: 1;
  margin-right: 2px;
}}
.docket-header {{
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  opacity: 0.65;
  margin-top: 14px;
  margin-bottom: 2px;
}}
.docket-header .ph {{
  margin-right: 3px;
}}

/* KPI tile accents -- each st.metric is wrapped in a keyed st.container()
   since st.metric itself has no `key` param in this Streamlit version. */
div[class*="st-key-kpi_"] [data-testid="stMetric"] {{
  border-left-width: 4px !important;
  border-left-style: solid !important;
}}

/* Streamlit's own native "copy link to heading" icon (a generic chain-link
   SVG auto-added to every st.header/st.subheader) -- confirmed via live DOM
   inspection this is not from this project's icon code. It only shows on
   hover, but its thin-stroke style matches nothing else in this design
   system, so it's suppressed rather than left to surprise a reader. */
[data-testid="stHeaderActionElements"] {{
  display: none !important;
}}

/* Shadcn-adjacent card treatment: soft shadow + 8px radius, replacing the
   flat 1px border look. Every "card" container is given an explicit
   key="card_..." in app.py since bordered st.container()s carry no
   distinguishing testid of their own in this Streamlit version -- only an
   unstable, auto-generated emotion-cache class -- so key= scoping (the same
   proven pattern as the docket buttons and KPI tiles) is the only reliable
   selector. */
div[class*="st-key-card_"] {{
  border: 1px solid rgba(22, 27, 46, 0.08) !important;
  border-radius: 8px !important;
  box-shadow: 0 1px 2px rgba(22, 27, 46, 0.04), 0 4px 10px rgba(22, 27, 46, 0.06) !important;
}}

/* Apple-style body clarity: generous line-height/letter-spacing on body
   text specifically -- headings stay tight (display-type convention),
   handled instead via config.toml's headingFontSizes/headingFontWeights. */
[data-testid="stMarkdownContainer"] p,
[data-testid="stCaptionContainer"] {{
  line-height: 1.65;
  letter-spacing: 0.01em;
}}

.severity-flat {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: 'IBM Plex Mono', monospace;
  font-weight: 600;
  font-size: 0.72rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  white-space: nowrap;
}}
.severity-flat .dot {{
  width: 7px;
  height: 7px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
}}
</style>
"""

# Section label -> Phosphor icon slug. Verified valid classes (ph-shield,
# ph-warning, ph-check) by fetching the actual Phosphor CSS files, not just
# assuming the names. Phosphor has no literal "triangle" icon -- "warning"
# (a triangle glyph) is the correct semantic match for risk.
SECTION_ICONS = {
    "Controls": "shield",
    "Risks": "warning",
    "Findings": "check",
}


def inject_base_css():
    st.html(PHOSPHOR_LINKS)
    st.html(STAMP_CSS)


def render_stamp(text, ink_hex, seed=None):
    """Renders one review-stamp badge. Rotation is deterministic per (text, seed)
    so it doesn't jitter on every Streamlit rerun, and always has a visible
    minimum tilt (3-8 degrees, either direction) so it can never draw a
    near-zero angle that reads as unrotated."""
    rng = random.Random(seed or text)
    rotation = rng.uniform(3, 8) * rng.choice([-1, 1])
    st.html(
        f'<div class="stamp" style="border-color:{ink_hex}; color:{ink_hex}; '
        f'background:{ink_hex}24; transform: rotate({rotation:.1f}deg);">{text}</div>'
    )


def render_severity_flat(text, ink_hex):
    """Quiet severity indicator for REPEATED LIST contexts (e.g. the Findings
    list): a small colored dot + flat uppercase label, no border, no rotation,
    no tint background. The full render_stamp() above is reserved for
    single-item DETAIL views (Section 4: spend the one bold signature element
    where it's actually seen alone, not stacked N-in-a-row as visual noise)."""
    st.html(
        f'<span class="severity-flat" style="color:{ink_hex};">'
        f'<span class="dot" style="background:{ink_hex};"></span>{text}</span>'
    )


def _section_header(label):
    icon = SECTION_ICONS[label]
    st.html(f'<div class="docket-header"><i class="ph ph-{icon}"></i> {label}</div>')


def _rail_item(item_id, section_label, selected_id):
    icon = SECTION_ICONS[section_label]
    if item_id == selected_id:
        st.html(f'<div class="docket-selected"><i class="ph-fill ph-{icon}"></i> {item_id}</div>')
        return
    icon_col, btn_col = st.columns([1, 6], vertical_alignment="center", gap="small")
    with icon_col:
        st.html(f'<i class="ph ph-{icon} rail-icon"></i>')
    with btn_col:
        if st.button(item_id, key=f"docket_{item_id}", width="stretch"):
            st.session_state["selected_id"] = item_id
            st.rerun()


def render_docket_rail(control_ids, risk_ids, finding_ids, selected_id):
    """Renders the persistent docket-style ID rail in the sidebar. Clicking an ID
    sets st.session_state.selected_id, which the main panel reads to highlight the
    matching item and show a detail workpaper card. Each row gets a Phosphor icon
    (Regular weight normally, Fill weight when selected)."""
    _section_header("Controls")
    for control_id in control_ids:
        _rail_item(control_id, "Controls", selected_id)

    _section_header("Risks")
    for risk_id in risk_ids:
        _rail_item(risk_id, "Risks", selected_id)

    _section_header("Findings")
    for finding_id in finding_ids:
        _rail_item(finding_id, "Findings", selected_id)

    if selected_id and st.button("Clear selection", key="docket_clear", width="stretch"):
        st.session_state["selected_id"] = None
        st.rerun()
