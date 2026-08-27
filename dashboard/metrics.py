"""Local computations for dashboard metrics that CISO Assistant's API doesn't carry,
plus the hardcoded C-03 remediation timeline (see the module docstring below for why
that one series is hardcoded rather than computed).
"""

import csv
from collections import Counter, defaultdict
from datetime import date, datetime

from constants import (
    CLOSED_FINDING_STATUSES,
    CONTROL_CATALOG_CSV,
    IDENTITY_INVENTORY_CSV,
    PRIVILEGED_ROLE_CATEGORIES,
    RISK_REGISTER_CSV,
    STALE_REVIEW_DAYS,
)


def load_risk_register():
    with open(RISK_REGISTER_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_control_catalog():
    with open(CONTROL_CATALOG_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_identity_inventory():
    with open(IDENTITY_INVENTORY_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def avg_control_effectiveness(risk_rows):
    """Mean of risk-register.csv's control_effectiveness_pct across all risks.
    This is a risk-register average, not a per-control pass/fail rate -- see
    requirement_verdict_counts() below for the live SOC 2 test-verdict split,
    which is the other, distinct half of "control effectiveness %"."""
    values = [int(r["control_effectiveness_pct"]) for r in risk_rows]
    return sum(values) / len(values) if values else 0.0


def live_residual_bands(risk_scenarios):
    """Maps risk_id -> live residual band name ("Low"/"Medium"/"High"/"Critical") from
    CISO Assistant's RiskScenario.residual_level, keyed by ref_id (== risk_id).

    CISO Assistant DOES independently store residual_proba/residual_impact -- Stage 5's
    risk_scoring.py PATCHes them for every scenario, verified live in this repo's own
    Stage 5 notes. What the CSV alone can't do is split its single combined
    residual_risk score into two independent index values (docs/risk-methodology.md
    Section 4a) -- that's a limitation of the CSV's model, not of CISO Assistant's API.
    So the live band is authoritative here; the CSV's residual_risk_band can legitimately
    disagree for a given risk (different formulas by design, see Section 4a) and is used
    only as a fallback when the live API is unreachable.

    risk_scenarios: the list from api_client.get_risk_scenarios(), or None if unreachable.
    Scenarios with an unrated (-1) residual_proba/residual_impact are skipped so callers
    fall back to that risk's CSV band instead of a nonsense level name.
    """
    bands = {}
    for scenario in risk_scenarios or []:
        ref_id = scenario.get("ref_id")
        if not ref_id:
            continue
        proba = scenario.get("residual_proba", {}).get("value", -1)
        impact = scenario.get("residual_impact", {}).get("value", -1)
        if proba < 0 or impact < 0:
            continue
        level = scenario.get("residual_level") or {}
        if level.get("name"):
            bands[ref_id] = level["name"]
    return bands


def risk_bubble_cells(risk_rows):
    """Groups risks by their inherent (likelihood, impact) grid cell.
    Returns {(likelihood, impact): [row, ...]}."""
    cells = defaultdict(list)
    for r in risk_rows:
        key = (int(r["likelihood"]), int(r["impact"]))
        cells[key].append(r)
    return cells


def privileged_review_status(identity_rows, as_of=None):
    """Returns (total_privileged, current_count, stale_count).

    Staleness rule mirrors Stage 5's n8n UAR workflow exactly (blank or
    >90 days before as_of) -- verified this session to reproduce that run's
    45 in-scope / 31 stale result on the CSV as committed.
    """
    as_of = as_of or date.today()
    privileged = [r for r in identity_rows if r["role_category"] in PRIVILEGED_ROLE_CATEGORIES]
    stale = 0
    for r in privileged:
        raw = (r.get("last_access_review_date") or "").strip()
        if not raw:
            stale += 1
            continue
        reviewed = datetime.strptime(raw, "%Y-%m-%d").date()
        if (as_of - reviewed).days > STALE_REVIEW_DAYS:
            stale += 1
    total = len(privileged)
    return total, total - stale, stale


def findings_open_and_overdue(findings, as_of=None):
    """findings: the list from api_client.get_findings(), or None if unreachable."""
    as_of = as_of or date.today()
    open_findings, overdue_findings = [], []
    for f in findings or []:
        if (f.get("status") or "").lower() in CLOSED_FINDING_STATUSES:
            continue
        open_findings.append(f)
        due = f.get("due_date")
        if due and date.fromisoformat(due) < as_of:
            overdue_findings.append(f)
    return open_findings, overdue_findings


def requirement_verdict_counts(assessments):
    """assessments: the filtered list from api_client.get_requirement_assessments(),
    or None if unreachable. Counts by result value (non_compliant / partially_compliant
    / compliant)."""
    return Counter(a.get("result") for a in assessments or [])


def find_c03_finding(findings):
    """Locates the C-03 finding among live API results by its linked applied control's
    name -- this CISO Assistant instance's Finding.ref_id field is not populated, so
    name/relationship matching is the only reliable live lookup."""
    for f in findings or []:
        controls = f.get("applied_controls") or []
        if any("Termination Deprovisioning" in (c.get("str") or "") for c in controls):
            return f
    return None


# --- C-03 remediation timeline -------------------------------------------
# Hardcoded rather than computed: no CISO Assistant field carries a Finding's
# dated observation history (only its current state). These 5 dates and
# exposed-account counts are transcribed verbatim from the Finding's real
# `observation` log, documented in full in
# docs/stage4-control-testing-findings.md ("Full Lifecycle -- Verified
# `observation` Log"). This is the ONLY multi-point dated series anywhere in
# the repo -- see that doc and docs/stage5-automation-notes.md for
# confirmation that no other finding or control has more than one dated
# event, which is why this is presented as a single-finding case study
# rather than a program-wide trend (Section 0 non-negotiable #3: no
# fabricated outcomes).
C03_TIMELINE = [
    ("2026-08-26", 3, "Identified"),
    ("2026-08-27", 3, "Confirmed"),
    ("2026-08-28", 0, "Deactivated"),
    ("2026-08-31", 0, "Verified closed"),
    ("2026-09-05", 0, "Monitoring complete"),
]
