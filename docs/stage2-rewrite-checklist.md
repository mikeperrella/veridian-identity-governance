# Stage 2 Content-Ownership Rewrite Checklist

Per `CLAUDE.md` Section 8, every DRAFT judgment call below needs to be rewritten in Mike's own words before Stage 2 is marked done. The structure and mechanics (IDs, scores, framework mappings, owners, frequencies) stay as generated — only the reasoning gets rewritten. Once every item below is checked off, the Stage 2 content-ownership gate is closed.

## Risk Register (`risk-register/risk-register.csv`) — 16 items

- [x] **R-001** — No formal joiner-mover-leaver (JML) process — `treatment_rationale`
- [x] **R-002** — Incomplete offboarding leaves terminated employees with active access — `treatment_rationale`
- [x] **R-003** — Shared service accounts without individual ownership — `treatment_rationale`
- [ ] **R-004** — Irregular user access reviews (UARs) for privileged roles — `treatment_rationale`
- [ ] **R-005** — Excess vendor access to client data — `treatment_rationale`
- [ ] **R-006** — Privileged session logging gaps — `treatment_rationale`
- [ ] **R-007** — MFA coverage gap on legacy applications — `treatment_rationale`
- [ ] **R-008** — Role and privilege sprawl — `treatment_rationale`
- [ ] **R-009** — Orphaned accounts with no mapped active employee — `treatment_rationale`
- [ ] **R-010** — Mover events do not trigger access revocation — `treatment_rationale`
- [ ] **R-011** — Admin console over-privilege on critical SaaS/cloud platforms — `treatment_rationale`
- [ ] **R-012** — Contractor access lifecycle not tied to engagement end date — `treatment_rationale`
- [ ] **R-013** — SSO coverage gap on the legacy e-discovery application — `treatment_rationale`, `compensating_control`, `escalation_path`
- [ ] **R-014** — Break-glass emergency access lacks logging and review — `treatment_rationale`
- [ ] **R-015** — SOC 2 evidence collection is scattered and untracked — `treatment_rationale`
- [ ] **R-016** — Multi-tenant data isolation has not been independently tested — `treatment_rationale`

## Control Catalog (`controls/control-catalog.csv`) — 10 items

- [ ] **C-01** — MFA Enforcement for SSO-Integrated Applications — `control_rationale`
- [x] **C-02** — Joiner-Mover-Leaver (JML) Provisioning Process — `control_rationale`
- [x] **C-03** — Termination Deprovisioning (Offboarding) — `control_rationale`
- [ ] **C-04** — Quarterly UAR for Privileged & Admin Roles — `control_rationale`
- [x] **C-05** — Service Account Ownership & Review — `control_rationale`
- [ ] **C-06** — Privileged Session Logging & Break-Glass Monitoring — `control_rationale`
- [ ] **C-07** — Vendor / Third-Party Access Review — `control_rationale`
- [ ] **C-08** — Least-Privilege Role Design & Entitlement Review — `control_rationale`
- [ ] **C-09** — Contractor Access Lifecycle Management — `control_rationale`
- [ ] **C-10** — Orphaned Account Reconciliation — `control_rationale`

## Total

16 risk-register items + 10 control-catalog items = 26 rows with at least one DRAFT field (28 individual DRAFT-prefixed fields total).

