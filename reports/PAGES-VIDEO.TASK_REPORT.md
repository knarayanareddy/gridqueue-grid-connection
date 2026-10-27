# PAGES-VIDEO · TASK REPORT — GitHub Pages static demo & demo video automation

Owner: fullstack-agent · Branch: `arena/35bac992-gridqueue-grid-connection` · Base: `c123381` (PR #4 merged)

**Short version.**
- **Static demo:** builds with `make build-pages`. The deploy workflow is written but the site is **not live
  yet**: it deploys when the workflow runs on `main` (see "Pages status" below).
- **Video:** recorded by a script, 1920×1080, exactly 170 s, mp4 + webm + captions, in `docs/media/`.
- **Devpost texts:** drafted. `docs/DEVPOST_SUBMISSION.md` §0 lists what must happen before submitting. Above all,
  **the Tavily track and the Stage-1 "runs on Token Factory" filter need one live run with real keys, which has
  not happened.**
- **Tests:** 236 pass (13 new).

## WHAT

**Deliverable 1: GitHub Pages site** (https://knarayanareddy.github.io/gridqueue-grid-connection/)
- `scripts/build_static_demo.py` (new): runs the real `answer_query` in fixture mode (SYNTHETIC) at 60 kW for both
  directions over 52 areas. These are the 50 sweep areas plus **5612** and **3011**; the systematic sample contains
  neither, so they are added. The result is 104 `QueryResponse` files plus `index.json` → `frontend/public/demo/`
  (gitignored, about 1.3 MB). It also copies `runs/ab_experiment_results.json` and `runs/sweep_summary.json` there.
- `frontend/src/data.ts` (new), `App.tsx`, `app.css`, `vite.config.ts`, `vite-env.d.ts`, `.env.pages`:
  - Static mode (`VITE_STATIC_DEMO`) fetches snapshot files instead of `/v1/answer`.
  - Area picker with chips for all 52 areas; typing a postcode works (`5612 AB` → 5612).
  - Feed-in/consumption toggle; the same Direction Card shows quotes, non-binding chips and sha256.
  - The 3011 refusal card ("We will not guess") with the Dutch phone script and Copy button.
  - A/B Gate Evidence tab (Gate OFF 10 fabricated dates vs Gate ON 0; 21/21 blocked).
  - A "Static demo" banner; a "not in this static snapshot" message for other areas.
  - Deep links `?postcode=&direction=&tab=ab&embed=1`.
  - The base is `/gridqueue-grid-connection/` in `--mode pages` only (DISCREPANCIES #30). `tokens.css` is untouched
    and only `var(--…)` tokens are used.
- `Makefile`: `build-pages`, `pages-preview`, `demo-video`.
- `docs/ci/deploy-pages.yml` (new): on push to `main` or manual run, runs `make build-pages` → `frontend/dist` →
  configure-pages v6 / upload-pages-artifact v5 / deploy-pages v5. Action versions were read from the GitHub API, not
  guessed. Enable steps are in `docs/ci/README.md`.

**Deliverable 2: demo video**
- `scripts/record-demo.ts` (new) with `scripts/package.json`, pinned exactly: playwright-core 1.64.1,
  @ffmpeg-installer/ffmpeg 1.1.0, and three @fontsource-variable 5.3.0 packages (D-026).
  - Parses the 12 shots from `video/script.md` and drives one harness page over the Pages build with Playwright
    `recordVideo` at 1920×1080. Zoom is a 1.25 CSS scale (DISCREPANCIES #38).
  - Shot content:
    - S01 persona card, S02 title;
    - S03 5612 AB split screen (feed-in waitlist / consumption 250 kW);
    - S04 date pill with quote and sha256; S05 options (non-firm 60 kW);
    - S06 3011 refusal, with the Dutch script copied (the "Copied" state is visible);
    - S07 architecture, S08 "Not yet run" lower third;
    - S09 the **real** `pytest -k withhold` run (8 passed);
    - S10 A/B tab; S11 LIMITATIONS.md scroll; S12 end card.
  - Timing is scheduled and checked (D-027): the run fails if a shot starts more than 0.25 s late.
  - Encoding: mp4 (H.264 + AAC) and webm (VP9 + Opus), a 0.48 s fade at each end, loudnorm, burned-in captions, and
    a `.vtt` with 33 cues.
- `video/voiceover/*.mp3`: synthetic TTS of the locked narration, disclosed on the end card (DISCREPANCIES #34).
- `docs/media/gridqueue-demo.{mp4,webm,vtt,timeline.json}` (17.9 MB + 15.2 MB). Chosen frames were reviewed: text
  is sharp, there are no padded frames, and nested markdown renders.
- `scripts/README.md`: how to record, the flags, and the sandbox Chromium workaround.

**Devpost texts**
- `docs/DEVPOST_SUBMISSION.md`:
  - §0 blockers B1–B5 and the fallback "Best Apps and Agents only" if B1 is not done;
  - form fields and the description, built from measured numbers only;
  - the Nebius/NVIDIA usage table, where each row is marked built/run/not run;
  - video notes, the judges' quick path, and the Tavily section (§6) with an evidence slot `TODO(B1)`.
- `docs/DEVPOST_FEEDBACK.md`: follows the template; about 1,100 words and 13 points.
  - Real observations, with URLs and quotes from the docs:
    - `json_schema` structured output worked;
    - the OpenAI-compatible base URL worked;
    - the network-off guard;
    - Serverless quickstart gaps (CPU preset, secrets/env, output persistence; logs are console/CLI only; the
      container disk is released);
    - the Sandboxes REST upload endpoint is missing.
  - A feature request that puts the use case first.
  - The "my fault" item (the live run was postponed).
  - Every live metric and the Dutch Tavily section are `TODO(B1)`; no numbers are made up.

**Docs and tests**
- README: links to the static demo and video, and two rows in the build-status table.
- `docs/ci/README.md`: Pages section.
- `docs/DISCREPANCIES.md`: rows #30–#38. `docs/DECISIONS.md`: D-025 to D-027.
- `backend/tests/test_static_demo.py` (new, 13 tests):
  - the snapshot covers every sweep area plus 5612/3011 in both directions;
  - every answer is a valid SYNTHETIC `QueryResponse` at 60 kW;
  - the video beats are in the snapshot (5612 feed-in Q3 2028 non-binding waitlist with non-firm 60 kW, 5612
    consumption 250 kW, 3011 refuses with the Dutch script);
  - the snapshot agrees with the committed sweep;
  - the A/B and sweep files are bundled unchanged;
  - the pages base and static mode are on in pages mode only;
  - the Makefile target and the workflow build and deploy the static site;
  - every shot is voiced exactly once and the clips exist;
  - the recorded video matches the locked script (12 shots, 170 s, lateness bound);
  - the captions match the narration word for word.
  - Failure paths: an extra area without an operator is refused, an invalid answer is not published, and a
    non-synthetic answer is not published as the demo.

## VERIFY (pasted)

```
$ make check            # ruff check + ruff format --check + pytest
============================= 236 passed in 3.23s ==============================

$ cd frontend && npx tsc -b && echo tsc-ok
tsc-ok

$ make build-pages
dist/index.html                   0.62 kB │ gzip:  0.36 kB
dist/assets/index-KM6kDcWb.css   11.31 kB │ gzip:  2.78 kB
dist/assets/index-C0TVrGod.js   171.49 kB │ gzip: 54.91 kB
✓ built in 1.81s

$ cd frontend && npx vite build --outDir /tmp/apibuild     # API mode still builds, base "/"
✓ built in 2.03s

$ uv run --extra dev pytest tests/test_static_demo.py -q
13 passed in 0.67s

$ ffmpeg -i docs/media/gridqueue-demo.mp4
  Duration: 00:02:50.02, start: 0.000000, bitrate: 840 kb/s
    Stream #0:0(eng): Video: h264 (High), yuv420p, 1920x1080 [SAR 1:1 DAR 16:9], 720 kb/s, 25 fps
    Stream #0:1(und): Audio: aac (LC), 48000 Hz, stereo, fltp, 114 kb/s
$ ffmpeg -i docs/media/gridqueue-demo.webm
  Duration: 00:02:50.01, start: -0.007000, bitrate: 713 kb/s
    Stream #0:0(eng): Video: vp9 (Profile 0), yuv420p(tv), 1920x1080, SAR 1:1 DAR 16:9, 25 fps
    Stream #0:1: Audio: opus, 48000 Hz, stereo, fltp
$ grep -c -- "-->" docs/media/gridqueue-demo.vtt
33
# recording run: sync offset 1.360 s, max shot lateness 0.006 s; loudness mean −19.6 dB, max −4.5 dB;
# speech onsets (silencedetect) 18.7 40.5 59.5 76.8 96.4 116.1 134.3 156.3 166.1 s — matching the script plan
```

Screenshots checked against `vite preview` of the Pages build: `?postcode=5612%20AB&direction=feed_in&embed=1`
(Q3 2028, Non-binding forecast, Waiting list only, three ranked options) and
`?postcode=3011&direction=consumption` (No official position found / We will not guess).

## Pages status

- **Workflow:** `.github/workflows/deploy-pages.yml` was pushed in its own commit (`ci(pages): …`). The push
  succeeded, so this token has the `workflow` scope. `docs/ci/deploy-pages.yml` is kept as the reference copy.
- **Enabling Pages from here failed:**
  ```
  $ gh api -X POST repos/knarayanareddy/gridqueue-grid-connection/pages -f build_type=workflow
  {"message":"Resource not accessible by integration", ... "status":"403"}
  $ gh api repos/knarayanareddy/gridqueue-grid-connection/pages
  {"message":"Not Found", ... "status":"404"}
  ```
- **Owner action, one time:** *Settings → Pages → Build and deployment → Source: **GitHub Actions***.
- **Then:** the site deploys on the first push to `main` after this branch is merged, or via *Actions → Deploy
  GitHub Pages demo → Run workflow* on `main`.
- **Not merged and not deployed:** agents do not merge without the user's request, so the URL is **not live
  yet** (B4).

## TODO_VERIFY / open items

- **B1, live run with real keys:** needed for the Tavily track ("functional runtime call") and the Stage-1
  "runs on Token Factory at runtime" filter. Not done. Neither the Pages demo nor the video calls Tavily or the model
  (DISCREPANCIES #32).
- **TODO_VERIFY(C-T02):** model ids in `backend/app/config.py`, still to be checked against the authenticated
  catalog.
- **TODO_VERIFY(serverless-logs-and-volumes), partly resolved.** The quickstart
  (https://docs.nebius.com/serverless/quickstart/jobs) says logs are available "only in the web console and CLI"
  (`nebius ai job logs $JOB_ID`), and that the container disk is released when the job completes. So the sweep's
  `--stdout` JSON in the logs is currently the only documented way to get its output back. Secrets/env vars,
  CPU-only presets and persistent output are still not documented there.
- **TODO_VERIFY(sandbox-file-upload):** no REST upload endpoint found (unchanged).
- **The Pages URL on the video end card** is shown before the site is verified live (B4, DISCREPANCIES #37).
- **`ARCHITECTURE.md` status marks are stale** (DISCREPANCIES #35); left for a follow-up ticket.
- **`DEVPOST_FEEDBACK.md`:** contact, name and role are `TODO`. Two doc-page URLs (Sandboxes networking, files)
  were not recorded and are marked `TODO(url)`.
