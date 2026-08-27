# VIGCAP — Veridian Identity Governance & Continuous Assurance Program

**Repo:** `github.com/mikeperrella/veridian-identity-governance`
**Purpose:** Second flagship cybersecurity portfolio project, GRC-focused. Complements `aegis-triage` (agentic SOC/AI security) by occupying distinct territory: governance, risk, and compliance judgment centered on identity governance.
**Builder:** Michael Perrella, built in Cursor with Claude Code, using Claude API credits.
**Status:** Not yet started. This file is the complete spec — build phase-by-phase against the roadmap in Section 9, with Claude (chat) verifying each stage's Definition of Done before moving to the next, same process used for `aegis-triage`.

---

## 0. Non-Negotiables

These override any other instruction in this file if they ever conflict:

1. **$0 required cost.** Free tools, free tiers, self-hosted, or open-source only. Anything that could ask for a card or risk a surprise charge gets flagged explicitly before use.
2. **100% synthetic data and organization.** Veridian LegalTech does not exist. Every dataset, employee, vendor, and finding is fabricated. The synthetic-data disclaimer must appear in the root README and cannot be buried.
3. **No fabricated outcomes.** Every metric in the README/resume must be calculable from data actually generated in this repo. Do not write a percentage before the data that produces it exists.
4. **No exaggerated claims.** This is a portfolio simulation, not real audit experience. Never imply otherwise in copy, comments, or commit messages.
5. **Distinct from `aegis-triage`.** Different visual identity, different stack for the dashboard (Streamlit, not Next.js), different subject matter (governance/compliance judgment, not agentic threat response). If a design or content choice starts to converge with the other project, stop and change it.
6. **Risk register and control rationale content is Mike's, not generated wholesale.** See Section 8 — this repo scaffolds structure and a first pass; the actual "why we accepted this risk" / "why this control is sufficient" reasoning gets rewritten by Mike before a stage is marked done. This is a build gate, not a suggestion.

---

## 1. Company Scenario — Veridian LegalTech

Fictional B2B SaaS provider of AI-assisted document automation, e-discovery support, and matter management for mid-size US law firms. Subscription + usage revenue model.

- **Size:** ~180 employees (grew from ~90 in 18 months), ~220 active customer tenants.
- **Tech stack:** AWS (multi-account, EKS, S3, RDS), Okta as IdP (SSO + MFA enforced for most apps), Next.js frontend, assorted SaaS (Slack, Notion, Stripe, Salesforce, GitHub).
- **Data sensitivity:** Customer client PII, matter metadata, contracts — high confidentiality given the law-firm customer base.
- **Identity architecture:** Okta plus some local app roles. Rapid hiring created access sprawl: shared service accounts, incomplete offboarding, inconsistent privileged-access reviews.
- **Compliance drivers:** Enterprise law-firm customers require SOC 2 Type II before signing. Internal interest in NIST CSF alignment. No formal ISMS yet.
- **Current GRC maturity:** Ad-hoc policies, no formal risk register, UARs performed irregularly, evidence scattered across tickets/email, high residual risk on logical access (SOC 2 CC6).
- **Risk appetite:** Low for customer-data exposure and privilege abuse; medium for operational availability.
- **Business consequences tied to the problems:** incomplete UARs on high-privilege roles risk unauthorized access to client matters; excess vendor access creates a third-party pathway into the same data; missing evidence blocks SOC 2 Type II, which blocks enterprise deals; no residual-risk tracking means leadership can't prioritize remediation.

State this scenario plainly and prominently as fictional everywhere it appears (README, dashboard footer, repo description).

---

## 2. Architecture

```
Okta / HRIS (synthetic exports)
        │
        ▼
CISO Assistant (Docker, self-hosted)  ◄──── system of record
  - assets, risks, controls, framework mappings (SOC 2, NIST CSF)
  - REST API (free in Community Edition, PAT auth)
        │
        │  HTTP Request node (n8n), PAT in header
        ▼
n8n (self-hosted, Docker)
  - simulated UAR cycle: generate review list → notify owners → collect
    attestation → update status in CISO Assistant → escalate overdue
        │
        │  CISO Assistant REST API (read)
        ▼
Streamlit dashboard (streamlit-facade theme)
  - executive view: residual risk heat map, control effectiveness %,
    open/overdue findings, % high-priv accounts current on review,
    trend line pre/post remediation
```

**Correction from earlier research:** there is no prebuilt n8n node for CISO Assistant (a cited package name did not check out on npm/GitHub). The automation is n8n's standard **HTTP Request node** authenticated with a **Personal Access Token** (Settings → Personal Access Tokens → Create Token in CISO Assistant's Community Edition — confirmed free, not Pro-gated). This is the normal integration pattern and a better interview story than an installed connector: it demonstrates you can integrate with a real platform's API directly.

**Update (Stage 5):** the above is now out of date. `n8n-nodes-ciso-assistant` (npm, MIT license, published by `intuitem`, source at `github.com/intuitem/n8n-nodes-ciso-assistant`) is a real, actively maintained community node — confirmed by downloading and inspecting the actual npm tarball, not just the registry listing page. It supports full CRUD across 26 CISO Assistant resources, including `riskScenario`, `finding`, `findingsAssessment`, `appliedControl`, and `user`; `requirementAssessment` supports `get`/`getAll`/`update` only, which is correct since CISO Assistant auto-generates those rows per requirement node rather than letting clients create or delete them. Auth is the same `Authorization: Token <PAT>` header already used since Stage 3. Used for the Stage 5 n8n workflow instead of the plain HTTP Request node.

Note: a *different*, unpublished, AGPL-licensed node also exists, bundled inside the `ciso-assistant-community` repo itself at `automation/n8n/n8n-nodes-ca/` — it is missing `requirementAssessment`/`user` support entirely and requires a manual Docker volume-mount rather than a normal npm install. That is **not** the package used here; confirm by checking the installed package's `package.json` (`license: MIT`, `version: 0.1.x`) or its file path (`dist/nodes/CisoAssistant/...`), not just the name.

**Supply-chain note:** n8n community nodes run unsandboxed with the same access as n8n itself — no isolation between node code and n8n's credential store. A real campaign in January 2026 exploited exactly this: malicious lookalike packages (e.g. `n8n-nodes-hfgjf-irtuinvcm-lasdqewriit`, posing as a Google Ads integration) exfiltrated decrypted OAuth tokens and API keys during workflow execution (reported by The Hacker News, CSO Online, Endor Labs, Rescana). Using `n8n-nodes-ciso-assistant` here is a provenance judgment — published under the `intuitem` npm account, MIT-licensed, traceable to the platform's own GitHub org — not a claim that community nodes are safe in general.

**Why not Eramba:** its Community-edition API access is inconsistent/effectively unreliable in practice per practitioner reports, even though marketing copy suggests otherwise. CISO Assistant's API is confirmed unrestricted in Community Edition. Not using Eramba.

**Why a separate Streamlit dashboard when CISO Assistant has native reporting:** CISO Assistant's built-in reporting is operational (internal, ticket-style views). The Streamlit piece is the polished, portfolio-facing executive artifact — and demonstrates independent Python/data skill distinct from configuring someone else's platform.

---

## 3. Tech Stack

| Component | Tool | Free? | Notes |
|---|---|---|---|
| GRC system of record | CISO Assistant Community Edition (Docker) | Yes | AGPL v3, Django/SvelteKit/PostgreSQL/Redis, API-first, ~4,000 GitHub stars, actively maintained (v3.15.9 as of Apr 2026) |
| Automation | n8n (self-hosted, Docker) | Yes | HTTP Request node + PAT against CISO Assistant's API — no community node needed |
| Dashboard | Python + Streamlit + `streamlit-facade` | Yes | `pip install streamlit-facade`; themeable, no Node dependency, avoids the streamlit-shadcn-ui look (too close to `aegis-triage`) |
| Risk scoring | Python + pandas | Yes | Local script, recalculates residual risk, flags overdue |
| Data | Synthetic CSV/JSON, SQLite where needed | Yes | |
| Version control | GitHub | Yes | |
| Diagrams | Mermaid (renders natively in GitHub markdown) | Yes | |

**Docker resource note:** CISO Assistant's minimum viable footprint is ~1 vCPU / 8GB RAM. Running CISO Assistant + n8n + Streamlit simultaneously will strain a laptop already running Cursor. Default to starting only what the current build session needs (`docker compose stop` the rest) rather than leaving all three up continuously.

**Known Docker setup friction to expect (from verified research, not guaranteed exhaustive):**
- Requires Docker Compose V2 / Docker Engine ≥27 — the legacy `docker-compose` binary will fail.
- First `docker compose up -d` can race the Postgres container's init; if the health check fails, run it again and check `docker compose logs backend` for completed migrations before concluding something's actually broken.
- The interactive superuser-creation prompt in `./docker-compose.sh` sometimes doesn't render; fallback is `docker compose exec backend poetry run python manage.py createsuperuser`.
- Caddy (the bundled reverse proxy) requires a real FQDN for TLS/SNI — accessing via bare `127.0.0.1` will fail. Add a local hosts-file entry (e.g., `ciso-assistant.local`) and update `CISO_ASSISTANT_URL` accordingly.
- Frontend body size limit defaults to 20MB (`BODY_SIZE_LIMIT`) — raise it if uploading larger synthetic evidence files.
- Windows: use Docker Desktop + WSL2 (Ubuntu), not native Windows — native is explicitly experimental per the project's own docs.

---

## 4. Design Direction — Dashboard

The subject is a compliance/audit register, not a SOC alert feed — lean into that vernacular (ledgers, registers, attestations, stamps of approval) rather than reaching for `aegis-triage`'s presumed dark/terminal SOC look. Avoid the three current AI-design defaults (warm cream + terracotta; near-black + acid accent; zero-radius newspaper broadsheet) — none of them are wrong per se, they're just not a *choice* for this brief.

**Token system:**
- **Palette:** cool pale slate-white background `#F2F3F5` (not warm cream), deep indigo-ink `#161B2E` for text/structure, aged-brass accent `#B08D57` for verified/passed states, deep garnet `#7A2E2E` for high-risk/deficiency, muted amber `#C08A2E` for medium-risk, deep muted slate-green `#3F6B4F` for low-risk/on-track.
- **Type:** a serif with real gravitas for headers (e.g. Fraunces or Source Serif 4) — evokes a charter/formal-document register — paired with IBM Plex Sans for body copy and IBM Plex Mono for control/risk IDs and data (ties the family together, reads as ledger entry codes).
- **Signature element:** a "review stamp" component for pass/fail/deficiency status — bordered, slightly rotated, brass or garnet ink — standing in for a literal audit stamp rather than a generic colored badge pill. This is the one place to spend visual boldness; keep the rest of the dashboard quiet and disciplined.
- **Layout:** a persistent left-hand rail listing control/risk ID codes (docket-style), main panel styled as structured workpapers, hairline dividers only where they encode real sequence (e.g., a findings timeline) — not decoratively.

Build to a quality floor: responsive, visible keyboard focus, no unnecessary motion. This direction is a starting point, not a locked spec — if it stops fitting once real data is in front of you, revise it and note why.

---

## 5. GRC Framework Mapping

- **Primary: SOC 2 Trust Services Criteria, CC6 (Logical and Physical Access Controls)** — Veridian's enterprise law-firm customers require SOC 2, and CC6 is where identity governance lives.
- **Secondary structure: NIST CSF 2.0** (Govern/Protect/Identify functions) plus relevant NIST 800-53 families (AC, AU, IA) for control language, informed by 800-30 risk-methodology principles.
- No kitchen-sink multi-framework mapping. Controls are designed once and shown to satisfy both where they genuinely overlap — state the overlap explicitly rather than mapping twice for volume.

---

## 6. Risk Methodology

- Qualitative matrix: Likelihood (1–5) × Impact (1–5) = Inherent Risk.
- Document existing controls and an effectiveness rating for each.
- Residual Risk = Inherent Risk adjusted by control effectiveness.
- Treatment options: **Mitigate / Accept / Transfer / Avoid** — every choice needs a written rationale, an owner, and a due date.
- Risk acceptance requires a compensating control, an explicit expiry date, and an escalation path if it lapses.
- Every high-residual risk needs a visible decision trail: nothing gets "accepted" silently.
- Populate 12–20 identity-and-access-related risks initially (JML gaps, shared service accounts, incomplete offboarding, excess vendor access, privileged session logging gaps, etc.) — scaffolded per Section 8, then rewritten in Mike's own words.

---

## 7. Control Framework & Testing

Access-focused control set: MFA enforcement, quarterly UAR for privileged roles, JML process, privileged session logging, vendor access review, least-privilege role design.

Each control needs: objective, owner, implementation status, frequency, evidence required, test procedure, expected vs. actual result, pass/fail, deficiency severity if failed.

Test a representative sample (8–12 controls) and document exactly as an auditor would expect to see it — this is the artifact that separates the project from a checklist.

---

## 8. Content Ownership Workflow — Build Gate

This governs how the risk register, control rationale, and treatment decisions get written. It is a required stage in the roadmap (Section 9, Stage 2 sign-off), not optional polish.

1. **Scaffold pass (Claude Code):** generate the risk register and control catalog structure — IDs, categories, likelihood/impact fields, control mappings — plus a first-draft rationale for each, clearly labeled as a draft.
2. **Rewrite pass (Mike):** every "why we accepted this risk," "why this control is sufficient," "why this treatment over another" line gets rewritten in Mike's own words before that stage is marked done. The structure and mechanics can stay generated; the judgment calls cannot.
3. **Gate:** a stage isn't complete until the rewrite pass is done. This exists because the interview value of this whole project depends on being able to defend the reasoning under a follow-up question — reasoning you didn't actually write is much harder to defend under pressure.

---

## 9. Environment Setup

Run once at the start of the build, inside the actual project directory in Cursor (these commands run on Mike's machine via Claude Code, not from this spec alone):

```bash
# Dashboard component library
pip install streamlit-facade

# agency-agents — Design + relevant Engineering/Security/Specialized/Testing/Support agents only,
# not the full 200+ roster
./scripts/install.sh --tool claude-code --agent \
  ui-designer,ux-architect,ui-finish-gate-reviewer,\
data-visualization-engineer,identity-access-engineer,\
compliance-auditor,automation-governance-architect,\
document-generator,api-tester,executive-summary-generator
# (also run --tool cursor with the same --agent list so Cursor gets them too)

# Karpathy behavioral guidelines plugin
curl -o CLAUDE_KARPATHY.md https://raw.githubusercontent.com/multica-ai/andrej-karpathy-skills/main/CLAUDE.md
echo "" >> CLAUDE.md && cat CLAUDE_KARPATHY.md >> CLAUDE.md && rm CLAUDE_KARPATHY.md
```

Verify the agent list against the installer's current roster before running (`./scripts/install.sh --list teams`) — agent names/paths may have shifted since this was written.

---

## 10. Build Roadmap

Same phase-gate process as `aegis-triage`: each stage has a Definition of Done, verified independently before moving on. No fixed deadline — build it right.

**Stage 1 — Foundation**
- Company profile, identity/asset inventory (synthetic), risk methodology doc.
- Initial risk register (scaffolded per Section 8).
- *DoD:* inventories exist as structured data (CSV/JSON), risk methodology doc explains the scoring model in plain language, 12–20 risks logged with inherent scores.

**Stage 2 — Framework & Controls**
- SOC 2 CC6 + NIST CSF justification write-up.
- Control catalog (owners, frequency, evidence requirements, test procedures).
- Content ownership gate (Section 8) passed for this stage's rationale.
- *DoD:* every control has all required fields populated; rationale is in Mike's own words, not the scaffolded draft.

**Stage 3 — Platform Deployment**
- CISO Assistant running locally via Docker; frameworks, assets, risks, controls loaded.
- PAT generated, API access confirmed with a simple authenticated GET request.
- *DoD:* CISO Assistant UI is reachable and populated; an API call from outside the UI (curl or Python) successfully returns data.

**Stage 4 — Control Testing & Findings**
- Execute the 8–12 sample control tests, document pass/fail/deficiency.
- Findings log with root cause, business impact, remediation plan, owner, due date; some findings closed with validation evidence.
- *DoD:* every tested control has a documented result; at least one finding shows a full open-to-closed lifecycle.

**Stage 5 — Automation**
- n8n workflow: generate UAR review list → notify → collect attestation → update CISO Assistant via API → escalate overdue.
- Python risk-scoring script: recalculates residual risk, flags overdue items.
- *DoD:* running the n8n workflow against synthetic data visibly changes a record in CISO Assistant (not just logs a step); the scoring script produces the same numbers on a re-run (deterministic, no silent randomness).

**Stage 6 — Dashboard**
- Streamlit app with the design direction from Section 4: heat map, control effectiveness %, open/overdue findings, % high-priv accounts reviewed, trend line.
- Pulls live from CISO Assistant's API, not a static snapshot, where practical.
- *DoD:* dashboard runs locally, renders real data from Stages 1–5, matches the design direction (not default Streamlit widgets).

**Stage 7 — Evidence, Polish, Resume**
- Evidence pack samples, architecture diagram (Mermaid), decision log, full README with synthetic-data disclaimer.
- Calculate real metrics from the data actually generated (never write a number before the data exists).
- Resume bullets (X-Y-Z format, only claims the repo can back up), LinkedIn/GitHub description.
- Interview prep: 30-second / 60-second / 2-minute explanations, likely questions with honest answers grounded in what was actually built.
- Final credibility audit (Section 11).
- *DoD:* every number in the README traces to a file in the repo; nothing in the resume bullets is unverifiable from the public repo.

---

## 11. Final Credibility Audit — run before calling this done

- Does anything look templated or AI-generated rather than reasoned through?
- Are the controls generic, or specific to Veridian's actual context (client-matter data sensitivity, rapid growth, law-firm customer base)?
- Are the metrics real (calculated from this repo's data) or invented?
- Could every component be defended under a specific follow-up question in an interview?
- Is the synthetic-data disclaimer prominent, not buried?
- Does it look different enough from `aegis-triage` (visually and substantively) to read as range rather than a repeat?

If any answer is no, fix it before considering the project finished.

# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
