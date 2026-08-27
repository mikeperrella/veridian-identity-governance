# Risk Methodology

This document explains, in plain language, how every risk in `risk-register/risk-register.csv` is scored. The goal is a scoring model simple enough to compute by hand for a scaffolded register, but precise enough that a script can reproduce the exact same numbers later (Stage 5 automates this recalculation).

## 1. Likelihood and Impact

Each risk is rated on two 1-5 scales:

**Likelihood** — how probable is it that this risk materializes, given Veridian's current controls-in-progress state?

| Score | Label | Meaning |
|---|---|---|
| 1 | Rare | Would require multiple simultaneous failures |
| 2 | Unlikely | Possible but no known precedent at Veridian |
| 3 | Possible | Plausible given current gaps; could happen |
| 4 | Likely | Expected to occur without intervention |
| 5 | Almost Certain | Already occurring or occurring imminently |

**Impact** — how severe is the consequence if it does?

| Score | Label | Meaning |
|---|---|---|
| 1 | Negligible | No meaningful business or customer impact |
| 2 | Minor | Localized, easily contained |
| 3 | Moderate | Noticeable operational or customer impact |
| 4 | Major | Significant customer-data or compliance impact |
| 5 | Severe | Breach-level exposure, SOC 2 attestation at risk, or major customer loss |

## 2. Inherent Risk

**Inherent Risk = Likelihood × Impact**, before crediting any existing control.

Range: 1-25, banded as:

| Band | Score Range |
|---|---|
| Low | 1-6 |
| Medium | 7-12 |
| High | 13-19 |
| Critical | 20-25 |

## 3. Control Effectiveness

Each risk's existing control(s) are rated for how much they actually reduce the risk in practice — not how well-designed they look on paper:

| Rating | Reduction Applied |
|---|---|
| Ineffective | 0% |
| Limited | 25% |
| Partial | 50% |
| Substantial | 75% |
| Effective | 90% |

## 4. Residual Risk

**Residual Risk = round(Inherent Risk × (1 − Control Effectiveness))**

The result is re-banded using the same Low/Medium/High/Critical thresholds from Section 2. This is the number that actually drives prioritization and treatment decisions — inherent risk alone is not actionable, since it ignores what's already in place.

## 4a. Mapping Residual Risk into CISO Assistant's Independent Likelihood/Impact Indices

CISO Assistant's RiskScenario model requires residual risk to be expressed as two independent index values (`residual_proba`, `residual_impact`), not the single combined score this document uses. Section 4's formula reduces one combined score and cannot be split into two independent factors by applying the same percentage to both: since Inherent = Likelihood × Impact, reducing *both* factors by the same fraction `f = (1 − effectiveness)` reduces the implied product by `f²`, not `f`. A documented 25% reduction (`f = 0.75`) would behave like a `1 − 0.75² ≈ 44%` reduction if applied to both factors — silently overstating every control's effectiveness.

Instead, `scripts/risk_scoring.py` reduces **only the Likelihood index**, floored to the nearest valid matrix index; **Impact is left unchanged at its inherent value**. Rationale: every control in this catalog (MFA, JML, quarterly UAR, least-privilege review, session logging, vendor access review) is a **preventive access-governance control** — its function is to reduce the probability that unauthorized access occurs, not to reduce the severity of what's exposed once it does. Impact is a property of the data or system being protected (client matter data, SOC 2 exposure), not something an access control changes.

This mapping is a best-effort representation inside CISO Assistant's data model and will not always reproduce the same band as this document's `residual_risk`/`residual_risk_band` (the two systems use different formulas by necessity — CISO Assistant's risk matrix is a hand-authored, non-linear grid lookup, not a multiplicative formula). This document's `residual_risk` and `residual_risk_band` columns in `risk-register/risk-register.csv` remain the **authoritative** residual-risk record for this project, per the limitation already documented in `docs/stage3-deployment-notes.md`.

## 5. Treatment

Every risk is assigned exactly one treatment:

- **Mitigate** — invest in additional or improved controls to reduce likelihood or impact.
- **Accept** — the residual risk is tolerable as-is, given a documented rationale.
- **Transfer** — shift financial or operational exposure elsewhere (e.g., insurance, contractual indemnification with a vendor).
- **Avoid** — eliminate the underlying activity or exposure entirely.

Every treatment decision requires a written rationale, a named owner, and a due date. "No action, no explanation" is not a valid state for any risk in this register.

## 6. Risk Acceptance Requirements

A risk may only be marked **Accept** if all three of the following are present:

1. A named **compensating control** — what is actually reducing exposure while the risk sits in accepted state.
2. An explicit **expiry date** — acceptance is time-bound, not indefinite.
3. An **escalation path** — who is notified and what happens if the acceptance lapses without re-review.

No high-residual risk is closed or accepted silently. Every Accept decision leaves a visible, dated trail in the register.
