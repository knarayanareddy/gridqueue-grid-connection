# C-T24-PACKAGE · TASK REPORT — 50-area sweep, README headline metrics, video script lock

Owner: fullstack-agent · Branch: `arena/22714110-gridqueue-grid-connection` · Base: `8aedc2d` (PR #3 merged)

**Short version.** The sweep job, README, LIMITATIONS and video script are done, and all 223 tests pass. **Every
run here is offline on SYNTHETIC fixtures.** The sweep has not been submitted as a Nebius Serverless Job, and the
README quotes no grid figures from it (user decision). The headline banner uses measured numbers only:
"100% Citation Precision" was replaced by "21/21 fabricated values blocked" (user decision). Meaning-level
precision, 10 of 14, is printed directly under the banner.

## User decisions (26 Oct, asked before building)

1. Banner third item: **"21/21 fabricated values blocked"**, with 10/14 meaning-level precision stated under it.
2. README Potential Impact: the sweep is shown **as a SYNTHETIC pipeline demonstration**, with no aggregate figures.

## WHAT

- **`jobs/sweep_50_postcodes.py`** (new):
  - **Selection:** 50 postcode4 areas, an evenly spaced sample of the three mapped ranges (Enexis 17, Liander 17,
    Stedin 16). It uses no congestion data and is labelled `systematic_sample`.
  - **Pipeline:** for each area and both directions it runs `answer_query`, the exact gated `/v1/answer` pipeline.
  - **Aggregates:**
    - share with no firm capacity (WAITLIST_ONLY / NON_FIRM_ONLY / NO_FIRM_CAPACITY), against both denominators;
    - indicative dates: distribution, median, mean quarter, binding counts;
    - operator-stated non-firm kW: min, median, max, distribution;
    - verdicts by operator, and direction-split cases.
  - **Honesty rules:** failed areas are reported, not dropped; abstentions are reported separately and never
    counted as negatives.
  - **Modes:** `--mode fixture` (default, offline, labelled SYNTHETIC) or `--mode live` (both keys required,
    otherwise exit 2, never mixed with fixtures).
  - **Serverless support:** `--min-interval` (default 2 s live), `--runner`/`--serverless-job-id`, and `--stdout`,
    which prints the full JSON so it survives in job logs.
  - **Plain `python`:** if packages are missing and `uv` exists, the script re-executes itself in the backend
    environment.
  - Writes `runs/sweep_summary.json` (committed). `make sweep`.
- **`schemas/core-schemas.json` → v1.4.0** (additive):
  - new `SweepDirection` per-direction record;
  - `SweepArea` gains `status`, `error` and `directions`, and `selected_by` gains `systematic_sample`;
  - `SweepReport` gains `mode`, `synthetic` and `request`.
  - The rules reject:
    - a fixture run claiming not to be synthetic;
    - `nebius_serverless_job` without a job id;
    - an abstained direction carrying a date or kW;
    - a failed area without an error.
- **`jobs/Dockerfile`**: also copies `jobs/` and `data/`, so one image serves the API (default CMD) or runs the
  sweep. Not built (no Docker here).
- **`README.md`**:
  - **Headline banner:** "Gate ON: 0 invented dates · Gate OFF: 10 fabricated dates accepted · 21/21 fabricated
    values blocked". The qualifier directly under it covers the synthetic hand-written set, local arms, 10 of 14
    correct and 4 misattributed.
  - **Four labelled criterion sections:**
    - Technological Implementation (Tavily + Nemotron Ultra + Token Factory Sandboxes): a component table with
      built/not-run status, and the **full 6-row A/B delta table**;
    - Design (Direction Cards + accessibility): the features that exist in code, and what is not done;
    - Potential Impact (50-area sweep): a pipeline demonstration, with only completed/failed/abstained counts;
    - Quality of the Idea (non-binding forecast prior), including the measured M04 gap.
  - Build status, commands and layout updated.
- **`LIMITATIONS.md`** (rewritten):
  - **States explicitly** that GridQueue reports **official published positions, not predictive grid physics**,
    and that **codeerprognoses remain legally non-binding** (`TODO_VERIFY(operator-wording)` to quote operators'
    own wording);
  - current status;
  - coverage (0 official documents; 3 unverified ranges = 249 postcode4 values);
  - 8 failure modes, including the measured misattribution 4/5 and the "indicatieve" marker miss;
  - a measured-numbers table with sources.
- **`video/script.md`** (locked):
  - 12 shots, exactly **2:50 (170 s)**, each with in/out timecodes, duration, transition, visual, verbatim
    voice-over and owner;
  - 322 spoken words (about 114 wpm);
  - insight shots of 22, 19 and 17 s; the refusal shot is uncut;
  - only built features are shown, and S08 says on camera what has not run;
  - evidence-gated swaps and a preflight checklist.
- **Tests** (33 new; 223 total):
  - `backend/tests/test_sweep.py` (17):
    - selection: 50 unique codes, each resolving to its operator, split 17/17/16, deterministic, endpoints
      included; an impossible allocation is rejected;
    - the report is contract-valid and labelled synthetic; counts are complete;
    - every aggregate can be recomputed from the area rows; fixture values match the gated pipeline;
    - abstentions are not negatives; every date has a binding status; runtime < 10 s; partial-date maths;
    - **failure paths:**
      - one area raises → 49 completed and 1 failed, reported and not padded, and still schema-valid;
      - live mode without keys → exit 2 and no file;
      - `nebius_serverless_job` without an id → exit 2;
      - the contract rejects four dishonest variants;
    - `main` writes the file; the plain `python` subprocess invocation runs in < 10 s;
    - the committed summary equals a fresh run.
  - `backend/tests/test_packaging.py` (16):
    - the banner and the meaning-level precision line are derived from `runs/ab_experiment_results.json`;
    - all 6 README A/B rows match;
    - "citation precision" is absent from the README and the video script;
    - the four criterion sections exist, each mentions its required terms and states what is not done;
    - the README sweep counts equal the report, and the section contains no `%`;
    - LIMITATIONS has the two required statements, and its figures equal the runs;
    - video: timecodes are contiguous and total 170 s, narration fits each shot, 3 insight shots ≤ 25 s, the
      refusal is present, every spoken numeral is published, and the spoken A/B numbers equal the measured ones.
- Makefile `sweep`. DISCREPANCIES rows 21–29; DECISIONS D-020 to D-024.

## MEASURED

**Acceptance run:** `python jobs/sweep_50_postcodes.py` with the system python3 (re-executes via uv):

```
sweep-50-v1 [SYNTHETIC fixture run — not a finding about the Dutch grid] runner=local_process mode=fixture
  areas: requested=50 completed=50 failed=0 abstained(both directions)=16 direction_split=34
  feed_in     no firm capacity 34/34 with a position (100.0%) · dates n=17 median=2028-Q3 binding={'non_binding': 17} · non-firm kW n=17 median=60
  consumption no firm capacity 17/34 with a position (50.0%) · dates n=0 median=None binding={} · non-firm kW n=0 median=None
  wall time 0.076 s · tavily calls 0 · model calls 0
real	0m0.354s
```

These aggregates **are by construction**: 17 Enexis areas all get the Enexis fixture answer, 17 Liander areas
the Liander answer, and 16 Stedin areas abstain because no document exists. They show the pipeline and the
aggregation work. They are not facts about the grid, and the README does not quote them.

## VERIFIED

- `make check`:
  ```
  cd backend && uv run --extra dev ruff check . && uv run --extra dev ruff format --check .
  All checks passed!
  32 files already formatted
  cd backend && uv run --extra dev mypy
  Success: no issues found in 19 source files
  ============================= 223 passed in 2.24s ==============================
  ```
- `jobs/sweep_50_postcodes.py`: ruff check and format clean; `mypy` → `Success: no issues found in 1 source file`.
- Schema: `check_schema` passes; the real report validates against `SweepReport` with 0 errors; the existing
  36 schema tests pass.
- **Mutation checks**, run by editing the source and then restoring it:
  - sweep counts abstentions as positions → **3 failed**;
  - README kW gate-ON cell changed 0/6 → 1/6 → **1 failed** (`test_readme_has_every_measured_ab_number`).
- `pytest tests/test_sandbox_pack.py -v -k withhold` (the S09 shot command) → 8 passed.
- **Not verified:** Docker build of `jobs/Dockerfile` (no Docker); any live or Serverless run; the README as
  rendered on GitHub (not viewed).

### VERIFY: `cd backend && uv run --extra dev pytest tests/ -v`

```
============================= test session starts ==============================
platform linux -- Python 3.11.2, pytest-9.1.1, pluggy-1.7.0 -- /home/user/gridqueue-grid-connection/backend/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/user/gridqueue-grid-connection/backend
configfile: pyproject.toml
plugins: asyncio-1.4.1, anyio-4.15.1
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 223 items

tests/test_ab_eval.py::test_result_is_contract_valid PASSED              [  0%]
tests/test_ab_eval.py::test_gate_on_rejects_every_fabricated_value PASSED [  0%]
tests/test_ab_eval.py::test_gate_off_accepts_every_fabricated_value PASSED [  1%]
tests/test_ab_eval.py::test_headline_numbers PASSED                      [  1%]
tests/test_ab_eval.py::test_gate_keeps_genuine_values PASSED             [  2%]
tests/test_ab_eval.py::test_misattribution_limitation_is_measured_and_reported PASSED [  2%]
tests/test_ab_eval.py::test_execution_is_honest_about_where_it_ran PASSED [  3%]
tests/test_ab_eval.py::test_both_arms_start_from_one_snapshot_and_are_deterministic PASSED [  3%]
tests/test_ab_eval.py::test_check_passes_on_real_gate PASSED             [  4%]
tests/test_ab_eval.py::test_check_fails_when_gate_is_removed PASSED      [  4%]
tests/test_ab_eval.py::test_check_fails_when_bypass_is_fake PASSED       [  4%]
tests/test_ab_eval.py::test_cases_file_must_be_synthetic_and_well_formed PASSED [  5%]
tests/test_ab_eval.py::test_main_writes_results_and_check_exit_code PASSED [  5%]
tests/test_ab_eval.py::test_committed_results_match_a_fresh_run PASSED   [  6%]
tests/test_ab_eval.py::test_ab_results_endpoint PASSED                   [  6%]
tests/test_ab_eval.py::test_api_has_no_way_to_turn_the_gate_off PASSED   [  7%]
tests/test_answer_api.py::test_eindhoven_feed_in_waitlist_with_gated_nonbinding_date PASSED [  7%]
tests/test_answer_api.py::test_options_are_gated_and_ranked_deterministically PASSED [  8%]
tests/test_answer_api.py::test_eindhoven_consumption_capacity_and_partial PASSED [  8%]
tests/test_answer_api.py::test_invented_date_and_fabrications_rejected_by_gate PASSED [  8%]
tests/test_answer_api.py::test_rotterdam_no_document_gives_no_official_position PASSED [  9%]
tests/test_answer_api.py::test_unmapped_or_malformed_postcode_abstains[9999] PASSED [  9%]
tests/test_answer_api.py::test_unmapped_or_malformed_postcode_abstains[abcd] PASSED [ 10%]
tests/test_answer_api.py::test_bad_input_is_422[payload0] PASSED         [ 10%]
tests/test_answer_api.py::test_bad_input_is_422[payload1] PASSED         [ 11%]
tests/test_answer_api.py::test_bad_input_is_422[payload2] PASSED         [ 11%]
tests/test_answer_api.py::test_bad_input_is_422[payload3] PASSED         [ 12%]
tests/test_answer_api.py::test_bad_input_is_422[payload4] PASSED         [ 12%]
tests/test_answer_api.py::test_determinism_hash_stable PASSED            [ 13%]
tests/test_answer_api.py::test_mode_selection_needs_both_keys PASSED     [ 13%]
tests/test_answer_api.py::test_live_path_retrieves_official_domain_only_and_gates PASSED [ 13%]
tests/test_answer_api.py::test_live_invented_date_is_dropped PASSED      [ 14%]
tests/test_answer_api.py::test_live_paraphrased_quote_gives_no_official_position PASSED [ 14%]
tests/test_answer_api.py::test_live_tavily_failure_abstains_without_fixture_fallback PASSED [ 15%]
tests/test_answer_api.py::test_live_extractor_calls_token_factory_shape_and_ledgers PASSED [ 15%]
tests/test_answer_api.py::test_live_extractor_invalid_output_abstains PASSED [ 16%]
tests/test_app.py::test_health PASSED                                    [ 16%]
tests/test_app.py::test_info_lists_models_without_leaking_keys PASSED    [ 17%]
tests/test_app.py::test_settings_read_env_and_have_no_fake_key PASSED    [ 17%]
tests/test_gate.py::test_line_wrapped_quote_passes PASSED                [ 17%]
tests/test_gate.py::test_trivial_quote_is_undetermined PASSED            [ 18%]
tests/test_gate.py::test_real_quote_not_containing_date_is_undetermined PASSED [ 18%]
tests/test_gate.py::test_paraphrase_fails PASSED                         [ 19%]
tests/test_gate.py::test_missing_quote_is_undetermined[None] PASSED      [ 19%]
tests/test_gate.py::test_missing_quote_is_undetermined[] PASSED          [ 20%]
tests/test_gate.py::test_missing_quote_is_undetermined[   ] PASSED       [ 20%]
tests/test_gate.py::test_missing_source_is_undetermined[None] PASSED     [ 21%]
tests/test_gate.py::test_missing_source_is_undetermined[] PASSED         [ 21%]
tests/test_gate.py::test_missing_source_is_undetermined[\n] PASSED       [ 21%]
tests/test_gate.py::test_pass_carries_verified_evidence PASSED           [ 22%]
tests/test_gate.py::test_nbsp_and_whitespace_normalised PASSED           [ 22%]
tests/test_gate.py::test_hyphenated_line_break_accepts_both_readings[van de productiecapaciteit] PASSED [ 23%]
tests/test_gate.py::test_hyphenated_line_break_accepts_both_readings[van de productie-capaciteit] PASSED [ 23%]
tests/test_gate.py::test_curly_quotes_and_dashes_normalised PASSED       [ 24%]
tests/test_gate.py::test_matching_is_case_sensitive PASSED               [ 24%]
tests/test_gate.py::test_normalise_is_idempotent PASSED                  [ 25%]
tests/test_gate.py::test_date_supported[2028-Q3-verwacht in Q3 2028] PASSED [ 25%]
tests/test_gate.py::test_date_supported[2028-Q3-verwacht in 2028-Q3] PASSED [ 26%]
tests/test_gate.py::test_date_supported[2028-Q3-in het derde kwartaal van 2028] PASSED [ 26%]
tests/test_gate.py::test_date_supported[2028-Q3-in het 3e kwartaal 2028] PASSED [ 26%]
tests/test_gate.py::test_date_supported[2028-Q3-in the third quarter of 2028] PASSED [ 27%]
tests/test_gate.py::test_date_supported[2028-H2-in de tweede helft van 2028] PASSED [ 27%]
tests/test_gate.py::test_date_supported[2028-H1-H1 2028] PASSED          [ 28%]
tests/test_gate.py::test_date_supported[2028-07-vanaf juli 2028] PASSED  [ 28%]
tests/test_gate.py::test_date_supported[2028-07-from July 2028] PASSED   [ 29%]
tests/test_gate.py::test_date_supported[2028-07-vanaf 07-2028] PASSED    [ 29%]
tests/test_gate.py::test_date_supported[2028-07-14-op 14 juli 2028] PASSED [ 30%]
tests/test_gate.py::test_date_supported[2028-07-14-on July 14, 2028] PASSED [ 30%]
tests/test_gate.py::test_date_supported[2028-07-14-op 14-07-2028] PASSED [ 30%]
tests/test_gate.py::test_date_supported[2028-niet voor 2028] PASSED      [ 31%]
tests/test_gate.py::test_date_supported[2028/2029-tussen 2028 en 2029] PASSED [ 31%]
tests/test_gate.py::test_date_not_supported[2028-Q3-verwacht in Q1 2028] PASSED [ 32%]
tests/test_gate.py::test_date_not_supported[2028-Q3-Q3 2027, en in 2028 meer] PASSED [ 32%]
tests/test_gate.py::test_date_not_supported[2028-05-capacity may become available in 2028] PASSED [ 33%]
tests/test_gate.py::test_date_not_supported[2028-03-in 2028, mark my words] PASSED [ 33%]
tests/test_gate.py::test_date_not_supported[2028-Q3-vanaf Q3 '28] PASSED [ 34%]
tests/test_gate.py::test_date_not_supported[2029-in 2028] PASSED         [ 34%]
tests/test_gate.py::test_date_not_supported[2028-in 20280] PASSED        [ 34%]
tests/test_gate.py::test_date_not_supported[2028/2029-vanaf 2028] PASSED [ 35%]
tests/test_gate.py::test_unparseable_date_is_undetermined[sometime soon] PASSED [ 35%]
tests/test_gate.py::test_unparseable_date_is_undetermined[Q3 2028] PASSED [ 36%]
tests/test_gate.py::test_unparseable_date_is_undetermined[2028-Q5] PASSED [ 36%]
tests/test_gate.py::test_unparseable_date_is_undetermined[binnenkort] PASSED [ 37%]
tests/test_gate.py::test_kw_supported[1250-afname: 1.250 kW] PASSED      [ 37%]
tests/test_gate.py::test_kw_supported[1.25-afname: 1,25 kW] PASSED       [ 38%]
tests/test_gate.py::test_kw_supported[250-0,25 MW beschikbaar] PASSED    [ 38%]
tests/test_gate.py::test_kw_supported[250-0.25MW] PASSED                 [ 39%]
tests/test_gate.py::test_kw_supported[250-250 kW] PASSED                 [ 39%]
tests/test_gate.py::test_kw_supported[1500000-1.500 MW] PASSED           [ 39%]
tests/test_gate.py::test_kw_supported[2500-2,5 MW] PASSED                [ 40%]
tests/test_gate.py::test_kw_not_supported[250-25 kW] PASSED              [ 40%]
tests/test_gate.py::test_kw_not_supported[250-250 kVA] PASSED            [ 41%]
tests/test_gate.py::test_kw_not_supported[250-250 huishoudens] PASSED    [ 41%]
tests/test_gate.py::test_kw_not_supported[250-no number] PASSED          [ 42%]
tests/test_gate.py::test_gate_checks_kw PASSED                           [ 42%]
tests/test_gate.py::test_kw_check_runs_even_when_date_passes PASSED      [ 43%]
tests/test_gate.py::test_deterministic PASSED                            [ 43%]
tests/test_gate.py::test_gate_module_makes_no_llm_or_network_calls PASSED [ 43%]
tests/test_ledger.py::test_ledger_line_matches_contract PASSED           [ 44%]
tests/test_ledger.py::test_ids_are_unique PASSED                         [ 44%]
tests/test_ledger.py::test_concurrent_writes_do_not_interleave PASSED    [ 45%]
tests/test_ledger.py::test_rejects_impossible_token_counts[kwargs0] PASSED [ 45%]
tests/test_ledger.py::test_rejects_impossible_token_counts[kwargs1] PASSED [ 46%]
tests/test_packaging.py::test_headline_banner_is_the_measured_one PASSED [ 46%]
tests/test_packaging.py::test_banner_states_meaning_level_precision PASSED [ 47%]
tests/test_packaging.py::test_readme_has_every_measured_ab_number PASSED [ 47%]
tests/test_packaging.py::test_no_unmeasured_precision_claim PASSED       [ 47%]
tests/test_packaging.py::test_four_criterion_sections[### Technological Implementation-must_mention0] PASSED [ 48%]
tests/test_packaging.py::test_four_criterion_sections[### Design-must_mention1] PASSED [ 48%]
tests/test_packaging.py::test_four_criterion_sections[### Potential Impact-must_mention2] PASSED [ 49%]
tests/test_packaging.py::test_four_criterion_sections[### Quality of the Idea-must_mention3] PASSED [ 49%]
tests/test_packaging.py::test_sweep_section_matches_the_report_and_quotes_no_synthetic_aggregates PASSED [ 50%]
tests/test_packaging.py::test_limitations_states_the_two_required_positions PASSED [ 50%]
tests/test_packaging.py::test_limitations_numbers_match_the_runs PASSED  [ 51%]
tests/test_packaging.py::test_script_runs_exactly_2_50_with_contiguous_shots PASSED [ 51%]
tests/test_packaging.py::test_narration_fits_its_shots PASSED            [ 52%]
tests/test_packaging.py::test_insight_shots_are_at_most_25_seconds_and_refusal_present PASSED [ 52%]
tests/test_packaging.py::test_every_spoken_number_is_published PASSED    [ 52%]
tests/test_packaging.py::test_spoken_ab_numbers_are_the_measured_ones PASSED [ 53%]
tests/test_s1_resolve_location.py::test_ranges_resolve_inclusive[5600-Enexis-Eindhoven] PASSED [ 53%]
tests/test_s1_resolve_location.py::test_ranges_resolve_inclusive[5658-Enexis-Eindhoven] PASSED [ 54%]
tests/test_s1_resolve_location.py::test_ranges_resolve_inclusive[5612 AB-Enexis-Eindhoven] PASSED [ 54%]
tests/test_s1_resolve_location.py::test_ranges_resolve_inclusive[5612ab-Enexis-Eindhoven] PASSED [ 55%]
tests/test_s1_resolve_location.py::test_ranges_resolve_inclusive[1000-Liander-Amsterdam] PASSED [ 55%]
tests/test_s1_resolve_location.py::test_ranges_resolve_inclusive[1099-Liander-Amsterdam] PASSED [ 56%]
tests/test_s1_resolve_location.py::test_ranges_resolve_inclusive[3000-Stedin-Rotterdam] PASSED [ 56%]
tests/test_s1_resolve_location.py::test_ranges_resolve_inclusive[3089-Stedin-Rotterdam] PASSED [ 56%]
tests/test_s1_resolve_location.py::test_postcode_is_normalised PASSED    [ 57%]
tests/test_s1_resolve_location.py::test_outside_ranges_abstains_instead_of_guessing[5599] PASSED [ 57%]
tests/test_s1_resolve_location.py::test_outside_ranges_abstains_instead_of_guessing[5659] PASSED [ 58%]
tests/test_s1_resolve_location.py::test_outside_ranges_abstains_instead_of_guessing[0999] PASSED [ 58%]
tests/test_s1_resolve_location.py::test_outside_ranges_abstains_instead_of_guessing[1100] PASSED [ 59%]
tests/test_s1_resolve_location.py::test_outside_ranges_abstains_instead_of_guessing[2999] PASSED [ 59%]
tests/test_s1_resolve_location.py::test_outside_ranges_abstains_instead_of_guessing[3090] PASSED [ 60%]
tests/test_s1_resolve_location.py::test_outside_ranges_abstains_instead_of_guessing[9999] PASSED [ 60%]
tests/test_s1_resolve_location.py::test_malformed_postcodes[] PASSED     [ 60%]
tests/test_s1_resolve_location.py::test_malformed_postcodes[56] PASSED   [ 61%]
tests/test_s1_resolve_location.py::test_malformed_postcodes[abcd] PASSED [ 61%]
tests/test_s1_resolve_location.py::test_malformed_postcodes[56123] PASSED [ 62%]
tests/test_s1_resolve_location.py::test_malformed_postcodes[5612 ABC] PASSED [ 62%]
tests/test_s1_resolve_location.py::test_malformed_postcodes[5612-AB] PASSED [ 63%]
tests/test_s1_resolve_location.py::test_location_and_citation_are_contract_valid PASSED [ 63%]
tests/test_sandbox_pack.py::test_pack_bytes_and_sha256_are_verifiable_and_deterministic PASSED [ 64%]
tests/test_sandbox_pack.py::test_pack_contains_application_block_and_verified_values PASSED [ 64%]
tests/test_sandbox_pack.py::test_only_verified_citations_are_injected PASSED [ 65%]
tests/test_sandbox_pack.py::test_consumption_kw_is_verified PASSED       [ 65%]
tests/test_sandbox_pack.py::test_no_position_pack_still_renders_phone_script PASSED [ 65%]
tests/test_sandbox_pack.py::test_answer_artifact_is_not_claimed PASSED   [ 66%]
tests/test_sandbox_pack.py::test_network_boundary_check_follows_sys_class_net PASSED [ 66%]
tests/test_sandbox_pack.py::test_cli_runs_with_network_disabled PASSED   [ 67%]
tests/test_sandbox_pack.py::test_cli_refuses_when_network_present PASSED [ 67%]
tests/test_sandbox_pack.py::test_pack_module_imports_only_stdlib_and_the_gate PASSED [ 68%]
tests/test_sandbox_pack.py::test_tampered_document_withholds_pack PASSED [ 68%]
tests/test_sandbox_pack.py::test_missing_document_text_withholds_pack PASSED [ 69%]
tests/test_sandbox_pack.py::test_injected_unsupported_date_withholds_pack PASSED [ 69%]
tests/test_sandbox_pack.py::test_date_that_differs_from_claim_withholds_pack PASSED [ 69%]
tests/test_sandbox_pack.py::test_injected_kw_withholds_pack PASSED       [ 70%]
tests/test_sandbox_pack.py::test_injected_option_kw_withholds_pack PASSED [ 70%]
tests/test_sandbox_pack.py::test_altered_citation_hash_excludes_citation_and_withholds PASSED [ 71%]
tests/test_sandbox_pack.py::test_fabricated_route_withholds_pack PASSED  [ 71%]
tests/test_sandbox_pack.py::test_cli_returns_2_and_writes_nothing_when_withheld PASSED [ 72%]
tests/test_schemas.py::test_schema_is_valid_draft_2020_12 PASSED         [ 72%]
tests/test_schemas.py::test_every_ref_is_local_and_resolves PASSED       [ 73%]
tests/test_schemas.py::test_every_type_compiles PASSED                   [ 73%]
tests/test_schemas.py::test_valid_claim_passes PASSED                    [ 73%]
tests/test_schemas.py::test_binding_null_fails PASSED                    [ 74%]
tests/test_schemas.py::test_asserted_binding_needs_a_real_quote[None] PASSED [ 74%]
tests/test_schemas.py::test_asserted_binding_needs_a_real_quote[] PASSED [ 75%]
tests/test_schemas.py::test_unknown_binding_needs_no_quote PASSED        [ 75%]
tests/test_schemas.py::test_date_without_publication_date_fails[drop] PASSED [ 76%]
tests/test_schemas.py::test_date_without_publication_date_fails[null] PASSED [ 76%]
tests/test_schemas.py::test_date_without_document_fails PASSED           [ 77%]
tests/test_schemas.py::test_free_text_or_malformed_date_fails[sometime soon] PASSED [ 77%]
tests/test_schemas.py::test_free_text_or_malformed_date_fails[Q3 2028] PASSED [ 78%]
tests/test_schemas.py::test_free_text_or_malformed_date_fails[2028-Q5] PASSED [ 78%]
tests/test_schemas.py::test_free_text_or_malformed_date_fails[2028-13] PASSED [ 78%]
tests/test_schemas.py::test_free_text_or_malformed_date_fails[28-Q3] PASSED [ 79%]
tests/test_schemas.py::test_iso_partial_dates_pass[2028] PASSED          [ 79%]
tests/test_schemas.py::test_iso_partial_dates_pass[2028-Q3] PASSED       [ 80%]
tests/test_schemas.py::test_iso_partial_dates_pass[2028-H2] PASSED       [ 80%]
tests/test_schemas.py::test_iso_partial_dates_pass[2028-07] PASSED       [ 81%]
tests/test_schemas.py::test_iso_partial_dates_pass[2028-07-14] PASSED    [ 81%]
tests/test_schemas.py::test_iso_partial_dates_pass[2028/2029] PASSED     [ 82%]
tests/test_schemas.py::test_kw_without_basis_quote_fails[drop] PASSED    [ 82%]
tests/test_schemas.py::test_kw_without_basis_quote_fails[None] PASSED    [ 82%]
tests/test_schemas.py::test_kw_without_basis_quote_fails[] PASSED        [ 83%]
tests/test_schemas.py::test_both_is_not_a_claim_direction PASSED         [ 83%]
tests/test_schemas.py::test_valid_option_passes PASSED                   [ 84%]
tests/test_schemas.py::test_model_estimate_without_flag_fails PASSED     [ 84%]
tests/test_schemas.py::test_computed_profile_needs_assumptions PASSED    [ 85%]
tests/test_schemas.py::test_option_without_evidence_fails PASSED         [ 85%]
tests/test_schemas.py::test_resolved_location_without_dso_citation_fails PASSED [ 86%]
tests/test_schemas.py::test_unresolved_location_abstains PASSED          [ 86%]
tests/test_schemas.py::test_self_reported_revision_needs_both_quotes PASSED [ 86%]
tests/test_schemas.py::test_document_citation_needs_hash_and_quote PASSED [ 87%]
tests/test_schemas.py::test_model_derived_citation_is_rejected PASSED    [ 87%]
tests/test_schemas.py::test_sample_ledger_lines_validate PASSED          [ 88%]
tests/test_sweep.py::test_selection_is_50_unique_mapped_postcodes_split_evenly PASSED [ 88%]
tests/test_sweep.py::test_selection_rejects_impossible_allocation PASSED [ 89%]
tests/test_sweep.py::test_report_is_contract_valid_and_honest_about_inputs PASSED [ 89%]
tests/test_sweep.py::test_counts_are_complete_and_never_padded PASSED    [ 90%]
tests/test_sweep.py::test_aggregates_match_the_per_area_rows PASSED      [ 90%]
tests/test_sweep.py::test_fixture_values_come_from_the_gated_pipeline PASSED [ 91%]
tests/test_sweep.py::test_abstentions_are_not_counted_as_negatives PASSED [ 91%]
tests/test_sweep.py::test_every_date_carries_its_binding_status PASSED   [ 91%]
tests/test_sweep.py::test_runs_well_under_ten_seconds PASSED             [ 92%]
tests/test_sweep.py::test_partial_dates_aggregate_by_period_start PASSED [ 92%]
tests/test_sweep.py::test_failed_area_is_reported_not_padded PASSED      [ 93%]
tests/test_sweep.py::test_live_mode_without_keys_refuses PASSED          [ 93%]
tests/test_sweep.py::test_serverless_runner_requires_a_job_id PASSED     [ 94%]
tests/test_sweep.py::test_contract_rejects_dishonest_reports PASSED      [ 94%]
tests/test_sweep.py::test_main_writes_file PASSED                        [ 95%]
tests/test_sweep.py::test_plain_python_invocation_works PASSED           [ 95%]
tests/test_sweep.py::test_committed_summary_matches_a_fresh_run PASSED   [ 95%]
tests/test_tavily.py::test_build_queries_uses_register_dso_direction_and_gemeente PASSED [ 96%]
tests/test_tavily.py::test_search_request_shape_and_ledger PASSED        [ 96%]
tests/test_tavily.py::test_extract_request_shape PASSED                  [ 97%]
tests/test_tavily.py::test_http_errors_raise_and_are_ledgered[401] PASSED [ 97%]
tests/test_tavily.py::test_http_errors_raise_and_are_ledgered[429] PASSED [ 98%]
tests/test_tavily.py::test_http_errors_raise_and_are_ledgered[432] PASSED [ 98%]
tests/test_tavily.py::test_http_errors_raise_and_are_ledgered[500] PASSED [ 99%]
tests/test_tavily.py::test_network_error_becomes_tavily_error PASSED     [ 99%]
tests/test_tavily.py::test_empty_key_rejected PASSED                     [100%]

============================= 223 passed in 2.01s ==============================
```

## SERVERLESS JOB RUNBOOK (not executed)

Source: `docs.nebius.com/serverless/quickstart/jobs`, fetched 26 Oct 2026. The documented CLI is
`nebius ai job create --name --image --container-command --args --platform --preset --timeout --subnet-id`.
Its example is a GPU job; this sweep needs CPU only.

1. Build and push the image: `docker build -f jobs/Dockerfile -t <registry>/gridqueue:<tag> .`
   `TODO_VERIFY(nebius-registry)`: which registry the job can pull from.
2. Create the job:
   ```
   nebius ai job create --name gridqueue-sweep-<date> --image <registry>/gridqueue:<tag> \
     --container-command python \
     --args "/app/jobs/sweep_50_postcodes.py --mode live --stdout --runner nebius_serverless_job --serverless-job-id gridqueue-sweep-<date>" \
     --platform <cpu platform> --preset <cpu preset> --timeout 1h --subnet-id <subnet_ID>
   ```
   Open items:
   - `TODO_VERIFY(serverless-cpu-preset)`: the platform and preset names for a CPU-only job.
   - `TODO_VERIFY(serverless-env-secrets)`: how to pass `NEBIUS_API_KEY` and `TAVILY_API_KEY` into the
     container. Live mode refuses to start without them.
   - `TODO_VERIFY(serverless-job-id)`: whether the job's id is visible inside the container. Until then, pass
     the job name chosen at creation and record the real id in the task report.
3. Collect the result. With `--stdout`, the full JSON is printed to the job logs; it is also written to
   `$RUNS_DIR/sweep_summary.json`. `TODO_VERIFY(serverless-logs-and-volumes)`: the command that fetches logs,
   or a volume mount for `/data/runs`.
4. Expected load: 50 areas × 2 directions, with ≥ 2 s between areas, so roughly 100 Tavily searches + extracts
   and 100 model calls. Every call is ledgered.

## COSTS

$0. No external calls were made.

## TODO_VERIFY

- `commercial-area-list`: a sourced list of business-park postcodes, if "commercial" areas are wanted.
- `operator-wording`: each operator's own non-binding statement, for LIMITATIONS §1.
- `nebius-registry`, `serverless-cpu-preset`, `serverless-env-secrets`, `serverless-job-id`,
  `serverless-logs-and-volumes`: the Serverless runbook items above.
- Carried over: C-T02 (model ids), C-T03 (operator domains), C-T04 (postcode ranges), and the Sandbox items from
  C-T21-T23.

## DEVIATIONS

- **The headline banner's third item** is "21/21 fabricated values blocked", not "100% Citation Precision"
  (DISCREPANCIES 23; user decision).
- **The README shows no sweep aggregates** (DISCREPANCIES 25; user decision).
- **Area selection** is a systematic sample, not "major commercial postal codes" (DISCREPANCIES 21).
- **n = 50, not SPEC's ≥200**, with no registered-congestion/control split and no Serverless run (DISCREPANCIES 22).
- **Changes outside the named deliverables:** schema v1.4.0 (additive), `jobs/Dockerfile`, Makefile `sweep`, and
  two test files. Each serves a deliverable.

## NOT_DONE

- No Serverless Job submission and no live sweep, so the README has no real-grid figures.
- No caching of S1–S3 by postcode4 + snapshot (SPEC C-T24).
- No `/sweep` page or map (C-T25).
- Video not recorded. The script is locked to what exists.
- The README was not viewed rendered on GitHub.

## NEXT

1. Resolve the Serverless TODO_VERIFYs, then run `--mode live` once (locally first, then as a job). Quote real
   figures only after that, with the run date and the corpus snapshot id.
2. Fix the binding-marker gap (LIMITATIONS failure mode 2), then re-run `make ab`. The README and its tests will
   flag the number changes.
3. Record the video from `video/script.md`. Swap shots only when their evidence exists.
