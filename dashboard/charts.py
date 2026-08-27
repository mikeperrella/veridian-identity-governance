"""Plotly figure builders. Tufte-informed: direct labels over legends where
possible, no chartjunk, no encodings that imply more precision than the
underlying data has (e.g. discrete categorical color for risk bands, never
a continuous gradient)."""

import plotly.graph_objects as go

from constants import (
    BG,
    BRASS,
    GARNET,
    GRID_LINE,
    INK,
    REQUIREMENT_RESULT_COLOR,
    REQUIREMENT_RESULT_LABEL,
    REQUIREMENT_RESULT_TEXT_ON_FILL,
    RISK_BAND_RANK,
    SLATE_GREEN,
    risk_band_ink,
    text_on_fill,
)

FONT = dict(family="IBM Plex Sans, sans-serif", color=INK)


def risk_bubble_chart(cells, live_bands=None, selected_risk_id=None):
    """cells: {(likelihood, impact): [risk_row, ...]} from metrics.risk_bubble_cells().
    live_bands: {risk_id: band_name} from metrics.live_residual_bands(), or None/{} if
    CISO Assistant is unreachable.

    Plots each occupied grid cell at its INHERENT (likelihood, impact) position -- the
    risk-register CSV has no independent residual likelihood/impact pair (only a
    combined residual score + band; see docs/risk-methodology.md Section 4a), so a
    literal residual grid isn't buildable from CSV data alone. CISO Assistant DOES
    store independent residual_proba/residual_impact per scenario (Stage 5), so the
    live residual band is used for marker color when available, falling back to that
    risk's CSV band per-row if the API is unreachable. Marker size encodes how many
    risks share that inherent cell.
    """
    live_bands = live_bands or {}
    xs, ys, sizes, colors, labels, hovers, line_widths = [], [], [], [], [], [], []
    for (likelihood, impact), rows in cells.items():
        effective_band = {r["risk_id"]: live_bands.get(r["risk_id"], r["residual_risk_band"]) for r in rows}
        worst_id = max(rows, key=lambda r: RISK_BAND_RANK[effective_band[r["risk_id"]]])["risk_id"]
        xs.append(likelihood)
        ys.append(impact)
        # Capped so adjacent grid cells (one likelihood/impact unit apart, ~66px
        # in this chart's geometry) never visually overlap regardless of count --
        # size is a secondary cue here; the count numeral and hover text carry
        # the exact value.
        sizes.append(22 + 6 * (len(rows) - 1))
        colors.append(risk_band_ink(effective_band[worst_id]))
        # Marker text is a bare count (legible at any bubble size); the full
        # risk_id list and titles are in the hover text instead, since a cell
        # with 2-3 risk_ids doesn't fit legibly inside even a large bubble.
        labels.append(str(len(rows)))
        ids = ", ".join(sorted(row["risk_id"] for row in rows))
        hover_lines = []
        for row in rows:
            band = effective_band[row["risk_id"]]
            source = "live" if row["risk_id"] in live_bands else "CSV fallback"
            note = f" (CSV: {row['residual_risk_band']})" if row["risk_id"] in live_bands and live_bands[row["risk_id"]] != row["residual_risk_band"] else ""
            hover_lines.append(f"{row['risk_id']}: {row['title']} — residual {band} [{source}]{note}")
        hovers.append(f"<b>{ids}</b><br>" + "<br>".join(hover_lines))
        line_widths.append(3 if any(row["risk_id"] == selected_risk_id for row in rows) else 1)

    fig = go.Figure(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers+text",
            marker=dict(size=sizes, color=colors, line=dict(width=line_widths, color=INK)),
            text=labels,
            textposition="middle center",
            textfont=dict(
                family="IBM Plex Mono, monospace",
                color=[text_on_fill(c) for c in colors],
                size=14,
            ),
            hovertext=hovers,
            hoverinfo="text",
        )
    )
    fig.update_layout(
        title="Risk register — inherent likelihood × impact (color = worst residual band in that cell)",
        xaxis=dict(title="Likelihood", range=[0.5, 5.5], dtick=1, gridcolor=GRID_LINE, zeroline=False),
        yaxis=dict(title="Impact", range=[0.5, 5.5], dtick=1, gridcolor=GRID_LINE, zeroline=False),
        plot_bgcolor=BG,
        paper_bgcolor=BG,
        font=FONT,
        showlegend=False,
        height=420,
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def control_verdict_bar(verdict_counts):
    """verdict_counts: a Counter of result -> count from metrics.requirement_verdict_counts().
    100%-stacked horizontal bar over the ~12 SOC 2 points of focus this project tested."""
    order = ["non_compliant", "partially_compliant", "compliant"]
    total = sum(verdict_counts.get(k, 0) for k in order) or 1

    fig = go.Figure()
    for key in order:
        n = verdict_counts.get(key, 0)
        if not n:
            continue
        fig.add_trace(
            go.Bar(
                y=["SOC 2 points of focus tested"],
                x=[n],
                name=REQUIREMENT_RESULT_LABEL[key],
                orientation="h",
                marker_color=REQUIREMENT_RESULT_COLOR[key],
                text=f"{REQUIREMENT_RESULT_LABEL[key]}: {n}/{total}",
                textposition="inside",
                textfont=dict(color=REQUIREMENT_RESULT_TEXT_ON_FILL[key], family="IBM Plex Sans"),
                hoverinfo="text",
            )
        )
    fig.update_layout(
        barmode="stack",
        height=130,
        showlegend=False,
        plot_bgcolor=BG,
        paper_bgcolor=BG,
        font=FONT,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def privileged_review_bar(current, stale):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=["Privileged / admin accounts"],
            x=[current],
            name="Current",
            orientation="h",
            marker_color=SLATE_GREEN,
            text=f"Current: {current}",
            textposition="inside",
            textfont=dict(color="white"),
        )
    )
    fig.add_trace(
        go.Bar(
            y=["Privileged / admin accounts"],
            x=[stale],
            name="Stale",
            orientation="h",
            marker_color=GARNET,
            text=f"Stale (blank or >90d): {stale}",
            textposition="inside",
            textfont=dict(color="white"),
        )
    )
    fig.update_layout(
        barmode="stack",
        height=110,
        showlegend=False,
        plot_bgcolor=BG,
        paper_bgcolor=BG,
        font=FONT,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def c03_timeline_chart(timeline):
    """timeline: metrics.C03_TIMELINE -- [(date_str, exposed_count, stage_label), ...]."""
    dates = [row[0] for row in timeline]
    counts = [row[1] for row in timeline]
    stages = [row[2] for row in timeline]
    colors = [GARNET if c > 0 else BRASS for c in counts]

    fig = go.Figure()
    fig.add_vrect(x0=dates[0], x1=dates[2], fillcolor=GARNET, opacity=0.06, line_width=0)
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=counts,
            mode="lines+markers+text",
            text=stages,
            textposition="top center",
            textfont=dict(family="IBM Plex Sans", size=11, color=INK),
            line=dict(color=INK, width=2),
            marker=dict(size=13, color=colors, line=dict(width=1, color=INK)),
            hovertemplate="%{x}: %{text} — %{y} account(s) exposed<extra></extra>",
        )
    )
    fig.update_layout(
        title="C-03 remediation timeline — one finding's case study, not a program-wide trend",
        yaxis=dict(title="Accounts exposed", dtick=1, range=[-0.5, 3.8], gridcolor=GRID_LINE),
        xaxis=dict(title="Date", gridcolor=GRID_LINE),
        plot_bgcolor=BG,
        paper_bgcolor=BG,
        font=FONT,
        height=340,
        showlegend=False,
        margin=dict(l=50, r=20, t=50, b=40),
    )
    return fig
