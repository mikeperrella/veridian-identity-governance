# Evidence Pack Samples

> **Synthetic data.** Every file in this directory was generated from Veridian LegalTech's fabricated dataset. No real person, employee, or organization is represented. See the root [README.md](../README.md) for the full disclaimer.

These are real exports pulled live from this project's own running systems on **2026-08-27**, not narrative summaries copied from the stage-notes docs — the point is to show what an evidence artifact actually looks like when pulled from a GRC platform's API and a source dataset, the same way an auditor would expect to receive it.

| File | What it is | How it was generated |
|---|---|---|
| `c03-finding-live-export.json` | The full current state of the C-03 Finding ("Terminated Employees Retain Active Okta Access Past Separation Date"), pulled live | `GET /api/findings/` against the local CISO Assistant instance, filtered to the C-03 record, dumped verbatim |
| `c04-uar-finding-live-export.json` | The full current state of the C-04 Finding (privileged/admin UAR cadence), including the n8n automation's real recorded `observation` text | Same method, filtered to the C-04 record |
| `c03-cited-identity-rows.csv` | The exact 3 employee rows (EMP-0007, EMP-0023, EMP-0029) cited as evidence in the C-03 Finding — terminated employees whose Okta status was still Active | Filtered fresh from `data/identity_inventory.csv` by `employee_id` |
| `dashboard-executive-view.png` | A full-page screenshot of the Streamlit dashboard running locally, rendering live data | Captured with Playwright/Chromium against `http://localhost:8501` |

## Why only these four

This is a **sample**, not a full evidence archive — Stage 7's brief asks for evidence pack *samples*, enough to show the pattern (a live platform export, a source-data extract, and a dashboard capture), not an exhaustive export of all 4 findings, 16 risks, and 10 controls. The full, current state of every record is always reachable live via the same API calls documented in `docs/architecture.md` and `scripts/risk_scoring.py`.

## A note on the fourth finding excluded here

A fourth row matches C-03's raw filter (`status == Terminated AND okta_status == Active`) in `data/identity_inventory.csv` — EMP-0190 — but is deliberately excluded from `c03-cited-identity-rows.csv`, same as it was excluded from the Finding's original evidence in Stage 4. Her `term_date` falls after the dataset's `AS_OF` reference date, a data-generation bug documented in `docs/stage3-deployment-notes.md` ("Data Integrity Finding") and indexed in `docs/decision-log.md`. Citing her here would repeat the same evidentiary error the Stage 4 pass caught and avoided.
