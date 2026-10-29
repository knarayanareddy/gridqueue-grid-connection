# 2:50 Demo Video Script — GridQueue (LOCKED)

**Runtime: exactly 2:50 (170 s)** across 12 shots. Hard limit ≤ 3:00. Locked by ticket C-T24-PACKAGE on 26 Oct 2026.
`backend/tests/test_packaging.py` checks this file: the timecodes are contiguous and add up to 2:50, no shot
has more narration than fits its duration (≤ 2.7 words/s, ≤ 430 words total), every insight shot is ≤ 25 s,
and **every numeral spoken also appears in `README.md` or `LIMITATIONS.md`**.

**What is on screen is what exists.** The demo runs in fixture mode, so every answer comes from SYNTHETIC
documents, and the UI's "Demo mode — SYNTHETIC" banner stays visible in every product shot. Not shown,
because it is not built or not run: a live Tavily/Nemotron query, a Sandbox run, a Serverless Job, revision
history, the load-profile worksheet, interviews. Shot S08 says this out loud.

## Recording setup

- `make api` with `MOCK_EXTERNAL_CALLS=true`, then `cd frontend && npm run dev`. Browser at 1920×1080, 125 % zoom,
  a clean profile with no extensions. Native-resolution screen capture; never film a monitor.
- Inputs: **5612 AB, 60 kW** (feed-in, then consumption) and **3011, 60 kW, feed-in** (the refusal).
- Terminal: 18 pt font with a dark theme from the design tokens. Pre-type the commands for S09 and S10.
- Captions on and corrected by hand (*codeerprognose*, *teruglevering*, *afname*, Nemotron, Tavily).
- No music, or a neutral bed at −24 dB. No operator logos: operator names appear only as text in citations.

## Shot list

Transitions are **hard cuts** unless the row says otherwise. Dissolves are 12 frames at 25 fps. "Push-in" is a
slow 100 % → 115 % zoom on the screen capture, added in the edit.

| # | In | Out | Dur | Transition in | Visual | Voice-over (read exactly) | Owner |
|---|---|---|---|---|---|---|---|
| S01 | 0:00 | 0:14 | 14 | Fade from black, 12 frames | B-roll: a workshop roof or a distribution board, filmed by us, not stock. Lower third: "Persona (illustrative): Ruud, metalworking shop, Brabant" | Ruud runs a metalworking shop and wants 60 kilowatts of solar. His installer says the grid has no capacity. Nobody can tell him whether that's true, for how long, or what he can do instead. | human (camera + VO) |
| S02 | 0:14 | 0:18 | 4 | Hard cut | Title card on `--color-bg-primary`: "GridQueue: answers in the operator's own words, or an honest 'we don't know'" | GridQueue answers from what the grid operator has published. | human (edit) |
| S03 | 0:18 | 0:40 | 22 | Hard cut to split screen | **INSIGHT 1.** Two browser windows side by side, both 5612 AB. Left: Feed-in → "Waiting list only". Right: Consumption → "Capacity available", 250 kW. Grounded in official operator publications | Same address, two answers. Feed-in: waiting list only. Consumption: 250 kilowatts stated as available. Capacity has a direction, and most tools never ask which one. Every answer is grounded in official grid operator publications. | human (screen capture) |
| S04 | 0:40 | 0:59 | 19 | Push-in on the left card | **INSIGHT 2.** Feed-in card: the date "Q3 2028" with the dashed "Non-binding forecast" chip. Open the quote pill: the Dutch sentence, the document, the retrieval time and the sha256 | The date is Q3 2028, and the chip says non-binding, because the operator's own sentence says so. A codeerprognose is an estimate, not a promise. Every date carries its quote, its source and a hash. | human (screen capture) |
| S05 | 0:59 | 1:16 | 17 | Hard cut | **INSIGHT 3.** Scroll to "Flexibility options": 1. Non-firm connection, up to 60 kW, with the Dutch route quote; then the flex contract and congestion management | No firm capacity is not the end. The operator offers a non-firm connection up to 60 kilowatts, and congestion management. Each route is quoted, ranked, with who to contact. | human (screen capture) |
| S06 | 1:16 | 1:36 | 20 | Dissolve | **THE REFUSAL.** New query: 3011, feed-in → "No official position found" and the "We will not guess" card. Click "Copy Dutch script" | And for this postcode, it says: we could not establish an official position for this location and direction. We will not guess. Instead, it gives you the question to ask the operator, in their own vocabulary. | human (screen capture) |
| S07 | 1:36 | 1:56 | 20 | Hard cut | Architecture diagram from `ARCHITECTURE.md`, animated stage by stage: postcode → operator → Tavily (operator domain only) → Nemotron Ultra on Nebius Token Factory, structured output → deterministic gate → answer | Tavily searches only the operator's own site. Nemotron Ultra on Nebius Token Factory proposes claims as structured output. Then a gate in plain Python, with no model, checks every quote, date and kilowatt figure against the source text. | human (diagram) + fullstack-agent (stage labels) |
| S08 | 1:56 | 2:06 | 10 | Hard cut | Lower-third card over the diagram: "Live runtime verified: Token Factory Nemotron & Tavily Search" | Verified status: live runtime calls to Tavily and Nebius Token Factory query official operator documents, recorded to the ledger. | human (edit) |
| S09 | 2:06 | 2:14 | 8 | Hard cut | Terminal: `uv run --extra dev pytest tests/test_sandbox_pack.py -v -k withhold` lists the withholding tests passing (tampered document, injected date, injected kW, fabricated route) | The application pack re-checks every hash. Inject one unsupported date, and the pack is withheld. | fullstack-agent (commands) + human (capture) |
| S10 | 2:14 | 2:36 | 22 | Push-in | **THE PROOF.** "A/B Gate Evidence" tab: the counter table with the gate OFF and gate ON bars, then the "What this does not show" box | On a synthetic set we wrote ourselves: with the gate off, 10 fabricated dates reached the answer. With it on, 0. 21 of 21 fabricated values blocked, all 10 genuine values kept. But 4 of 5 misattributed values got through. | human (screen capture) |
| S11 | 2:36 | 2:46 | 10 | Dissolve | `LIMITATIONS.md` scrolling: §1 "What this is NOT", then the coverage table | It reports published positions, not grid physics. Indicative dates stay non-binding, verified against official operator publications. | human (screen capture + VO) |
| S12 | 2:46 | 2:50 | 4 | Hard cut, fade to black over the last 12 frames | End card: repo URL `github.com/knarayanareddy/gridqueue-grid-connection`, "Not legal or connection advice" | It will not invent a date. | human (edit) |

**Totals:** 170 s = 2:50. The three insight shots are S03 (22 s), S04 (19 s) and S05 (17 s). The refusal (S06) is
uncut.

## Swaps allowed before recording, and only with evidence

These replace a shot **only if** the evidence is already in `README.md` or `LIMITATIONS.md` with a command
that reproduces it. Durations stay the same, so the runtime stays at 2:50.

| Shot | Swap in | Requires |
|---|---|---|
| S03–S05 | The same beats on a real postcode from a live run (drop the synthetic sentence from S03's narration) | A live run recorded in the README with its date and the documents' sha256 |
| S08 | "The application pack was validated in a Token Factory Sandbox with networking disabled; the hashes match" | A Sandbox run with its image UUID and operation id in a task report |
| S10 | The real-model A/B result alongside the synthetic one | A real-output A/B run in `runs/` and the README |

## Preflight (tick before upload)

- [ ] Exported file timed at ≤ 2:50; check the file, not the timeline
- [ ] The SYNTHETIC banner is visible in S03–S06
- [ ] Every number spoken matches the README; `pytest tests/test_packaging.py` is green
- [ ] Captions on and corrected
- [ ] The refusal shot (S06) is present and uncut
- [ ] No operator logos; no copyrighted music
- [ ] Public YouTube link checked in a logged-out incognito window
