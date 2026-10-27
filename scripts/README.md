# scripts/

| File | What it does |
|---|---|
| `build_static_demo.py` | Precomputes the GitHub Pages snapshot: the pipeline in fixture mode (SYNTHETIC), 60 kW, both directions, for the 50 sweep areas plus 5612 and 3011 → `frontend/public/demo/` (gitignored). Run by `make build-pages` |
| `record-demo.ts` | Records the demo video (`video/script.md`, 12 shots, exactly 170 s) from the Pages build → `docs/media/gridqueue-demo.{mp4,webm,vtt,timeline.json}`. Run by `make demo-video` |
| `package.json` | Node dependencies of the recorder only: `playwright-core`, `@ffmpeg-installer/ffmpeg` (H.264/VP9/AAC/Opus encoding), and the three design-system fonts named in `frontend/src/tokens.css` (`@fontsource-variable/*`) |

## Recording the video

```bash
make build-pages                       # snapshot + static site in frontend/dist
cd scripts && npm ci
npx playwright-core install chromium   # once; or set CHROMIUM_PATH to any Chromium/Chrome binary
node --experimental-strip-types record-demo.ts
```

Requirements: Node ≥ 22.6 (type stripping), `uv` on PATH (S09 runs the real withholding tests), about 10 minutes:
170 s of real-time capture, then encoding.

Options: `--plan` prints the shot and voice-over timeline and exits; `--no-voiceover`; `--no-captions` (keep only
the `.vtt`); `--keep-raw` keeps the raw capture in `docs/media/.raw/` (gitignored).

How it is timed:
- The shot list is parsed from `video/script.md`; the run fails if it is not 12 contiguous shots adding up to 170 s.
- Each shot starts on its timecode. The run fails if any shot starts more than 0.25 s late, and the actual start
  times are written to `gridqueue-demo.timeline.json`.
- A white pre-roll marks t = 0. ffmpeg converts the variable-rate capture to 25 fps and trims exactly 170 s at the
  sync point.

The voice-over is `video/voiceover/*.mp3`: synthetic text-to-speech, read exactly from the script, and disclosed on
the end card. To use a human voice instead, record files with the same names (S01+S02 and S08+S09 are one file
each, see `VOICEOVER` in `record-demo.ts`; the placement check fails if a clip overruns its shots) and re-run.

### Recording without system Chromium (what the agent sandbox did)

The sandbox had no browser, no system libraries for one, and no access to Playwright's download CDN. The video in
`docs/media/` was recorded with `@sparticuz/chromium@153.0.0` (installed outside the repo, not a dependency):

```bash
# after extracting its al2023 libraries to /tmp/chromelibs
LD_LIBRARY_PATH=/tmp/chromelibs/al2023/lib CHROMIUM_PATH=/tmp/chromium PLAYWRIGHT_BROWSERS_PATH=/tmp/pwb \
  node --experimental-strip-types record-demo.ts
```

Playwright's `recordVideo` looks for its own ffmpeg in `$PLAYWRIGHT_BROWSERS_PATH/ffmpeg-<rev>/`. If that is
missing, the recorder links the `@ffmpeg-installer` binary there.
