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
