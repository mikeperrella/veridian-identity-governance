# Stage 3 — Platform Deployment Notes

Documents how CISO Assistant Community Edition was deployed and verified for this project. No secrets (tokens, passwords) appear anywhere in this file — see the note at the bottom on where those actually live.

## Environment

- **Docker Engine:** 29.7.2 (well above the ≥27 minimum CISO Assistant requires)
- **Docker Compose:** v5.4.0, invoked as the `docker compose` CLI plugin (Compose V2) — the legacy standalone `docker-compose` binary that also ships with Docker Desktop was deliberately not used
- **Host OS:** Windows 11, via Docker Desktop's WSL2 backend (`Ubuntu` as the default WSL distro), per CLAUDE.md's guidance to avoid Docker Desktop's experimental native-Windows mode

## Memory

Pre-flight check found only ~3.59GB of the host's 15.71GB RAM free at the time (Cursor and other apps were running), against CISO Assistant's documented ~8GB minimum footprint. This was flagged as a risk before deployment; the decision was made to proceed and monitor rather than pre-emptively close applications. In practice, the stack came up and passed its health checks with no observed memory-related failures (no OOM kills, no container thrashing) — the risk did not materialize into an actual incident.

## Hostname / TLS — Correction from CLAUDE.md's Original Research

CLAUDE.md anticipated needing a custom hosts-file entry (`ciso-assistant.local -> 127.0.0.1`) because Caddy requires a real FQDN for TLS/SNI, not a bare IP address. In practice, **no hosts-file entry was added.** The cloned repo's current default `docker-compose.yml` sets `CISO_ASSISTANT_URL=https://localhost:8443`, and `localhost` is itself a valid hostname (not an IP literal), which already satisfies Caddy's SNI requirement. The hosts-file problem CLAUDE.md described only applies if the URL is set to a bare IP address — it wasn't necessary here. This is a correction to CLAUDE.md's research, the same category as the earlier n8n-integration-node correction already documented there.

## Deployment

1. Cloned CISO Assistant Community Edition to a sibling directory, `C:\Users\miker\ciso-assistant-community` — deliberately outside this repo, the same pattern used for the `agency-agents` clone in Stage 0 setup.
2. Started Docker Desktop and confirmed the engine was responsive (`docker info`) before proceeding.
3. Pulled all four images defined in `docker-compose.yml` (`backend`, `frontend`, `caddy`, `qdrant`) via `docker compose pull`.
4. Brought the stack up with `docker compose up -d` directly, rather than the repo's `docker-compose.ps1`/`docker-compose.sh` wrapper scripts — those wrappers end in an interactive `createsuperuser` prompt, which doesn't render through this session's non-interactive shell.
5. Backend took several minutes to report healthy on first boot — its startup seeds the full built-in framework library (SOC 2, ISO 27001, NIST CSF, TISAX, DORA, and dozens of others) into the database before the health check passes. This is expected first-run behavior, not a failure.
6. **Superuser creation was non-interactive**, using Django's `createsuperuser --noinput` with the email and password supplied via environment variables passed to `docker compose exec`, since the interactive prompt path (as CLAUDE.md anticipated for a different but related reason) doesn't work in this environment.

## Verification

- **UI reachability:** `https://localhost:8443/` returns an HTTP 302 redirect to `/login?next=/`, which itself returns HTTP 200 — confirmed via `curl -sk -L`.
- **API access:** An authenticated GET request was made from outside the UI:
  ```
  curl -sk -H "Authorization: Token <PAT>" https://localhost:8443/api/folders/
  ```
  (Per the repo's own documentation, CISO Assistant's PAT auth uses the `Token` scheme, not `Bearer`.)

  Response: HTTP 200, with a real JSON body:
  ```json
  {"count":1,"next":null,"previous":null,"results":[{"id":"dc7cd9f8-d1f1-42a5-8dc2-6e2264cd432b","path":[],"parent_folder":null,"filtering_labels":[],"content_type":"GLOBAL","created_at":"2026-08-26T19:21:34.948483Z","updated_at":"2026-08-26T19:21:34.948501Z","is_published":true,"name":"Global","description":null,"builtin":true,"create_iam_groups":true}]}
  ```
  This is CISO Assistant's built-in "Global" folder, created automatically on first initialization.

This satisfies Stage 3's Definition of Done: the UI is reachable, and an authenticated API call from outside the UI returns real data.

## Scope Note

The initial pass covered deployment and verification only. Importing the actual Veridian risk register, control catalog, and identity/asset inventory into CISO Assistant ("populated," per the fuller reading of Stage 3's DoD) followed as a distinct task — see below for the asset import; the risk register and control catalog import are still outstanding as of this writing.

## Asset Import — PR/SP Typing Criterion

The 15 rows in `data/asset_inventory.csv` were imported via `POST /api/assets/`. CISO Assistant's `Asset.type` field only accepts two values, `PR` (Primary) or `SP` (Supporting) — this is EBIOS RM terminology, where a **Primary asset** is meant to be an abstract business asset (a business process or a piece of information with inherent value — e.g., "client matter data" as a concept) and a **Supporting asset** is the technical/organizational component that carries it (a server, an application, a network).

That strict EBIOS RM distinction was **not** the criterion actually used here. Every row in our inventory is itself a piece of infrastructure or a SaaS tool (Okta, an S3 bucket, GitHub, Salesforce), not an abstract business asset — under strict EBIOS RM semantics, essentially all 15 would be classified as Supporting assets, since none of them *are* "client matter data," they only *carry* it. Typing them all `SP` would have made the field meaningless (uniform, no signal), so instead each asset was typed by a simpler, explicit criterion:

- **PR** — customer-facing and/or production-critical to Veridian's actual product (e.g., the production EKS cluster, the client-document S3 bucket, the Next.js frontend, Stripe billing)
- **SP** — internal tooling not part of the customer-facing production path (e.g., Okta, GitHub, Slack, Notion, Salesforce, the HRIS platform)

Result: 7 assets typed `PR`, 8 typed `SP`.

**Flag for later:** if this asset data ever feeds a real EBIOS RM study in CISO Assistant (the platform has dedicated EBIOS RM workflow support), this typing will need to be redone under the strict EBIOS RM definition — the business-criticality criterion used here is a reasonable stand-in for a first import, not a substitute for actual EBIOS RM asset modeling.

`data_sensitivity` (a column in our CSV with no equivalent field on CISO Assistant's Asset object) was preserved by prepending `Data sensitivity: <value>.` to each asset's `description` field, ahead of the original CSV notes text — not silently dropped.

## Risk Import — `current_proba`/`current_impact` Limitation

CISO Assistant's RiskScenario tracks three independent probability/impact pairs — inherent, current (with existing measures), and residual (with planned/extra measures) — each as separate likelihood and impact indices. Our own methodology only reduces a single **combined** `inherent_risk` score (`Likelihood × Impact`) by a control-effectiveness percentage to get `residual_risk`; it never adjusts likelihood and impact independently. There is no principled way to reverse-engineer separate current-state likelihood and impact values from a single reduced combined score without inventing an arbitrary split rule (e.g., "reduce impact first," "reduce both proportionally") that our methodology doc doesn't define and that would misrepresent the reasoning behind each risk's actual treatment.

Rather than fabricate that split, `current_proba` and `current_impact` were set **identical to `inherent_proba`/`inherent_impact` for all 16 risk scenarios**, uniformly, with no per-row exceptions. `risk-register/risk-register.csv`'s `residual_risk` and `residual_risk_band` columns remain the authoritative record of control-adjusted risk for this project — CISO Assistant's `current_level` field does not represent that adjustment for any scenario imported here.

## Risk Scenario Import

1. Created the RiskAssessment container: `name: "Veridian Identity Governance Risk Assessment 2026"`, `risk_matrix: 5a0993eb-231e-4318-94e7-d33655bb58ef` (our custom L×I matrix, confirmed live via `GET /api/risk-matrices/` before use, not hardcoded from memory).
2. Imported all 16 rows from `risk-register/risk-register.csv` as RiskScenario objects (`inherent_proba`/`inherent_impact` set from `likelihood`/`impact` minus 1; `current_proba`/`current_impact` identical to inherent per the limitation above; `existing_controls`, `treatment`, `justification`, and `ref_id` carried over directly).
3. Verified via `GET /api/risk-scenarios/`: **count = 16**.

**Independent spot-check** — 3 scenarios fetched individually via `GET /api/risk-scenarios/{id}/` and compared against a separate re-read of `risk-register.csv` (not the values used at creation time), confirming CISO Assistant's own grid lookup — not just the matrix being loaded — actually reproduces our methodology:

| risk_id | L×I | Our methodology band | CISO Assistant `inherent_level` | Match |
|---|---|---|---|---|
| R-001 | 4×4=16 | High | High (Likely × Major → High) | Yes |
| R-002 | 4×5=20 | Critical | Critical (Likely × Severe → Critical) | Yes |
| R-015 | 4×4=16 | High | High (Likely × Major → High) | Yes |

All three matched exactly. The API response for each scenario also echoed back the matched level's `description` field verbatim as `"<Band> risk band, per docs/risk-methodology.md"` — the text baked into our custom matrix's own definition — confirming the level came from our matrix, not a built-in one that happened to agree.

`residual_proba`, `residual_impact`, and `residual_level` correctly show as unrated (`value: -1`, `name: "--"`) on every scenario, consistent with the current/residual limitation documented above — those fields were never set for any of the 16 imports.

## Applied Control Import

Imported all 10 rows from `controls/control-catalog.csv` as AppliedControl objects via `POST /api/applied-controls/`. Verified via `GET /api/applied-controls/`: **count = 10**. `category` was inferred per control from its `frequency` column value (continuous/system-enforced → `technical`; per-event-triggered → `procedure`; calendar-cadence recurring review → `process`); `csf_function` was sourced directly from each control's existing NIST CSF citation in `framework_mapping` (all 10 sourced, none inferred); `status` was mapped from `implementation_status` (`Partially Implemented` → `in_progress`, `Designed (not yet implemented)` → `to_do`). `reference_control` was deliberately left unset, pending the SOC 2 framework library import.

`effort` and `priority` were **intentionally left unpopulated** on all 10 controls. Neither field has a corresponding source column in `control-catalog.csv`, and assigning a T-shirt size or a 1-4 priority number now would be inventing a judgment call rather than translating existing data. Both are deferred to Stage 4 ("Control Testing & Findings"), where actual test results and deficiency severity will give a real, evidence-based basis for prioritization — rather than a speculative one assigned before any testing has occurred.

## Risk-to-Control Linking

`control-catalog.csv`'s `linked_risk_ids` column was used to link each AppliedControl to its corresponding RiskScenario(s). This relationship is writable only from the RiskScenario side (`applied_controls`, an array of control UUIDs) — AppliedControl has no reciprocal field pointing back at a risk scenario — so the link was made via `PATCH` to each risk scenario's own endpoint, not by posting anything to the control.

13 of the 16 risk scenarios received a control link; **13/13 PATCH requests succeeded**. Three controls link to two risks each, and all three multi-risk shares were confirmed correct via independent `GET` requests after submission:

- **C-02** (JML Provisioning Process) → R-001 and R-010, both showing the identical control UUID
- **C-06** (Privileged Session Logging & Break-Glass Monitoring) → R-006 and R-014
- **C-08** (Least-Privilege Role Design & Entitlement Review) → R-008 and R-011

**R-013, R-015, and R-016 correctly remain unlinked** (`applied_controls: []`) — `control-catalog.csv` never assigns any of the 10 controls to these three risks, so no PATCH was sent for them. This was confirmed directly: a fresh `GET` on R-013 after the linking pass returned an empty `applied_controls` array, not an accidental population.

## Where the Credentials Actually Live

The superuser password and the Personal Access Token generated during this session exist only in the running CISO Assistant instance and in the operator's own local notes — neither value appears in this repository, in any command output saved to the repo, or in git history.
