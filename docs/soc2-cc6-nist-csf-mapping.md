# Framework Justification — SOC 2 CC6 & NIST CSF 2.0

Per `CLAUDE.md` Section 5, this project maps to one primary framework and one secondary structure — deliberately, not a kitchen-sink mapping across every framework that might plausibly apply. This document states which parts of each framework are in scope, which are explicitly out of scope, and where the two frameworks are describing the same underlying control objective.

## Why SOC 2 CC6 Is Primary

Veridian's enterprise law-firm customers require a SOC 2 Type II report before signing (`docs/company-profile.md`, Compliance Drivers). Within the SOC 2 Trust Services Criteria, **CC6 — Logical and Physical Access Controls** is where identity governance lives: who has access, how it's granted and removed, and how privileged access is controlled. That is the subject of this entire repository, so CC6 is the framework this project is built to satisfy.

### In Scope

| Sub-Criterion | What It Covers | Where It Shows Up Here |
|---|---|---|
| **CC6.1** | Logical access security measures (authentication, authorization) protect against unauthorized access | Nearly every control in `controls/control-catalog.csv` — MFA, JML, least privilege, orphaned-account reconciliation |
| **CC6.2** | Prior to issuing credentials, users are registered and authorized; access is removed when no longer needed | C-02 (JML), C-03 (offboarding), C-09 (contractor lifecycle), C-10 (orphaned accounts) |
| **CC6.3** | Role-based access, least privilege, and periodic review of access and segregation of duties | C-04 (UAR), C-06 (session logging), C-08 (least-privilege role design) |

### Explicitly Out of Scope

Named here rather than silently omitted, per Section 5's instruction to state overlap (and gaps) explicitly:

| Sub-Criterion | What It Covers | Why It's Out of Scope |
|---|---|---|
| **CC6.4** | Physical access controls to facilities and hardware | Veridian is cloud-native (AWS); physical security is inherited from AWS's own SOC 2 report, not something Veridian's identity governance program controls directly |
| **CC6.6** | Boundary protection (firewalls, network segmentation) | Network security architecture, not identity/access governance — a distinct control domain |
| **CC6.7** | Restricts transmission and movement of information (encryption in transit/at rest) | Data protection engineering concern, not identity governance |
| **CC6.8** | Prevents or detects unauthorized/malicious software | Endpoint/malware defense, unrelated to who has access to what |

## Why NIST CSF 2.0 Is Secondary

There is internal interest in aligning with NIST CSF 2.0 (`docs/company-profile.md`, Compliance Drivers), but no customer is requiring it and no formal ISMS exists yet. CSF 2.0 is used here as a secondary structure layered onto the same controls — not a parallel mapping exercise done for its own sake.

The relevant CSF 2.0 categories:

- **PR.AA — Identity Management, Authentication, and Access Control** (Protect function). This is the CSF 2.0 category that replaced the older CSF 1.1 "PR.AC" (Access Control) category — this project uses CSF 2.0 terminology consistently, including in `risk-register/risk-register.csv`'s `framework_mapping` column. `PR.AA` is the direct secondary-framework equivalent of SOC 2 CC6 for this project's purposes.
- **GV.RM / GV.SC / GV.OV** (Govern function) — risk management strategy, supply chain/third-party risk, and organizational oversight. Used only where a risk or control is genuinely about governance process (e.g., vendor access review, evidence collection) rather than access control mechanics.
- **PR.PS — Platform Security** (Protect function) — used specifically for the privileged session logging control, which is about platform-level audit logging rather than access control per se.
- **PR.DS — Data Security** (Protect function) — used for the one control catalog item that touches data-layer protection (tenant isolation) rather than identity access.

CSF categories that don't map to anything in this project's scope (e.g., `RS` Respond, `RC` Recover, `ID.AM` outside of what's already covered by the asset inventory) are simply not referenced — they're not relevant to an identity-governance-focused project and forcing a mapping would be exactly the kind of kitchen-sink exercise Section 5 warns against.

## Where CC6 and PR.AA Overlap

In practice, SOC 2 **CC6** and NIST CSF 2.0 **PR.AA** are describing the same control objective — "manage who has access to what, and prove it" — from two different framework vocabularies aimed at two different audiences (an external auditor for SOC 2, an internal risk-management structure for CSF). Every control in `controls/control-catalog.csv` is designed once against the access-governance problem it's meant to solve, and its `framework_mapping` column shows both the SOC 2 and CSF citation for the same control — it is not designed twice, once per framework.
