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

## Where the Credentials Actually Live

The superuser password and the Personal Access Token generated during this session exist only in the running CISO Assistant instance and in the operator's own local notes — neither value appears in this repository, in any command output saved to the repo, or in git history.
