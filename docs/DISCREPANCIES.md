# Discrepancies — spec vs. repository

Things where `SPEC.md` and the code disagree, and which one is right. Resolve or explain each.

| # | Spec says | Repo does | Resolution |
|---|---|---|---|
| 1 | SPEC §6: the gate is `build_answer(request, location, claims, options, docs, rules) -> Answer` | Only the per-claim primitive `DeterministicGate.evaluate()` exists | Intended: `build_answer` will call `evaluate()` per claim. Open until C-T17/C-T18 |
| 2 | SPEC §4.1: `ConnectionRequest` input for Ruud: 60 kW PV + 20 kW battery + 2× 22 kW | v0 README used a different persona (Jan-Willem, 250 kW) | README aligned to SPEC (Ruud) on 2026-10-26 |
| 3 | SPEC §7 layout: `stages/`, `corpus/`, `sandbox/`, `tools/`, `data/geo/`, `data/rules/`, `eval/`, `jobs/sweep.py` | None exist yet | Expected at Phase 0. Tracked in README build-status table |
| 4 | SPEC C-T01: `make sample` replays one fixture query end to end with no key | `make sample` runs the gate + contract tests | Honest stop-gap. Replace when the pipeline and fixtures exist |
| 5 | SPEC §5: model IDs `nvidia/Nemotron-3-Ultra-550b-a55b` etc. | Same strings in config, mixed casing, unverified | Verify against the authenticated catalog snapshot (C-T02) before any live call |
