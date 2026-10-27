# Devpost submission — GridQueue

Copy-paste source for the Devpost form. Every number here is in `README.md` or `LIMITATIONS.md` and comes from a
command in the repo. Fill or resolve every `TODO` (listed in §0) **before** pressing submit.

**Deadline:** Fri 30 Oct 2026, 17:00 UTC (19:00 CEST). **Target:** submit Thu 29 Oct, 18:00 CEST.

---

## 0. Blockers before submitting (honest status, 27 Oct 2026)

| # | What | Why it blocks | State |
|---|---|---|---|
| B1 | **One live run with real keys**: `NEBIUS_API_KEY` + `TAVILY_API_KEY`, then `make api` and one query (e.g. 5612 AB, feed-in), with the ledger lines kept | Stage-1 filter: the project must *"run on Nebius Token Factory … at runtime"*. **Best Use of Tavily ($3,000)** requires *"a functional runtime call to the Tavily API as part of the solution"* (`docs/JUDGING-RUBRIC.md`, `docs/SUBMISSION-CHECKLIST.md` §A, §D). Today every answer comes from SYNTHETIC fixtures with 0 Tavily calls (LIMITATIONS §2) | **TODO** |
| B2 | Verify the pinned model IDs against the authenticated Token Factory catalog | `backend/app/config.py` pins `nvidia/Nemotron-3-Ultra-550b-a55b`, `nvidia/nemotron-3-super-120b-a12b`, `nvidia/nemotron-3-nano` with `TODO_VERIFY(C-T02)` | **TODO_VERIFY(C-T02)** |
| B3 | Upload `docs/media/gridqueue-demo.mp4` to YouTube as **public**, attach `docs/media/gridqueue-demo.vtt` as captions | Devpost needs a public YouTube link ≤ 3:00 | **TODO** (file ready, 2:50) |
| B4 | GitHub Pages live at https://knarayanareddy.github.io/gridqueue-grid-connection/ | The "working demo" URL. Needs the deploy workflow on `main` and Pages set to *GitHub Actions* | Workflow is in `.github/workflows/` on the branch. **Owner action:** *Settings → Pages → Source: GitHub Actions* (the agent token got 403), then merge to `main` and open the URL. See `reports/PAGES-VIDEO.TASK_REPORT.md` |
| B5 | Clean-clone test of the README on another machine | `docs/SUBMISSION-CHECKLIST.md` §C | **TODO** (29 Oct) |

If B1 cannot happen in time: submit to **Best Apps and Agents** only, delete §6 below, and do not claim the
Tavily bonus. A Tavily integration that has never made a runtime call does not meet the stated requirement.

---

## 1. Form fields

**Project name:** GridQueue

**Tagline (≤ 200 chars):**
> Can I get grid power here, and when? Answers per direction from Dutch grid operators' own documents, every
> date with its quote and hash, or an honest "we don't know".

**Track:** Best Apps and Agents · **Bonus:** Best Use of Tavily ($3,000), only if B1 is done.
Award stacking: *"one (1) Overall Award OR one (1) Track Award and one (1) Bonus Award."*

**Links**
- Code: https://github.com/knarayanareddy/gridqueue-grid-connection (Apache-2.0, `LICENSE` at the root)
- Demo (static, no login): https://knarayanareddy.github.io/gridqueue-grid-connection/ (B4)
- Video: `TODO(B3): YouTube URL` (2:50, captions)

**Built with:** Python 3.11+ · FastAPI · Pydantic · JSON Schema 2020-12 · React 18 · TypeScript · Vite · Nebius
Token Factory (OpenAI-compatible API, structured output with `json_schema`) · NVIDIA Nemotron (B2) · Tavily
Search + Extract · Token Factory Sandboxes (pack built for it; not run) · Nebius Serverless AI Jobs (job and
container written; not run) · GitHub Pages · Playwright (demo video)

---

## 2. Description (paste into "About the project")

### Inspiration

The persona in our spec: Ruud runs a 22-person metalworking shop in Brabant and wants 60 kW of rooftop solar.
His installer says the grid has no capacity. Nobody can tell him whether that is true, for how long, or what he
can do instead. The answer exists, scattered across grid-operator PDFs and registers in Dutch, in a vocabulary
that does not match the question. *(The persona is illustrative; we have not yet run interviews.)*

### What it does

You enter a postcode, a power and a direction. GridQueue answers in the operator's own words:

- **Per direction.** Congestion is registered separately for feed-in (*teruglevering*) and consumption
  (*afname*). For the same address it can answer "waiting list only" for solar export and "250 kW stated as
  available" for consumption. Answers that merge the two directions are invalid by contract.
- **Every date with its binding status.** An indicative date (*codeerprognose*) is shown with a "Non-binding
  forecast" chip *because the operator's own sentence says so*, plus the verbatim Dutch quote, the document, the
  retrieval time and its sha256.
- **Routes, not dead ends.** Non-firm connections, flex contracts and congestion-management participation,
  ranked, each with the operator's quoted route and who to contact.
- **Refusal as a feature.** If no official position survives verification, the answer is
  `NO_OFFICIAL_POSITION_FOUND`: "We will not guess." Instead it gives a Dutch phone script in the operator's
  vocabulary.

### How we built it

1. **S1 resolve location**: postcode → grid operator from a static, cited table. No model.
2. **S2 retrieve**: **Tavily** search and extract, restricted to the operator's own domain; every document gets
   a sha256 and a retrieval time; every call goes to an append-only ledger.
3. **S3 extract**: **NVIDIA Nemotron on Nebius Token Factory** proposes position claims as **structured output**
   against our JSON Schema (`schemas/core-schemas.json`).
4. **S5 deterministic gate**: plain Python with no model and no network (a test enforces it). It checks that
   every quote is literally in the source, and that every date and kW figure is stated in that quote. Fail →
   rejected; not stated → dropped and the answer abstains.
5. **Answer + UI**: React Direction Cards with the quote pill, the binding chip, ranked options, the gate
   report, and an A/B evidence tab.

Also built: an application pack that re-verifies every hash and is withheld if one unsupported date is injected
(made for a network-off Token Factory Sandbox; run locally so far); a 50-area sweep job and its container (for a
Serverless AI Job; run offline so far); a gate-on vs gate-off A/B harness.

### The proof (measured, synthetic)

`make ab`, on a **SYNTHETIC, hand-written** adversarial set of 29 cases, both arms from the same snapshot:

| | Gate OFF | Gate ON |
|---|---|---|
| Fabricated dates reaching the answer | 10/10 | **0/10** |
| Fabricated kW figures | 6/6 | **0/6** |
| All fabricated values blocked | — | **21/21** |
| Genuine values kept | 10/10 | 10/10 |
| Misattributed values (real quote, wrong meaning) passing | 5/5 | **4/5** |

The last row is the gap we publish rather than hide: the gate checks that a value is *stated*, not what the
sentence *means*. That is why the quote is always shown next to the value. The set was written to contain
fabrications, so it shows what the gate stops, not how often a real model invents dates.

### Challenges we ran into

- Matching Dutch dates and numbers literally ("derde kwartaal van 2028", "1.250 kW") without letting a model
  "interpret" them.
- Keeping the two directions apart all the way through the contracts, the sweep and the UI.
- Being honest in the demo: everything shown runs on SYNTHETIC fixtures, and the UI, the video and the README
  say so.

### Accomplishments we're proud of

- A gate that blocked 21 of 21 fabricated values in our synthetic set while keeping all 10 genuine ones, with no
  model in the loop and 0 LLM calls in the gate.
- A refusal path that is useful: "we will not guess", plus the question to ask the operator.
- 236 automated tests; the README's and LIMITATIONS' numbers are derived from `runs/*.json` by a test.

### What we learned

Provenance is a product feature. Users trust a dated quote with a hash more than a confident sentence. Refusing
needs as much design work as answering.

### What's next

The live run (B1); ingesting official documents (the corpus has 0 today); revision tracking for forecasts that
move; running the pack in a network-off Token Factory Sandbox and the sweep as a Serverless AI Job; a native
speaker's check of the Dutch phone scripts.

---

## 3. Nebius / NVIDIA usage (for the README-highlights requirement)

| Service | How GridQueue uses it | Status |
|---|---|---|
| **Token Factory** (base `https://api.tokenfactory.nebius.com/v1/`) | S3 extraction through the OpenAI-compatible API with `response_format` `json_schema` ([doc](https://docs.tokenfactory.nebius.com/ai-models-inference/json)) | Wired and unit-tested with mocks; **not yet run live (B1)** |
| **NVIDIA Nemotron** | Ultra for extraction; Super and Nano are pinned for options and pre-summarising | IDs **TODO_VERIFY(C-T02)** (B2) |
| **Token Factory Sandboxes** | Network-off validation of the application pack (spawn with `networking.enabled: false`) | Pack built and tested locally; **not run in a Sandbox** |
| **Serverless AI Jobs** | The 50-area sweep (`jobs/sweep_50_postcodes.py`, `jobs/Dockerfile`) | Run offline; **not submitted as a job** |

## 4. Demo video

- File: `docs/media/gridqueue-demo.mp4` (H.264/AAC, 1920×1080, 25 fps, **2:50**) and `.webm` (VP9/Opus).
  Captions: `docs/media/gridqueue-demo.vtt`. Shot timing: `docs/media/gridqueue-demo.timeline.json`.
- Follows the locked `video/script.md` shot for shot. It was recorded automatically by `scripts/record-demo.ts`
  (Playwright) from the static Pages build; S09 shows a real pytest run captured at recording time.
- **Narration is a synthetic text-to-speech voice**, disclosed on the end card. The script's human voice-over
  can replace `video/voiceover/*.mp3` (same file names), followed by a re-run of `make demo-video`.
- S01 is a typographic persona card, not filmed B-roll; the persona is labelled illustrative.

## 5. Judge quick path (≤ 2 minutes, no install)

1. Open the static demo. The banner says it is precomputed from SYNTHETIC documents.
2. Click **5612** (tagged *video*). Feed-in: Q3 2028, non-binding, waiting list. Open **Official quote**: the
   Dutch sentence, the document, the retrieval time, the sha256.
3. Toggle **Consumption**: capacity available, 250 kW stated.
4. Click **3011**: "No official position found", then "We will not guess" with the Dutch script.
5. Open the **A/B Gate Evidence** tab: gate OFF 10 fabricated dates, gate ON 0.

Deep links: `?postcode=5612&direction=consumption`, `?postcode=3011`, `?tab=ab`.

## 6. Best Use of Tavily ($3,000), only if B1 is done

> Requirement: *"a functional runtime call to the Tavily API as part of the solution."*

Tavily is **load-bearing**, not decoration. Grid operators move and re-version their congestion documents
constantly, so a hard-coded URL list rots; S2 asks Tavily for the operator's *current* documents on the
operator's own domain, then extracts their text for the gate to check against.

- Endpoints: `POST https://api.tavily.com/search` and `POST https://api.tavily.com/extract`, Bearer auth
  ([search](https://docs.tavily.com/documentation/api-reference/endpoint/search),
  [extract](https://docs.tavily.com/documentation/api-reference/endpoint/extract)). Client:
  `backend/app/tools/tavily.py`.
- Every call is ledgered (`runs/ledger.jsonl`, the `LedgerLine` contract: query, time, results used and
  rejected), and every answer's footer shows `N Tavily calls`.
- What the gate does with Tavily's output: a quote that is not literally in the extracted text is rejected. So
  Tavily's retrieval quality directly sets how often GridQueue can answer rather than refuse.
- `TODO(B1)`: paste the live run's evidence here: query, timestamp, Tavily calls, documents used/rejected, the
  ledger line ids, and a screenshot of a Direction Card whose footer shows a non-zero Tavily count.
