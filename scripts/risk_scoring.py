"""
Stage 5 risk-scoring script.

Recomputes CISO Assistant's residual_proba/residual_impact indices for every
RiskScenario from risk-register.csv's control_effectiveness_pct, using the
likelihood-only reduction rule documented in docs/risk-methodology.md
Section 4a (reducing both indices independently would compound to
roughly the square of the intended reduction -- see that section for the
full math). It also drift-checks CISO Assistant's live inherent values
against the CSV, and flags any open Finding whose due_date has passed.

Read-only against Findings; the only writes this script performs are the
PATCH calls to RiskScenario.residual_proba/residual_impact.

Usage:
    CISO_ASSISTANT_PAT=<token> python scripts/risk_scoring.py [--base-url URL] [--out FILE]
"""

import argparse
import csv
import math
import os
import sys
from datetime import date
from pathlib import Path

import requests
import urllib3

# Fixed reference date -- matches data/generate_inventory.py's AS_OF convention
# so "is this Finding overdue" never drifts with real wall-clock time and the
# report stays byte-identical across reruns.
AS_OF = date(2026, 8, 26)

REPO_ROOT = Path(__file__).resolve().parent.parent
RISK_REGISTER_CSV = REPO_ROOT / "risk-register" / "risk-register.csv"

CLOSED_FINDING_STATUSES = {"resolved", "closed", "dismissed", "deprecated"}

# Matrix index range for a 5x5 likelihood/impact matrix (0-4).
MIN_INDEX = 0
MAX_INDEX = 4


def load_control_effectiveness(csv_path):
    """Returns {ref_id: {"effectiveness_pct": int, "likelihood": int, "impact": int}}."""
    rows = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows[row["risk_id"]] = {
                "effectiveness_pct": int(row["control_effectiveness_pct"]),
                "likelihood": int(row["likelihood"]),
                "impact": int(row["impact"]),
            }
    return rows


def get_all_pages(session, base_url, path):
    """GETs a paginated CISO Assistant endpoint and returns the concatenated results list."""
    results = []
    url = f"{base_url}{path}"
    while url:
        resp = session.get(url, verify=False, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        results.extend(payload["results"])
        url = payload.get("next")
    return results


def compute_residual(inherent_proba_index, inherent_impact_index, effectiveness_pct):
    """
    Likelihood-only reduction (docs/risk-methodology.md Section 4a):
    only the probability/likelihood index is reduced by effectiveness_pct,
    floored to the nearest valid matrix index. Impact is left unchanged --
    every control in this catalog is preventive (reduces the probability of
    unauthorized access), not mitigating (reducing impact/severity once
    access occurs already happened).
    """
    reduction_factor = 1 - (effectiveness_pct / 100)
    residual_proba_index = math.floor(inherent_proba_index * reduction_factor)
    residual_proba_index = max(MIN_INDEX, min(MAX_INDEX, residual_proba_index))
    residual_impact_index = inherent_impact_index
    return residual_proba_index, residual_impact_index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://localhost:8443")
    parser.add_argument("--out", default=None, help="Write the markdown report to this file instead of stdout")
    args = parser.parse_args()

    pat = os.environ.get("CISO_ASSISTANT_PAT")
    if not pat:
        print("ERROR: CISO_ASSISTANT_PAT environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    session = requests.Session()
    session.headers.update({"Authorization": f"Token {pat}"})

    csv_rows = load_control_effectiveness(RISK_REGISTER_CSV)

    scenarios = get_all_pages(session, args.base_url, "/api/risk-scenarios/")

    updated = []
    drift = []
    unrated = []
    unmatched = []

    for scenario in scenarios:
        ref_id = scenario.get("ref_id")
        if not ref_id or ref_id not in csv_rows:
            unmatched.append(ref_id or scenario["id"])
            continue

        csv_row = csv_rows[ref_id]

        inherent_proba = scenario["inherent_proba"]["value"]
        inherent_impact = scenario["inherent_impact"]["value"]

        if inherent_proba < 0 or inherent_impact < 0:
            unrated.append(ref_id)
            continue

        # Drift check: CISO Assistant's 0-4 matrix index vs. the CSV's 1-5 scale.
        live_likelihood = inherent_proba + 1
        live_impact = inherent_impact + 1
        if live_likelihood != csv_row["likelihood"] or live_impact != csv_row["impact"]:
            drift.append(
                {
                    "ref_id": ref_id,
                    "csv_likelihood": csv_row["likelihood"],
                    "csv_impact": csv_row["impact"],
                    "live_likelihood": live_likelihood,
                    "live_impact": live_impact,
                }
            )

        residual_proba, residual_impact = compute_residual(
            inherent_proba, inherent_impact, csv_row["effectiveness_pct"]
        )

        resp = session.patch(
            f"{args.base_url}/api/risk-scenarios/{scenario['id']}/",
            json={"residual_proba": residual_proba, "residual_impact": residual_impact},
            verify=False,
            timeout=30,
        )
        resp.raise_for_status()

        updated.append(
            {
                "ref_id": ref_id,
                "effectiveness_pct": csv_row["effectiveness_pct"],
                "inherent_proba": inherent_proba,
                "inherent_impact": inherent_impact,
                "residual_proba": residual_proba,
                "residual_impact": residual_impact,
            }
        )

    findings = get_all_pages(session, args.base_url, "/api/findings/")
    overdue = []
    for finding in findings:
        due_date_str = finding.get("due_date")
        status = finding.get("status")
        if not due_date_str or status in CLOSED_FINDING_STATUSES:
            continue
        due_date = date.fromisoformat(due_date_str)
        if due_date < AS_OF:
            overdue.append(
                {
                    "ref_id": finding.get("ref_id") or finding["id"],
                    "name": finding.get("name", ""),
                    "due_date": due_date_str,
                    "status": status,
                }
            )

    report = render_report(updated, drift, unrated, unmatched, overdue)

    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(report)
    else:
        print(report, end="")


def render_report(updated, drift, unrated, unmatched, overdue):
    lines = []
    lines.append("# Risk Scoring Report")
    lines.append("")
    lines.append(
        "Deterministic recalculation of residual_proba/residual_impact for every "
        "RiskScenario, per docs/risk-methodology.md Section 4a (likelihood-only "
        "reduction; impact left at its inherent value)."
    )
    lines.append("")

    lines.append("## Residual Risk Updates")
    lines.append("")
    lines.append("| ref_id | effectiveness_pct | inherent (L,I) | residual (L,I) |")
    lines.append("|---|---|---|---|")
    for row in sorted(updated, key=lambda r: r["ref_id"]):
        lines.append(
            f"| {row['ref_id']} | {row['effectiveness_pct']}% "
            f"| ({row['inherent_proba']},{row['inherent_impact']}) "
            f"| ({row['residual_proba']},{row['residual_impact']}) |"
        )
    lines.append("")

    lines.append("## Drift Check (live inherent values vs. risk-register.csv)")
    lines.append("")
    if drift:
        lines.append("| ref_id | CSV (L,I) | Live (L,I) |")
        lines.append("|---|---|---|")
        for row in sorted(drift, key=lambda r: r["ref_id"]):
            lines.append(
                f"| {row['ref_id']} | ({row['csv_likelihood']},{row['csv_impact']}) "
                f"| ({row['live_likelihood']},{row['live_impact']}) |"
            )
    else:
        lines.append("No drift detected -- all live inherent values match the CSV.")
    lines.append("")

    lines.append("## Unrated Scenarios (skipped, no inherent_proba/inherent_impact set)")
    lines.append("")
    if unrated:
        for ref_id in sorted(unrated):
            lines.append(f"- {ref_id}")
    else:
        lines.append("None.")
    lines.append("")

    lines.append("## Unmatched Scenarios (no corresponding risk_id in risk-register.csv)")
    lines.append("")
    if unmatched:
        for ref_id in sorted(str(r) for r in unmatched):
            lines.append(f"- {ref_id}")
    else:
        lines.append("None.")
    lines.append("")

    lines.append(f"## Overdue Findings (due_date before {AS_OF.isoformat()}, not closed)")
    lines.append("")
    if overdue:
        lines.append("| ref_id | name | due_date | status |")
        lines.append("|---|---|---|---|")
        for row in sorted(overdue, key=lambda r: r["ref_id"]):
            lines.append(f"| {row['ref_id']} | {row['name']} | {row['due_date']} | {row['status']} |")
    else:
        lines.append("None.")
    lines.append("")

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
