# Final Credibility Audit

> **Synthetic data.** Veridian LegalTech is fictional. See the root [README.md](../README.md) for the full disclaimer.

Per `CLAUDE.md` Section 11, answered explicitly rather than asserted, as of **2026-08-27**.

## Does anything look templated or AI-generated rather than reasoned through?

The risk register and control catalog *started* templated on purpose — `CLAUDE.md` Section 8 is an explicit two-pass workflow: a scaffolded first draft (clearly labeled `DRAFT:`), then a required rewrite pass in Mike's own words before a stage counts as done. That pass is complete: `grep -c "DRAFT:"` returns 0 on both CSVs, and `docs/stage2-rewrite-checklist.md` is checked off for all 16 risks and 10 controls. Spot-checking the actual rationale text, it reads as reasoned-through, not generic — e.g. R-001's rationale explicitly weighs a cheaper interim fix against the real one and cross-references two *other* risk IDs (R-002, R-010) that share its root cause; C-03's rationale cites the identity inventory data directly as proof the gap is real, not hypothetical.

**One real instance of stale, templated-looking content found and fixed during this audit:** `controls/README.md` and `risk-register/README.md` still said the rewrite gate hadn't passed, days after it actually had. Corrected — see `docs/decision-log.md` #25.

## Are the controls specific to Veridian's actual context, or generic?

Specific. Every control's rationale in `controls/control-catalog.csv` names something concrete about Veridian rather than generic best-practice language — e.g. C-03's rationale ties directly to the identity inventory showing real terminated-but-Active accounts; C-07's cites that vendor review is tied to contract renewal rather than an independent schedule, specific to how Veridian's vendor relationships are actually structured. The SOC 2 point-of-focus mapping in `docs/stage3-deployment-notes.md` was done by reading each point of focus's actual text against each control's actual content, not a template lookup — three controls (C-06, C-07, C-08) ended up citing point-of-focus categories (CC7.2, CC9.2) that CLAUDE.md's own original framework doc hadn't initially anticipated, because the literal content match required it.

## Are the metrics real (calculated from this repo's data) or invented?

Real, and re-verified live on 2026-08-27 while writing this stage (not recalled from earlier stage reports — see `docs/decision-log.md`'s header and the numbers throughout this README): 16 risks, 10 controls, 195 synthetic employees, 45 privileged/admin accounts with 31 stale as of today, 4 live findings with 0 currently overdue, 375 total SOC 2 requirement-assessment rows with 12 actually tested (6 non-compliant / 6 partially compliant), 15 assets (7 Primary / 8 Support). `scripts/risk_scoring.py` was re-run twice fresh this session and diffed byte-identical before "deterministic" was written down anywhere in this stage's copy.

## Could every component be defended under a specific follow-up question in an interview?

Yes — but the specific preparation material for this lives outside the tracked repo, deliberately. A visible, pre-written answer key would undermine the thing it's meant to demonstrate if an interviewer could read it in advance, so that material stays local-only rather than committed. What follows here is one example worked through in public: how to defend the Stage 6 shadcn-adjacent override under a skeptical "isn't this the same as `aegis-triage` now?" follow-up.

## Is the synthetic-data disclaimer prominent, not buried?

It's the first content block in the root README, in a blockquote, before the architecture diagram or any metric. It's also restated at the bottom of the README, in `docs/company-profile.md`'s first line, in every `docs/stage*.md` file's opening paragraph, in `evidence/README.md`, in this file, and as a permanent caption in the running dashboard itself (`dashboard/app.py`).

## Does it read as distinct from `aegis-triage`, given the Stage 6 shadcn-adjacent override?

Checked the actual `aegis-triage` repo rather than assume an answer, since the override genuinely changed the risk calculus here — including the strongest form of the counterpoint, not just the README's prose description of it:

- `aegis-triage`'s `frontend/package.json` lists `"shadcn": "^4.19.0"` directly in its dependencies — confirmed by fetching the raw file. This is not a stylistic resemblance or a README claim; it's a real, versioned build dependency that generates the actual component primitives (buttons, cards, badges) its UI is built from.
- Its README states the same thing in prose: `"Frontend: Next.js 16, React 19, Tailwind v4, shadcn/ui."`
- Its actual dashboard screenshot (`docs/screenshots/dashboard.png`, fetched live): a near-black background, white/gray sans-serif throughout (no serif anywhere), saturated red/amber/gray rounded-pill verdict badges, generic KPI tiles, a data table of triage runs. A dark terminal/alert-feed aesthetic.
- VIGCAP's dashboard: a light slate `#F2F3F5` background, Fraunces serif headers, IBM Plex Mono for IDs, a bespoke rotated ink-stamp component, a docket-rail-with-Phosphor-icons layout, a brass/garnet/amber/slate-green palette coded to audit/ledger meaning, built in Streamlit/Python — not Next.js/React at all.

**Honest answer, engaging that fact directly rather than softening it:** `aegis-triage`'s shadcn/ui is a genuine, versioned dependency, and Stage 6's override means VIGCAP's hand-rolled CSS now deliberately reproduces that same component grammar — soft shadow, ~8px radius, clean-sans base type. On that one axis, the two products share real design-system lineage, not coincidence, and that should be said plainly rather than argued around.

What does *not* converge, checked dimension by dimension, each independently verifiable by inspecting both repos:

| Axis | `aegis-triage` | VIGCAP | Converged? |
|---|---|---|---|
| Stack | Next.js/React/Tailwind, client-rendered SPA | Streamlit/Python, server-rendered | No — different rendering model entirely |
| Mode | Dark (near-black) | Light (`#F2F3F5` slate) | No — inverted before any component is considered |
| Typography | No serif anywhere | Fraunces serif display headers | No — the most visible difference in any screenshot |
| Signature component | Plain rounded-pill badges (shadcn's default `Badge`) | Bespoke rotated ink-stamp component | No — the one place Section 4 asked for boldness has no shadcn equivalent |
| Layout metaphor | Flat alert-feed data table | Docket-rail + workpaper ledger | No — different information architecture |
| Subject matter | Agentic SOC alert triage | Governance/compliance judgment | No — different content regardless of styling |
| Card/button geometry (shadow, radius, base type weight) | shadcn/ui's actual default recipe | Hand-rolled CSS deliberately imitating that recipe | **Yes — this is the real, acknowledged convergence** |

**Where this leaves the claim:** "distinct" holds across stack, mode, typography, signature component, layout, and subject matter — six independently falsifiable axes. It does not hold for the underlying card/button geometry, which the override deliberately borrowed from the same source `aegis-triage` depends on directly. If asked in an interview whether the two look the same, the honest answer is "no, but they now share one specific, named design-system lineage" — not an unqualified "no," and not "yes" either.
