# Stage 4 — Control Testing & Findings

Documents how the 10 controls in `controls/control-catalog.csv` were tested against the SOC 2 framework loaded in Stage 3, and how the resulting findings were recorded in CISO Assistant. No secrets appear in this file.

## Test Outcome Design

Before creating anything, a proposed `result`/`extended_result` was derived for each of the 10 controls directly from `implementation_status` and `control_rationale` already written in `controls/control-catalog.csv` — no new judgment invented, only what was already on record:

- **3 non_compliant**: C-03 (Termination Deprovisioning — proven live exposure), C-06 and C-08 (both "Designed, not yet implemented" — nothing operates yet)
- **7 partially_compliant**: C-01, C-02, C-04, C-05, C-07, C-09, C-10 — each has a documented gap, none rises to proven-current-exposure

Zero controls were marked fully `compliant` — every one of the 10 has an acknowledged gap in its own rationale.

## FindingsAssessment Container

Created: `name: "Veridian Identity Governance Control Testing 2026"`, `category: audit` (not `self_identified` — Stage 4 is a structured pass against pre-defined test procedures already written per control, documented "exactly as an auditor would expect to see it" per `CLAUDE.md` Section 7, which is an audit-style exercise, not an ad hoc self-discovered issue), `reported_at: 2026-08-26`, `status: in_progress`.

## Which Controls Got an Individual Finding

**Rule:** every `non_compliant` result gets a Finding (a compliance verdict alone doesn't carry a remediation plan/owner/due date). For `partially_compliant` results, a Finding was warranted only where the control's own rationale cites **concrete data evidence** of an actual gap — not just a described risk of future drift. Otherwise the RequirementAssessment's `result`/`extended_result` alone is sufficient, since duplicating the same gap into a second tracking system (Finding) when the risk register already carries its remediation plan would just fork the record.

| Control | Result | Finding? | Why |
|---|---|---|---|
| **C-03** | non_compliant | **Yes** | Highest severity, proven live exposure. The full-lifecycle demonstration. |
| **C-06** | non_compliant | **Yes** | Absence-of-control; no session logging exists at all. |
| **C-08** | non_compliant | **Yes** | Absence-of-control; ties to R-011's "worst-case scenario" language. |
| **C-04** | partially_compliant | **Yes** | Only partially_compliant control whose rationale cites the same class of concrete, citable data evidence as C-03 (stale/missing UAR review dates), just lower severity. |
| C-01, C-02, C-05, C-07, C-09, C-10 | partially_compliant | No | Each either already has its own tracked remediation mechanism elsewhere (e.g. C-01's gap is covered by R-013's Accept treatment), describes a future risk rather than a proven current gap, or has one half of the control confirmed working with no proof the other half has actually failed. |

**Result: 4 Findings**, all under the one FindingsAssessment.

## C-03 Finding — Full Detail

- **Name:** "Terminated Employees Retain Active Okta Access Past Separation Date"
- **`requirement_node`:** CC6.2.3 ("Prevents the Use of Credentials When No Longer Valid") — the more precise match for credentials remaining active, vs. CC6.3.2's broader "removes access"
- **`applied_controls`:** C-03 (Termination Deprovisioning)
- **`asset`:** AST-001 (Okta) — the system where the exposure lives
- **`severity`:** **critical** (4) — not "high." Three specific accounts *currently* hold valid, active credentials past termination; severity reflects the confirmed presence of the vulnerable condition, not whether it's been actively exploited
- **`priority`:** 1 (highest)
- **`owner`:** IT/Security Manager
- **`due_date`:** 2026-08-31 — a short-term date for the *immediate* fix (deactivate the known accounts); the *systemic* fix (event-driven automated deprovisioning) remains tracked separately at R-002 (due 2026-10-15) and C-02

**`description`** (root cause, business impact, evidence — using the corrected 3-account set, not the original 4):
> **Root cause:** Termination-triggered deprovisioning depends entirely on a manager remembering to notify IT after an employee's last day. There is no automated trigger tied to the HRIS termination event, and no reconciliation step verifies that Okta deactivation actually occurred.
>
> **Business impact:** A terminated employee with valid SSO credentials can access client matter data and internal systems after separation — a direct confidentiality exposure with contractual and regulatory consequences, and concretely a SOC 2 CC6.2/CC6.3 nonconformity that puts SOC 2 Type II attestation (and the enterprise deals gated on it) at risk.
>
> **Evidence:** `data/identity_inventory.csv` shows 3 employees with a valid past `status: Terminated` and `okta_status: Active`. Specific example: **EMP-0007, Abigail Shaffer** (Product Designer), terminated 2024-08-15, still `Active` in Okta as of her last recorded access review (2026-07-19). The other 2 valid accounts: EMP-0023, EMP-0029. (A 4th matching row, EMP-0190, was excluded — see the Data Integrity Finding link below.)

### Full Lifecycle — Verified `observation` Log

Walked through all 5 stages via individual `PATCH` requests, each verified with a fresh `GET` immediately after before proceeding to the next stage. One gap was caught and corrected mid-process: the "identified" observation line was omitted when the Finding was first created (only `description` was set) — it was added as a same-day correction before the requested transitions began, still dated 2026-08-26 (accurate, just entered later). Final state, pulled fresh from the platform:

```
[2026-08-26] Identified during Stage 4 control test of C-03: identity inventory review found 3 terminated employees (incl. EMP-0007 Abigail Shaffer) still Active in Okta past their termination date. (A 4th matching row, EMP-0190, was excluded after direct verification found her term_date is 11 days in the future -- a data-generation bug tracked separately, not cited as evidence here.)
[2026-08-27] Confirmed all 3 accounts (EMP-0007, EMP-0023, EMP-0029) hold Active, session-capable Okta credentials past their termination date. Immediate deactivation initiated.
[2026-08-28] All 3 accounts manually deactivated in Okta. Root-cause remediation (event-driven deprovisioning tied to the HRIS termination trigger, per C-03/R-002/C-02's shared remediation plan) opened as a tracked engineering task.
[2026-08-31] Verified all 3 accounts remain deactivated with no login activity since remediation. Immediate exposure closed. Systemic automated-deprovisioning fix remains tracked separately under R-002 (due 2026-10-15) and C-02 -- this finding covers the specific 3-account exposure only, not the underlying process gap.
[2026-09-05] One-week monitoring window complete; no further offboarding gaps detected. Finding closed.
```

**Final status: `closed`.**

**Honesty note:** `data/identity_inventory.csv` was **not** edited to reflect these 3 accounts as deactivated — that file is Stage 1's generated snapshot, and rewriting it to match this narrative would be editing source data to fit a story after the fact. This Finding's lifecycle documents the *tracked remediation record* inside CISO Assistant, the same way a real audit finding gets worked and closed without retroactively altering the original evidence export.

## The Other 3 Findings — Left Open at `identified`

These genuinely remain unworked, which is realistic — Stage 4's DoD asks for *at least one* full lifecycle, not all of them:

| Finding | Control | Requirement Node | Severity | Owner | Due Date |
|---|---|---|---|---|---|
| Privileged/Admin UAR Cadence Not Centrally Enforced or Tracked | C-04 | CC6.3.4 | medium | Compliance Analyst | 2026-09-30 |
| Privileged Session Logging and Break-Glass Monitoring Not Yet Implemented | C-06 | CC7.2.1 | high | IT/Security Manager | 2026-12-31 |
| Least-Privilege Role Review Not Yet Implemented | C-08 | CC6.3.3 | high | Engineering Manager | 2027-01-31 |

## RequirementAssessment Updates — The Worst-Case-Wins Rule

Two of the 12 points-of-focus linked to our controls in Stage 3 are shared by controls with *different* individual outcomes — but `RequirementAssessment.result` is a single field per row, not one per linked control. Rule applied, explicitly rather than picked ad hoc: **the shared RequirementAssessment takes the most severe result among its linked controls** (a SOC 2 requirement is only as satisfied as its weakest supporting control), with an `observation` note explaining the split.

| Point of focus | Linked controls | Result | Extended Result |
|---|---|---|---|
| CC6.1.4 | C-01 | partially_compliant | observation_sensitive_point |
| CC6.2.1 | C-02, C-09 | partially_compliant | minor_nonconformity |
| **CC6.2.3** | C-02, **C-03**, C-09 | **non_compliant** | **major_nonconformity** *(driven by C-03)* |
| CC6.3.2 | C-03 | non_compliant | major_nonconformity |
| **CC6.3.4** | C-04, **C-08** | **non_compliant** | **major_nonconformity** *(driven by C-08)* |
| CC6.1.9 | C-05 | partially_compliant | minor_nonconformity |
| CC7.2.1 | C-06 | non_compliant | major_nonconformity |
| CC7.2.3 | C-06 | non_compliant | major_nonconformity |
| CC9.2.2 | C-07 | partially_compliant | minor_nonconformity |
| CC9.2.3 | C-07 | partially_compliant | minor_nonconformity |
| CC6.3.3 | C-08 | non_compliant | major_nonconformity |
| CC6.2.2 | C-10 | partially_compliant | minor_nonconformity |

**Final tally, confirmed via fresh `GET` after all 12 PATCH requests: 6 non_compliant / 6 partially_compliant.** This does not match "3 non_compliant controls" 1:1 — it's a real consequence of the many-to-one structure (CC6.2.3 and CC6.3.4 each get pulled up by their most severe linked control), not a rounding choice.

## Data Integrity Finding — See Stage 3 Notes

A data-generation bug (one employee, EMP-0190, with a `term_date` after `AS_OF`) was discovered while verifying evidence for the C-03 Finding above — i.e., during **this** stage's work, even though the affected file (`data/identity_inventory.csv`) and the generator script it come from (`data/generate_inventory.py`) are Stage 1 artifacts. Full details — root cause, the fix applied, and why the committed CSV was deliberately not regenerated — are documented in the **"Data Integrity Finding" section of `docs/stage3-deployment-notes.md`**, rather than duplicated here.
