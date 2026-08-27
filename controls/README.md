# Control Catalog — Status

`control-catalog.csv` was scaffolded in Stage 2 per the content-ownership workflow in `CLAUDE.md` Section 8, then went through the required rewrite pass: every `control_rationale` field's `DRAFT:` prefix is gone (verified: `grep -c "DRAFT:" controls/control-catalog.csv` returns 0), and `docs/stage2-rewrite-checklist.md` is checked off in full. **The Section 8 content-ownership gate has passed** — this rationale is Mike's own words, not the scaffolded first-pass draft, and is defensible in an interview context.

`test_procedure` describes how each control was designed to be tested. Actual test results (expected vs. actual, pass/fail, deficiency severity) live in `docs/stage4-control-testing-findings.md`, not in this catalog.

See `docs/decision-log.md` for every methodology decision and correction made while populating and testing this catalog (e.g. how each control maps to specific SOC 2 points of focus, the residual-risk mapping limitation) rather than repeated here.
