"""VIGCAP executive dashboard (Stage 6).

Fictional company, fictional data: Veridian LegalTech does not exist. Every
employee, vendor, risk, control, and finding referenced here is synthetic,
generated for this portfolio project. See the root README for the full
disclaimer.

Run with:
    CISO_ASSISTANT_PAT=<token> streamlit run dashboard/app.py
"""

import sys
from datetime import date, datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

import api_client
import charts
import components
import metrics
from constants import BRASS_TEXT, finding_severity_ink, kpi_accent

st.set_page_config(
    page_title="VIGCAP — Veridian Identity Governance Dashboard",
    page_icon=":material/gavel:",
    layout="wide",
)
components.inject_base_css()

st.session_state.setdefault("selected_id", None)


@st.cache_data(ttl=300)
def cached_risk_register():
    return metrics.load_risk_register()


@st.cache_data(ttl=300)
def cached_control_catalog():
    return metrics.load_control_catalog()


@st.cache_data(ttl=300)
def cached_identity_inventory():
    return metrics.load_identity_inventory()


@st.cache_data(ttl=30)
def cached_risk_scenarios():
    return api_client.get_risk_scenarios()


@st.cache_data(ttl=30)
def cached_findings():
    return api_client.get_findings()


@st.cache_data(ttl=30)
def cached_requirement_assessments():
    return api_client.get_requirement_assessments()


risk_rows = cached_risk_register()
control_rows = cached_control_catalog()
identity_rows = cached_identity_inventory()

risk_scenarios = cached_risk_scenarios()
findings = cached_findings()
assessments = cached_requirement_assessments()
live_bands = metrics.live_residual_bands(risk_scenarios)

risk_by_id = {r["risk_id"]: r for r in risk_rows}
control_by_id = {c["control_id"]: c for c in control_rows}
# Findings have no ref_id in this CISO Assistant instance -- synthetic short IDs
# for the docket rail, in the same due-date order as the Findings section below.
sorted_findings = sorted(findings or [], key=lambda x: x.get("due_date") or "9999-99-99")
finding_by_id = {f"F-{i + 1:02d}": f for i, f in enumerate(sorted_findings)}

# --- Header ---------------------------------------------------------------

st.title("VIGCAP — Veridian Identity Governance & Continuous Assurance")
st.caption(
    "⚠ Synthetic portfolio project. Veridian LegalTech does not exist. Every employee, "
    "vendor, risk, control, and finding shown here is fabricated data — not a real audit."
)

# --- Sidebar: docket rail ---------------------------------------------------

with st.sidebar:
    st.markdown("**Docket**")
    components.render_docket_rail(
        control_ids=sorted(control_by_id),
        risk_ids=sorted(risk_by_id),
        finding_ids=sorted(finding_by_id),
        selected_id=st.session_state["selected_id"],
    )
    st.divider()
    st.caption(
        f"Live CISO Assistant data as of {datetime.now().strftime('%Y-%m-%d %H:%M')}. "
        "Heat map position (inherent L×I) and privileged-review % are computed from "
        "this repo's CSV data; heat map color (residual band), findings, and "
        "control-verdict figures are pulled live. The C-03 timeline is a hardcoded "
        "case study (see caption below it for why)."
    )

# --- KPI row -----------------------------------------------------------

total_priv, current_priv, stale_priv = metrics.privileged_review_status(identity_rows, as_of=date.today())
open_findings, overdue_findings = metrics.findings_open_and_overdue(findings, as_of=date.today())
avg_effectiveness = metrics.avg_control_effectiveness(risk_rows)

# Left-border accent color per KPI tile -- good (on-track) vs. concerning, per
# constants.kpi_accent(). None (no accent) when the underlying value is "--"
# because the live API is unreachable, rather than implying a false signal.
kpi_colors = {
    "kpi_privileged": kpi_accent(current_priv / total_priv >= 0.5) if total_priv else None,
    "kpi_open": kpi_accent(len(open_findings) == 0) if findings is not None else None,
    "kpi_overdue": kpi_accent(len(overdue_findings) == 0) if findings is not None else None,
    "kpi_effectiveness": kpi_accent(avg_effectiveness >= 50),
}
st.html(
    "<style>"
    + "\n".join(
        f'div[class*="st-key-{key}"] [data-testid="stMetric"] {{ border-left-color: {color}; }}'
        for key, color in kpi_colors.items()
        if color
    )
    + "</style>"
)

with st.container(horizontal=True):
    with st.container(key="kpi_privileged"):
        st.metric(
            "Privileged accounts current on review",
            f"{current_priv}/{total_priv}" if total_priv else "—",
            border=True,
        )
    with st.container(key="kpi_open"):
        st.metric(
            "Open findings",
            len(open_findings) if findings is not None else "—",
            border=True,
        )
    with st.container(key="kpi_overdue"):
        st.metric(
            "Overdue findings",
            len(overdue_findings) if findings is not None else "—",
            border=True,
        )
    with st.container(key="kpi_effectiveness"):
        st.metric(
            "Avg. control effectiveness (risk-adjusted)",
            f"{avg_effectiveness:.0f}%",
            border=True,
        )
st.caption(
    f"{stale_priv} of {total_priv} privileged/admin accounts are stale (review blank or "
    "over 90 days old), same rule as Stage 5's n8n UAR run."
)

# --- Risk heat map -------------------------------------------------------

with st.container(border=True, key="card_risk_register"):
    st.subheader("Risk register")
    cells = metrics.risk_bubble_cells(risk_rows)
    fig = charts.risk_bubble_chart(cells, live_bands=live_bands, selected_risk_id=st.session_state["selected_id"])
    st.plotly_chart(fig, config={"displayModeBar": False})
    if live_bands:
        diverging = sum(
            1 for r in risk_rows if r["risk_id"] in live_bands and live_bands[r["risk_id"]] != r["residual_risk_band"]
        )
        st.caption(
            "Plotted at each risk's inherent likelihood × impact (from this repo's CSV -- "
            "CISO Assistant's inherent values are copied from the same CSV, per Stage 5's "
            "drift check). Bubble color is CISO Assistant's LIVE residual band for each "
            "risk (hover for detail). This can legitimately differ from risk-register.csv's "
            "residual_risk_band for a given risk -- the two use different formulas by "
            "design, since a single combined score can't be split into independent "
            f"likelihood/impact indices without inventing values (docs/risk-methodology.md "
            f"Section 4a). Currently differs for {diverging} of {len(risk_rows)} risks."
        )
    else:
        st.warning(
            "CISO Assistant is unreachable — showing risk-register.csv's residual band "
            "as a fallback instead of the live value.",
            icon=":material/warning:",
        )

    selected = st.session_state["selected_id"]
    if selected and selected in risk_by_id:
        row = risk_by_id[selected]
        with st.container(border=True, key="card_risk_detail"):
            st.markdown(f"**{row['risk_id']} — {row['title']}**")
            st.write(row["description"])
            st.write(f"**Threat scenario:** {row['threat_scenario']}")
            cols = st.columns(4)
            cols[0].metric("Likelihood", row["likelihood"])
            cols[1].metric("Impact", row["impact"])
            cols[2].metric("Inherent risk", f"{row['inherent_risk']} ({row['inherent_risk_band']})")
            cols[3].metric("Residual risk (CSV, authoritative)", f"{row['residual_risk']} ({row['residual_risk_band']})")
            live_band = live_bands.get(row["risk_id"])
            if live_band:
                st.caption(
                    f"Live residual band in CISO Assistant: **{live_band}**"
                    + (" (matches CSV)" if live_band == row["residual_risk_band"] else " (differs from CSV -- see heat map caption above)")
                )
            components.render_stamp(row["treatment"], BRASS_TEXT, seed=row["risk_id"])
            st.write(f"**Treatment rationale:** {row['treatment_rationale']}")
            st.caption(f"Owner: {row['owner']} · Due: {row['due_date']} · Status: {row['status']}")

# --- Control effectiveness -----------------------------------------------

with st.container(border=True, key="card_control_effectiveness"):
    st.subheader("Control effectiveness")
    if assessments is not None:
        verdict_counts = metrics.requirement_verdict_counts(assessments)
        st.plotly_chart(charts.control_verdict_bar(verdict_counts), config={"displayModeBar": False})
        st.caption(
            "Live from CISO Assistant's RequirementAssessment verdicts for the SOC 2 "
            "points of focus actually tested in Stage 4 (worst-case-wins where a point "
            "of focus is shared by multiple controls). This is distinct from the "
            "risk-adjusted average above: that figure is a CSV input to residual-risk "
            "scoring, this one is a live test outcome."
        )
    else:
        st.warning(
            "CISO Assistant is unreachable — control test verdicts require the live API. "
            "Confirm CISO_ASSISTANT_PAT is set and the platform is running.",
            icon=":material/warning:",
        )

    selected = st.session_state["selected_id"]
    if selected and selected in control_by_id:
        row = control_by_id[selected]
        with st.container(border=True, key="card_control_detail"):
            st.markdown(f"**{row['control_id']} — {row['title']}**")
            st.write(row["objective"])
            cols = st.columns(3)
            cols[0].metric("Implementation status", row["implementation_status"])
            cols[1].metric("Frequency", row["frequency"])
            cols[2].metric("Owner", row["owner"])
            st.write(f"**Test procedure:** {row['test_procedure']}")
            st.write(f"**Rationale:** {row['control_rationale']}")
            linked_finding = None
            for f in findings or []:
                if any(row["title"] in (c.get("str") or "") for c in f.get("applied_controls") or []):
                    linked_finding = f
                    break
            if linked_finding:
                st.write(f"**Linked finding (live):** {linked_finding['name']}")
                components.render_stamp(
                    linked_finding["severity"],
                    finding_severity_ink(linked_finding["severity"]),
                    seed=linked_finding["id"],
                )

# --- Findings --------------------------------------------------------------

with st.container(border=True, key="card_findings"):
    st.subheader("Findings")
    if findings is not None:
        for finding_id, f in finding_by_id.items():
            badge_col, text_col = st.columns([1, 6], vertical_alignment="top")
            with badge_col:
                components.render_severity_flat(f["severity"], finding_severity_ink(f["severity"]))
            with text_col:
                st.markdown(f"**`{finding_id}` {f['name']}**")
                is_overdue = f in overdue_findings
                caption = f"Status: {f.get('status', '').title()}  ·  Due: {f.get('due_date')}"
                if is_overdue:
                    caption += "  ·  **Overdue**"
                st.caption(caption)
        if not findings:
            st.caption("No findings recorded.")

        selected = st.session_state["selected_id"]
        if selected and selected in finding_by_id:
            f = finding_by_id[selected]
            with st.container(border=True, key="card_finding_detail"):
                st.markdown(f"**{selected} — {f['name']}**")
                st.write(f.get("description", ""))
                components.render_stamp(f["severity"], finding_severity_ink(f["severity"]), seed=f["id"])
                st.caption(
                    f"Status: {f.get('status')} · Due: {f.get('due_date')} · "
                    f"Priority: {f.get('priority')}"
                )
    else:
        st.warning(
            "CISO Assistant is unreachable — the findings log requires the live API.",
            icon=":material/warning:",
        )

# --- C-03 remediation timeline ---------------------------------------------

with st.container(border=True, key="card_c03_timeline"):
    st.subheader("C-03 remediation timeline")
    st.plotly_chart(charts.c03_timeline_chart(metrics.C03_TIMELINE), config={"displayModeBar": False})
    st.caption(
        "This is the ONLY finding in the register with more than one dated event — "
        "the other three sit at a single 'identified' timestamp with future due dates. "
        "Shown as a single-finding case study, not a program-wide trend, per this "
        "project's no-fabricated-outcomes rule. Dates and counts are transcribed "
        "verbatim from the finding's real observation log in "
        "docs/stage4-control-testing-findings.md."
    )
    live_c03 = metrics.find_c03_finding(findings)
    if live_c03:
        st.caption(
            f"Verified live at {datetime.now().strftime('%Y-%m-%d %H:%M')}: "
            f"current status = **{live_c03.get('status')}**, severity = **{live_c03.get('severity')}**."
        )
        if live_c03.get("status") not in {"closed", "resolved"}:
            st.warning(
                "Live status no longer matches the closed narrative above — the finding "
                "may have been reopened or reset since this timeline was written.",
                icon=":material/warning:",
            )
    elif findings is not None:
        st.warning("Could not locate the C-03 finding in the live API response.", icon=":material/warning:")

st.caption(
    "VIGCAP is a fictional-company portfolio simulation (Veridian LegalTech), not real "
    "audit or client work. Source: github.com/mikeperrella/veridian-identity-governance."
)
