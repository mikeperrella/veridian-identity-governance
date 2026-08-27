# Stage 6 — Dashboard

Documents how the Streamlit executive dashboard (`dashboard/`) was built, the tooling
correction found before writing any code, the trend-line honesty check the dashboard's
own design depends on, and the accessibility fixes made after visually testing it. No
secrets appear in this file.

## Correction: `streamlit-facade` rejected before use

CLAUDE.md Section 3 named `streamlit-facade` specifically to avoid a shadcn-style look
("avoids the streamlit-shadcn-ui look — too close to `aegis-triage`"). Verified via
PyPI's JSON package metadata (`https://pypi.org/pypi/streamlit-facade/json`, v0.1.6,
MIT, by Daniyal M) and the author's own Streamlit-community announcement post: the
package is real, but is explicitly self-described as **"shadcn-inspired,"** which is
the exact visual family Section 3 said to avoid. Same category of correction as the
n8n-node and Eramba-API findings in earlier stages — verify the actual package, not
just its name, before building on it.

**Resolution:** the dashboard uses Streamlit's native `.streamlit/config.toml` theming
(colors, both `font`/`headingFont`/`codeFont` set directly to Google Fonts URLs — no
custom CSS needed for typography at all, contrary to this stage's original plan to
self-host font files) plus a small amount of hand-written CSS/HTML, scoped only to the
two elements with no native Streamlit equivalent: the "review stamp" badge and the
docket-rail button restyling. This follows the bundled `developing-with-streamlit`
skill's own explicit guidance ("do not use custom CSS for theming — only for what a
native element can't do").

## Trend-line honesty check

Per Section 0 non-negotiable #3 (no fabricated outcomes), checked whether the repo has
enough dated history for a program-wide "trend line pre/post remediation" before
building one. It does not: the C-03 finding's 5-stage lifecycle
(`docs/stage4-control-testing-findings.md`, 2026-08-26 → 2026-09-05) is the **only**
multi-point dated series anywhere in the repo. The other 3 findings sit at a single
`identified` timestamp with future due dates; no risk or control has more than one
dated event.

**Resolution:** the dashboard renders one chart — "C-03 remediation timeline" — plotting
exposed-account count (3 → 3 → 0 → 0 → 0) against the finding's 5 real dates, titled and
captioned explicitly as a single-finding case study, not a program-wide trend. No
intermediate points are invented for anything else.

## Correction: heat map originally sourced residual band from the CSV, not live

The first version of the risk heat map colored bubbles from `risk-register.csv`'s
`residual_risk_band`, on the reasoning that CISO Assistant "has no independent residual
likelihood/impact pair" — true of the CSV's data *model* (a single combined score,
per `docs/risk-methodology.md` Section 4a), but wrongly generalized to CISO Assistant's
API, which Stage 5's `risk_scoring.py` specifically populates with independent
`residual_proba`/`residual_impact` per scenario. A live `GET /api/risk-scenarios/`
re-check confirmed all 16 scenarios still carry real (non -1) residual values and a
populated `residual_level` — nothing had regressed since Stage 5's own verification.

**Fix:** `dashboard/metrics.py`'s `live_residual_bands()` reads the live
`residual_level.name` per scenario; `dashboard/charts.py`'s `risk_bubble_chart()` uses
it for bubble color, falling back to that risk's CSV band only per-row when the live
value is unavailable (API unreachable, or a future unrated scenario). The CSV is still
used for inherent likelihood/impact position (CISO Assistant's inherent values are
themselves copied from the same CSV, per Stage 5's drift check) and remains the
authoritative record referenced elsewhere in this project.

**This is not a bug to reconcile away:** comparing live `residual_level` to the CSV's
`residual_risk_band` for all 16 risks, **6 diverge** (R-003, R-007, R-009, R-012, R-013,
R-014) — the expected, already-documented consequence of Section 4a's likelihood-only
reduction rule (reducing only one of two factors that make up a multiplicative score
will not always re-band the same way a combined-score formula does). The dashboard
surfaces this directly: the heat map caption states the live figure dynamically, and
selecting a diverging risk in the docket rail shows both values side by side with an
explicit "differs from CSV" note, rather than picking one number and hiding the
disagreement.

## Data sourcing per dashboard element

| Element | Source | Live or local |
|---|---|---|
| Risk heat map | Position: `risk-register/risk-register.csv` (inherent L×I). Color: `GET /api/risk-scenarios/` `residual_level` | Position local, color live (see the correction above) — the CSV has no independent residual likelihood/impact pair (`docs/risk-methodology.md` §4a), only a combined residual score + band, so the live per-scenario `residual_level` drives bubble color instead, with per-risk CSV fallback if the API is unreachable |
| Avg. control effectiveness (risk-adjusted) | `risk-register/risk-register.csv` `control_effectiveness_pct` | Local mean across the 16 risks (25%, matching `scripts/risk_scoring.py`'s Stage 5 output) |
| Control test verdicts | `GET /api/requirement-assessments/` | Live — filtered client-side to `result != not_assessed` (12 of the ~375 rows in the full imported SOC 2 framework), reproducing Stage 4's 6 non_compliant / 6 partially_compliant / 0 compliant split |
| Open / overdue findings | `GET /api/findings/` | Live — overdue uses the real wall-clock date, not a frozen `AS_OF` like `risk_scoring.py`, since this is a live dashboard, not a one-off deterministic report |
| % privileged accounts current on review | `data/identity_inventory.csv` | Local only — CISO Assistant has no per-employee review-date field. Same staleness rule as Stage 5's n8n UAR run (blank or >90 days); reproduces 45 in scope / 31 stale exactly |
| C-03 remediation timeline | Hardcoded in `dashboard/metrics.py`, cross-checked live | The 5 dates/counts are transcribed verbatim from the finding's `observation` log; a live `GET` on the same finding checks `status`/`severity` still match and shows a warning banner if they don't |

`dashboard/api_client.py` reuses `scripts/risk_scoring.py`'s exact auth/TLS/pagination
pattern (`Authorization: Token <PAT>`, `CISO_ASSISTANT_PAT` env var, self-signed-cert
`verify=False`, DRF `{"results", "next"}` pagination) but is read-only and returns
`None` instead of raising on failure, so each section of the dashboard degrades
independently if CISO Assistant is unreachable.

**Verified (this session):** stopped only the `caddy` container (CISO Assistant's
reverse proxy) with the dashboard already running — the findings table and control-
verdict bar showed clear "CISO Assistant is unreachable" warnings with no traceback,
while the CSV-only sections (heat map, privileged-review %, C-03 timeline) kept
rendering normally. Restarted `caddy` and confirmed the live sections recovered without
restarting the dashboard process.

## Accessibility: WCAG contrast fix found during visual verification

A Playwright screenshot of the running dashboard (`python -m playwright install
chromium`, free/open-source, no paid service) surfaced two real defects that the code
alone didn't reveal:

1. White marker/bar text on `BRASS`/`AMBER` fills (bubble-count numerals, the
   control-verdict bar's amber segment) measured **~3:1** against WCAG 2.1's contrast
   formula — below the 4.5:1 normal-text threshold, and visibly hard to read at native
   size in the screenshot.
2. The "review stamp" component (ink-colored text on a pale tint of the same ink) fails
   the same threshold for amber/brass ink specifically (**~2.5:1**) — garnet and
   slate-green ink pass on their own tints (7.18:1 and 4.87:1), but amber/brass are
   too light at any tint to reach 4.5:1 as text, only as a fill.

**Fix:** `dashboard/constants.py` keeps `AMBER`/`BRASS` as fill-only colors (bubble and
bar backgrounds, where the palette's exact hex values from Section 4 stay unchanged)
and adds `AMBER_TEXT`/`BRASS_TEXT` — same hue, darkened until both reach ≥4.5:1 against
the app background and against white — for anything rendered as text/ink/border
instead (`text_on_fill()` picks per-fill text color in the charts; `FINDING_SEVERITY_COLOR["medium"]`
uses `AMBER_TEXT` directly since severity stamps are text-only, never a fill).
Re-verified numerically (relative-luminance contrast formula) and visually (before/after
screenshots) after the fix.

## Follow-up fix pass: rail icons, KPI accents, stamp fidelity, bubble overlap, toolbar

A second, narrowly-scoped pass fixed 6 specific problems found from screenshots of the
finished dashboard:

1. **Docket rail icons** — Phosphor Icons (`@phosphor-icons/web`, MIT), Regular weight
   for inactive rail items, Fill weight for the selected one. Added a third rail section,
   **Findings**, since the requested icon set (shield/warning/check) implied one; findings
   get synthetic `F-01`..`F-04` IDs (matching the Findings section's due-date order) since
   `Finding.ref_id` isn't populated in this CISO Assistant instance.

   **Real bug found and fixed:** the first attempt loaded the icon font via `<link
   rel="stylesheet">` inside `st.html()` — zero network requests ever fired. `st.html()`
   sanitizes with DOMPurify, which strips `<link>` outright (any tag that can load
   external resources). Confirmed by reading `streamlit/elements/html.py` directly and
   checking live network requests before/after. Fixed by moving the stylesheet URLs into
   `@import` inside an actual `<style>` block instead, which passes DOMPurify's
   sanitizer — verified the font request (200) and the icon's computed `content` resolving
   to a real glyph afterward, not just that the code "looks right."

2. **Forest green (`#2D5C3E`)** added for exactly one purpose: the selected rail item's
   filled background. Contrast-checked before choosing the text color on top: white
   passes (7.74:1), brass and ink both fail badly (2.5:1, 2.2:1) — so the selected item
   renders in white, not the brass used elsewhere for "selected" state text.

3. **KPI left-border accents**, 2-tier (good/concerning only, matching exactly what was
   asked): `SLATE_GREEN` vs. `AMBER_TEXT`. `st.metric` has no `key` parameter in this
   Streamlit version (checked its signature directly) — each metric is wrapped in
   `st.container(key="kpi_...")` and targeted via `[class*="st-key-kpi_..."]
   [data-testid="stMetric"]`, the same descendant-selector pattern already proven on the
   docket-rail buttons. Verified the actual computed `border-left-color` on all four
   tiles via `page.evaluate`, not just visually: `rgb(134,97,32)` (`#866120`,
   `AMBER_TEXT`) on 3 of 4, `rgb(63,107,79)` (`#3F6B4F`, `SLATE_GREEN`) on the 0-overdue
   tile.

4. **Review stamp fidelity** — root-caused by inspecting the live rendered DOM
   (`getComputedStyle`) before changing anything: the CSS/rotation/border were all
   already applying correctly; the specific stamp that read as "a plain black rectangle"
   was the risk-treatment stamp (`Mitigate`/`Accept`/etc.), which had deliberately been
   colored neutral ink in an earlier fix since those aren't pass/fail verdicts. Switched
   treatment stamps to `BRASS_TEXT` and made the stamp itself read more clearly as a
   stamp regardless of color (3px border, 14% tint, guaranteed 3-8° minimum tilt so a
   random draw can never land near 0° and look unrotated).

5. **Heat map bubble overlap** — real, computed, not a same-coordinate collision (risks
   sharing one exact coordinate were already merged into one bubble with a count numeral
   and full hover breakdown). Adjacent grid cells are ~66px apart in this chart's
   geometry; the old size formula could produce two adjacent bubbles whose radii summed
   to more than that gap (e.g. 47px + 31px = 78px > 66px). Reduced the formula so the
   largest possible adjacent pair in this data stays under the gap, keeping size as a
   secondary cue behind the numeral and hover text.

6. **Toolbar hidden** — confirmed `client.toolbarMode = "minimal"` is a real, current
   option by reading the installed Streamlit's own `config.py` directly (not just a
   forum post), and added it to `.streamlit/config.toml`.

## Deliberate design-direction override: shadcn-adjacent polish + Apple-style typography

The user explicitly decided to move the dashboard's visual polish toward a shadcn-adjacent
look (soft shadows, 8px radius, tighter type scale) and Apple-style typography (generous
body line-height/letter-spacing, clear heading-size steps) — **overriding** the earlier
`streamlit-facade` correction's reasoning and, by extension, knowingly accepting some of
the `aegis-triage` visual-convergence risk Section 0's distinctness non-negotiable
originally wanted to avoid. Recorded here as a considered tradeoff the user made
deliberately, not a silent contradiction — see the matching note added to CLAUDE.md
Section 3. The implementation is still hand-rolled CSS layered onto the existing native
theming and bespoke components, not the `streamlit-facade` library or any other
shadcn-wrapping package, since none of it has an equivalent for the stamp/rail/icon
components already built.

Concrete changes: `.streamlit/config.toml` gained `headingFontSizes`/`headingFontWeights`
(previously unset, so every heading level rendered close in size), `baseFontSize = 15`,
and `baseRadius = "medium"` (8px, native, applied globally). `dashboard/components.py`
added a soft-shadow/8px-radius treatment for every "card" container (each given an
explicit `key="card_..."` in `app.py`, since bordered `st.container()`s carry no
distinguishing testid of their own in this Streamlit version — confirmed via DOM
inspection, only an unstable auto-generated emotion-cache class exists — so `key=`
scoping, the same pattern already proven on the docket buttons and KPI tiles, is the
only reliable selector), a hover-elevation treatment on docket-rail buttons, and
`line-height: 1.65` / `letter-spacing: 0.01em` scoped to body text only
(`stMarkdownContainer p`, `stCaptionContainer`), not headings.

**Real bug found and root-caused along the way, same method as the earlier Phosphor
`<link>` bug:** a visual artifact next to the "Findings" header turned out to be
**Streamlit's own native "copy link to heading" icon** (`data-testid=
"stHeaderActionElements"`, a chain-link SVG auto-added to every `st.header`/
`st.subheader`), not anything from this project's icon code. Confirmed via
`getComputedStyle` (opacity 0 at rest, only shown on `:hover`) and by hovering over the
header and screenshotting the icon actually appearing, in a generic thin-stroke style
that matches nothing else in this design system. Fixed by suppressing it globally
(`display: none !important`) rather than guessing at spacing.

**Severity indicators, audited across every `render_stamp()` call site:** the risk-detail
treatment stamp, control-detail linked-finding stamp, and the Findings-detail card's
stamp are all genuine single-item detail contexts and were already correct. The only
violation was the main Findings section's list loop — four rotated stamps stacked in a
row, reading as repeated stickers rather than Section 4's "spend the boldness in one
place" signature element. New `render_severity_flat()` (a small colored dot + flat
uppercase label, no border, no rotation, no tint) replaces the stamp in that one list
context; the Findings row layout was also restructured (bold title on its own line,
`Status: ... · Due: ...` as a separate muted caption line) instead of one run-on
sentence that wrapped awkwardly mid-date.

## Verification summary

- Data logic (`metrics.py`, `charts.py`) unit-checked directly against the real API and
  CSVs: 45 privileged/admin, 31 stale, 25% avg. effectiveness, 6/6/0 control verdicts,
  4 findings (0 overdue), C-03 found live and `closed` — all match the figures already
  documented in Stages 4-5.
- Rendered and screenshotted with Playwright/Chromium at desktop (1440px), tablet
  (900px), and mobile (420px, where Streamlit's own responsive breakpoint collapses the
  sidebar) widths.
- Docket-rail click-to-select verified interactively (clicking `C-03` or `R-002`
  highlights the matching heat-map bubble and renders its detail workpaper card).
- Keyboard focus confirmed visible on a restyled docket-rail button (`.focus()` +
  screenshot) despite the custom CSS resetting default button chrome.
- `pbakaus/impeccable` (real, Apache-2.0, `github.com/pbakaus/impeccable`) installed via
  `claude plugin marketplace add` / `claude plugin install` for the final design-QA
  punch-list pass, per the project's convention of running it only once the dashboard is
  functionally built and styled — plugin installation takes effect on the next Claude
  Code session, so that pass is queued rather than run inline in this one.
