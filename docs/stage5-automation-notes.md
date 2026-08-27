# Stage 5 — Automation

Documents how the n8n UAR workflow and `scripts/risk_scoring.py` were built, deployed, and verified against the live CISO Assistant instance from Stage 3. No secrets appear in this file.

## n8n Deployment

`automation/n8n/Dockerfile` builds `n8nio/n8n:latest` with `n8n-nodes-ciso-assistant` installed globally as root (the real, MIT-licensed npm package — see the CLAUDE.md Stage 5 correction for how this was distinguished from the unrelated AGPL node bundled inside the `ciso-assistant-community` repo itself). `automation/n8n/docker-compose.yml` runs it as a single service, port 5678 published to `127.0.0.1` only.

**Community node registration:** `npm install -g` alone does not make n8n load the package — n8n only scans directories named in `N8N_CUSTOM_EXTENSIONS`. Confirmed via `n8n export:nodes` (910 node types before, 912 after adding the env var). A side effect worth flagging: nodes loaded this way get re-namespaced under a `CUSTOM.` prefix rather than the package's own declared name, so the workflow JSON's node `type` fields are `"CUSTOM.cisoAssistant"`, not `"n8n-nodes-ciso-assistant.cisoAssistant"`.

**File-access restriction:** the "Read Identity Inventory" node initially failed with `NodeApiError: Access to the file is not allowed.` n8n's `SecurityConfig.restrictFileAccessTo` defaults to `~/.n8n-files`, not empty — confirmed by reading `@n8n/config`'s `security.config.js` directly, since this default isn't obvious from the error message alone. Fixed with `N8N_RESTRICT_FILE_ACCESS_TO=/data;/home/node/.n8n-files` so the mounted `data/` volume is explicitly allow-listed alongside n8n's own default.

**Reaching CISO Assistant from n8n's container:** the credential's Base URL can't be `https://localhost:8443` (that resolves to the n8n container itself, not the host) and the two stacks run as separate Docker Compose projects on separate networks, so container-name DNS doesn't cross between them by default. Rather than solve Caddy's TLS/SNI routing across an inter-project network join, n8n's compose service was attached directly to the CISO Assistant stack's network (`ciso-assistant-community_default`, referenced as `external: true`) and pointed at `http://backend:8000` — the Django container's own internal port, which Caddy itself proxies `/api/*` to. This is a supported path, not a workaround: Django's `ALLOWED_HOSTS` already includes `'backend'` alongside `'localhost'`. It also means UAR automation traffic never needs TLS at all, since it stays inside the Docker network.

**Owner account is a one-time manual step, not a persistence bug.** The workflow and credential were imported non-interactively via `n8n import:workflow` / `n8n import:credentials` specifically to avoid the interactive setup wizard (same reasoning as CISO Assistant's `createsuperuser --noinput` in Stage 3). That leaves n8n's Users table empty, so the web UI always shows "Set up owner account" on first login — this looked like the volume wasn't persisting, but the named volume (`n8n_n8n_data`) and its `database.sqlite` were confirmed intact throughout (checked via `docker volume inspect` and `n8n list:workflow`, which showed the imported workflow present the whole time). Unlike CISO Assistant, this n8n version has no non-interactive owner-creation CLI command, so completing that screen once is an unavoidable manual step, in the same category as entering the PAT into n8n's credential UI.

**Execution pattern:** the main compose-managed `n8n` container runs `n8n start` (the web UI + task broker on port 5679). Running `n8n execute --id=...` inside that same container conflicts on the task-broker port. Workflow executions for verification were instead run via a one-off `docker run --rm --entrypoint n8n ... n8n-n8n:latest execute --id=...`, sharing the same named volume (`n8n_n8n_data`) so it sees the same workflows/credentials, and joined to `ciso-assistant-community_default` for API reachability.

## Bug Found and Fixed: `Finding.severity` Is an Integer, Not a String

`core/models.py`'s `Finding.severity` is a `SmallIntegerField` with `IntegerChoices` (`undefined=-1, info=0, low=1, medium=2, high=3, critical=4`). The read serializer hydrates it to its display label (`get_severity_display`) — e.g. a `GET` shows `"severity": "medium"` — but the write serializer expects the raw integer. The workflow's escalation logic originally sent the string `"high"` back on `PATCH`, which Django rejected: `400 {"severity": ["\"high\" is not a valid choice."]}`. Fixed in the "Merge Observation & Escalate" Code node by mapping the label back to its integer value before the update.

## UAR Workflow — Verified End to End

Ran via the one-off execution pattern above. Real counts against `data/identity_inventory.csv` (45 Privileged/Admin accounts in scope, 31 stale by the >90-day/blank rule): **29 auto-attested**, **2 flagged** (EMP-0058, EMP-0152), `escalate: true`.

Confirmed via a **separate, fresh `n8n execute` run** of a minimal read-only verification workflow (`automation/n8n/verify-finding.json`, not the same execution that performed the `PATCH`) that the C-04 Finding's live state in CISO Assistant actually changed:

```
"severity": "high",
"status": "identified",
"observation": "[2026-08-26] Automated UAR run (n8n): 45 privileged/admin accounts in scope, 31 due for review (last_access_review_date blank or >90 days old). 29 auto-attested (Active in HRIS and Okta, access confirmed still needed). 2 not auto-attested, flagged for manual review (terminated and/or Okta status mismatch): EMP-0058, EMP-0152.
[2026-08-26] ESCALATED: severity raised from 'medium' to 'high' because 2 account(s) were not auto-attested and require manual removal review."
```

Severity was `medium` before this run; the escalation rule fired correctly because `flaggedCount > 0`.

## Risk-Scoring Script — Verified

`scripts/risk_scoring.py` runs from the host (not from inside a container -- it hits CISO Assistant through Caddy at `https://localhost:8443`, the same path used by curl throughout Stages 3-4; this is a different execution context from the n8n workflow above, which had to reach the Django backend directly over the Docker network). Reads `CISO_ASSISTANT_PAT` from the environment only, never from a file the script itself writes or logs.

**Determinism:** ran twice back to back (`--out` to two separate files); `diff` between the two runs produced zero output -- byte-identical.

**Real output, first run** (16/16 RiskScenarios matched to `risk-register.csv` by `ref_id`, zero drift, zero unrated, zero unmatched, zero overdue findings -- consistent with Stage 4's open findings all carrying future due dates):

```
| ref_id | effectiveness_pct | inherent (L,I) | residual (L,I) |
|---|---|---|---|
| R-001 | 25% | (3,3) | (2,3) |
| R-002 | 25% | (3,4) | (2,4) |
| R-003 | 25% | (2,2) | (1,2) |
| R-004 | 25% | (3,3) | (2,3) |
| R-005 | 25% | (2,3) | (1,3) |
| R-006 | 25% | (2,3) | (1,3) |
| R-007 | 50% | (2,3) | (1,3) |
| R-008 | 0% | (3,2) | (3,2) |
| R-009 | 25% | (2,2) | (1,2) |
| R-010 | 0% | (3,2) | (3,2) |
| R-011 | 25% | (2,3) | (1,3) |
| R-012 | 25% | (2,2) | (1,2) |
| R-013 | 50% | (2,3) | (1,3) |
| R-014 | 25% | (1,4) | (0,4) |
| R-015 | 0% | (3,3) | (3,3) |
| R-016 | 50% | (1,4) | (0,4) |
```

**Fresh, independent `GET`** on 3 scenarios (a separate script invocation, not reusing the `PATCH` responses) confirmed the residual fields actually changed in CISO Assistant, not just that the script reported success -- and confirmed the math against Section 4a's rule by hand:

| ref_id | CSV (L,I) | Inherent index | Effectiveness | Expected residual index | Live residual index |
|---|---|---|---|---|---|
| R-001 | (4,4) | (3,3) | 25% | floor(3×0.75)=2, impact 3 → (2,3) | (2,3) |
| R-002 | (4,5) | (3,4) | 25% | floor(3×0.75)=2, impact 4 → (2,4) | (2,4) |
| R-013 | (3,4) | (2,3) | 50% | floor(2×0.50)=1, impact 3 → (1,3) | (1,3) |

All three match. One early mistake caught before this run: the script initially defaulted `--base-url` to `http://backend:8000` (copied from the n8n networking fix above), which is only reachable from inside the Docker network, not from the host where this script actually runs. Corrected the default back to `https://localhost:8443`.
