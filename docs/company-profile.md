# Company Profile — Veridian LegalTech

> **Synthetic data notice:** Veridian LegalTech is a fictional company. Every employee, vendor, system, dataset, and finding referenced in this repository is fabricated for the purpose of this portfolio project. No real organization, person, or incident is represented.

## Overview

Veridian LegalTech is a fictional B2B SaaS provider of AI-assisted document automation, e-discovery support, and matter management for mid-size US law firms. Revenue is a mix of subscription and usage-based billing.

## Scale & Growth

- ~180 employees, grown from ~90 over the preceding 18 months.
- ~220 active customer tenants (law firms).
- Rapid hiring has outpaced identity governance process maturity — this tension is the throughline for the risk register in this repo.

## Technology Environment

- **Cloud:** AWS, multi-account (production, staging, security/logging), EKS for container workloads, S3 for document storage, RDS for relational data.
- **Frontend:** Next.js.
- **Identity provider:** Okta — SSO and MFA enforced for most, but not all, applications.
- **Other SaaS:** Slack, Notion, Stripe, Salesforce, GitHub.

## Data Sensitivity

Veridian's customer base is law firms, so the data it processes on their behalf — client PII, matter metadata, contracts — carries high confidentiality requirements even though Veridian itself is not a law firm.

## Identity Architecture

Okta is the primary identity provider, supplemented by local application roles in systems that don't federate cleanly. Rapid hiring has produced access sprawl: shared service accounts, incomplete offboarding, and inconsistent privileged-access reviews.

## Compliance Drivers

- Enterprise law-firm customers require SOC 2 Type II attestation before signing.
- Internal interest in aligning with NIST CSF 2.0.
- No formal ISMS exists yet.

## Current GRC Maturity

- Policies are ad-hoc.
- No formal risk register existed before this project.
- User access reviews (UARs) are performed irregularly.
- Evidence of control operation is scattered across tickets and email rather than centralized.
- Residual risk on logical access controls (SOC 2 CC6) is high.

## Risk Appetite

- **Low** appetite for customer-data exposure and privilege abuse.
- **Medium** appetite for operational availability risk.

## Business Consequences

- Incomplete UARs on high-privilege roles risk unauthorized access to client matters.
- Excess vendor access creates a third-party pathway into the same sensitive data.
- Missing evidence blocks SOC 2 Type II attestation, which blocks enterprise deals.
- No residual-risk tracking means leadership cannot prioritize remediation spend.
