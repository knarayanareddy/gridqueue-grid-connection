# DEVPOST-LOCK · TASK REPORT — Devpost submission & Tavily bonus lock

Owner: fullstack-agent · Branch: `arena/022b3201-gridqueue-grid-connection` · Base: `3259b08` (PR #5 merged)

**Short version.** All three action items are done. Two instructions were carried out *accurately* rather than
literally, because the literal versions are not true:
- **"Clean Energy Track":** the hackathon has no such track. The submission selects **Best Apps and Agents** and
  calls GridQueue a clean-energy app (DISCREPANCIES #39).
- **"21/21 … across the 50-area sweep":** the A/B ran on the 29-case SYNTHETIC set, and the sweep has no gate-off
  arm. The headline quotes the A/B with its real scope and mentions the sweep separately (DISCREPANCIES #40).

The Tavily bonus is flagged as **entered, eligible once B1 (the live run) is done**. Reviewing the feedback also
turned up a factual error in our own docs: the Sandboxes REST upload endpoint *does* exist. It is now the
feedback's "my fault" point, and `TODO_VERIFY(sandbox-file-upload)` is resolved.

## Checked before writing

- **Pages is live.**
  - `gh api repos/…/pages` → `build_type: workflow`, `html_url: https://knarayanareddy.github.io/gridqueue-grid-connection/`.
  - Deploy run [40524323828](https://github.com/knarayanareddy/gridqueue-grid-connection/actions/runs/40524323828):
    `workflow_dispatch` on `main` @ `3259b08`, conclusion `success`.
  - Fetching the URL returns the static-demo banner and the 52-area picker (Enexis 18, Liander 17, Stedin 17).
- **Tracks.** The official page https://nebiusglobalaihackathon.devpost.com/ lists four: Coding and Agentic
  Engineering, Best Apps and Agents, Personal AI, Physical AI. Bonus: Best Use of Tavily, $3,000. This agrees with
  `docs/JUDGING-RUBRIC.md`.
- **A/B scope.**
  - `runs/ab_experiment_results.json`: `test_set.n_cases` 29, SYNTHETIC, `hand_written_adversarial`.
  - `runs/sweep_summary.json`: `mode` fixture, 50/50 completed, 0 failed, 16 abstained.
  - The sweep has no gate-off path (D-020).
- **Deadline.** EU summer time ended on Sun 25 Oct 2026, so 17:00 UTC on 30 Oct is **18:00 CET**, not 19:00 CEST
  as `SUBMISSION-CHECKLIST.md` said. The US is still on PDT until 1 Nov, so "10:00 am PT = 17:00 UTC" holds.

## WHAT

1. **`README.md`**
   - The requested Live Demo badge sits directly under the H1.
   - The demo link no longer says "live once the workflow has deployed".
   - The status-table row is now ✅ live (deployed from `main` on 27 Oct).
2. **`docs/DEVPOST_SUBMISSION.md`**
   - Top of the file: the live demo link and `Video: TODO(B3): https://www.youtube.com/watch?v=<VIDEO_ID>`.
   - New **Prize eligibility** table:
     - Best Apps and Agents: selected; clean-energy app; there is no Clean Energy Track, with the official URL;
     - Best Use of Tavily, $3,000: entered, eligible once B1 is done, quoting the requirement;
     - Overall awards, with the stacking rule;
     - Most Valuable Feedback, with `TODO_VERIFY(rules)` on whether it counts as the one Bonus Award.
   - The description now opens with the **A/B delta**: *"Gate OFF accepted 10 of 10 fabricated dates. Gate ON blocked
     21 of 21 fabricated values (0 invented dates) and kept 10 of 10 genuine ones."* It also gives:
     - the scope (29 SYNTHETIC cases) and the 4 of 5 misattributed gap;
     - the sweep as a separate gate-on run (50 of 50 completed, 0 failed, no grid findings);
     - the live link.
   - B4 is marked **Done** with the run link. The deadline is corrected to 18:00 CET.
3. **`docs/DEVPOST_FEEDBACK.md`**, reviewed against the template checklist and partly rewritten:
   - **Retracted a false claim.** "We could not find the REST upload endpoint" was wrong. It is `POST
     https://api.tokenfactory.nebius.com/sandboxes/v1/files` (raw octet-stream, `Project` header, returns `uuid`,
     `sha256`, `size`). It is now the **"my fault" point**, together with what made it easy to miss, each with a
     URL:
     - the files guide links the REST download reference but not the upload one;
     - the reference page's title is a raw docstring;
     - there is a second, different `POST /v1/files` (OpenAI-compatible, multipart, `purpose=batch`, `id`);
     - the cURL sample says `Project: <api-key>`, while the field is described as the project ID.
   - Filled the two `TODO(url)`s, using the networking cookbook with its `/sys/class/net` snippet.
   - Added a **TL;DR** with the three most actionable asks, for the "viability and impact" judging.
   - Added the measured sweep wall time (0.072 s, from `cost.wall_seconds`).
   - Softened two phrases that went beyond the evidence.
   - Live metrics and the Dutch Tavily results remain `TODO(B1)`. Contact, name and role remain `TODO`.
   - About 1,560 words, 10 URLs, 7 sections.
4. **`backend/tests/test_devpost_copy.py`** (new, 10 tests). Under D-023 the Devpost copy is now checked against
   `runs/*.json`:
   - the badge is at the top of the README;
   - the headline is derived from the A/B run, with a failure-path test on tampered data;
   - the scope and sweep wording, with no A/B numbers attributed "across the 50-area sweep";
   - only a real track is selected, and "Clean Energy Track" appears only as "no Clean Energy Track";
   - the Tavily claim stays conditional while B1 is TODO;
   - the links block has the Pages URL, plus the TODO(B3) placeholder or a real YouTube URL;
   - the feedback meets the template targets and does not repeat the retracted claim.
5. **Corrections elsewhere**
   - `docs/SUBMISSION-CHECKLIST.md`: deadline and target times.
   - `reports/C-T21-T23.TASK_REPORT.md`: an update note in runbook step 2 and in the TODO list (upload endpoint).
   - `docs/DISCREPANCIES.md`: rows #39–#42.

## VERIFY (pasted)

```
$ make check
All checks passed!
============================= 246 passed in 3.64s ==============================

$ uv run --extra dev pytest tests/test_devpost_copy.py -q
10 passed in 0.03s

# mutation check: each edit applied to a copy, test run, file restored
1 badge removed                         → 1 failed, 9 passed
2 headline "blocked 20 of 21"           → 1 failed, 9 passed
3 "21/21 … across the 50-area sweep"    → 1 failed, 9 passed
4 "**Track:** Clean Energy Track"       → 1 failed, 9 passed
5 Tavily "Entered and eligible."        → 1 failed, 9 passed
6 "TODO(url)" back in feedback          → 1 failed, 9 passed
restored
```

## Still open (owner actions before submitting)

- **B1, live run with real keys.** This is what makes the **Tavily bonus** claim true; until then the copy says
  "once B1 is done". Paste the evidence into §6 of the submission.
- **B3, YouTube.** Upload `docs/media/gridqueue-demo.mp4` as public, attach the `.vtt`, and replace
  `<VIDEO_ID>` in both places.
- **B2, model ids** (`TODO_VERIFY(C-T02)`) and **B5, clean-clone test**.
- **`TODO_VERIFY(rules)`:** whether Most Valuable Feedback counts as the single Bonus Award next to Tavily.
- **Feedback personal fields:** contact, name and role.
