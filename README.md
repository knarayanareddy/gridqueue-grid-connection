# GridQueue — Energy Grid Interconnection Navigator & Flex Planner

[![Live Demo](https://img.shields.io/badge/Live_Demo-GitHub_Pages-2ea44f?style=for-the-badge)](https://knarayanareddy.github.io/gridqueue-grid-connection/)
[![Submission Status](https://img.shields.io/badge/Submission-READY-success?style=for-the-badge)](docs/DEVPOST_SUBMISSION.md)

> **Can I actually get power here, and when? GridQueue answers per direction (feed-in vs consumption) from
> official Dutch grid-operator documents, refuses to invent a date, and ranks the non-firm and flexibility
> routes you can use today.**
>
> ### Gate ON: 0 invented dates · Gate OFF: 10 fabricated dates accepted · 21/21 fabricated values blocked
>
> _Measured by `make ab` on a **SYNTHETIC, hand-written** adversarial set (29 cases; both arms start from
> the same snapshot; local process, not a Token Factory Sandbox). With the gate on, 14 labelled values reached the
> answer and 10 of those 14 were correct: 4 misattributed values (a real quote used for the wrong claim) got
> through. The set was written to contain fabrications, so this shows **what the gate stops**, not how often a real
> model invents dates. A run on real model output has not happened yet. [Full table](#technological-implementation)._

**Not legal or connection advice.** GridQueue reports what grid operators have published, at a stated
retrieval time. It does not predict capacity and is not affiliated with any grid operator.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
· [Limitations](LIMITATIONS.md) · [Architecture](ARCHITECTURE.md) · [Spec](SPEC.md)
· [Static demo](https://knarayanareddy.github.io/gridqueue-grid-connection/) (precomputed, SYNTHETIC; live once
the Pages workflow has deployed) · [Demo video](docs/media/gridqueue-demo.mp4) (2:50; [captions](docs/media/gridqueue-demo.vtt))

**Target:** Nebius × NVIDIA Global AI Hackathon, Best Apps and Agents track (also eligible for Best Use of Tavily).

---

## ⚠️ Build status (honest, as of 26 Oct 2026)

The end-to-end slice — postcode → operator → Tavily retrieval → Nemotron extraction → gate → `/v1/answer` →
Direction Card UI — is built, along with the offline application pack, the gate-on/off A/B and the 50-area sweep
job (tickets C-T14 to C-T24). **Everything has run offline on SYNTHETIC fixtures only.** The live path is
unit-tested with mocked Tavily/model calls but has not been run against the real APIs. Nothing has run in a Token
Factory Sandbox or as a Serverless Job, and the corpus of official documents does not exist yet.

| Component | Status | Where |
|---|---|---|
| Data contracts (JSON Schema v1.4.0, 20 `$defs` incl. `QueryResponse`, `AbExperimentResult`, `SweepReport`) | ✅ built, contract-tested | `schemas/core-schemas.json`, `backend/tests/test_schemas.py` |
| Deterministic citation gate: quote-in-source, date-in-quote, kW-in-quote | ✅ built, tested | `backend/app/gate/gate.py`, `backend/tests/test_gate.py` |
| Telemetry ledger (`runs/ledger.jsonl`) | ✅ built, tested; written by every Tavily and model call | `backend/app/tf/ledger.py` |
| API (`/health`, `/v1/info`, `POST /v1/answer` → `QueryResponse`) | ✅ contract-tested | `backend/app/main.py`, `backend/app/pipeline.py` |
| Design tokens | ✅ | `frontend/src/tokens.css` |
| Answer gate: quote, date, kW, binding, route and no-position rules; determinism hash | 🟡 built for one direction per request; TTL/currency check not yet | `backend/app/stages/s5_answer.py` |
| Source corpus (≥8 hashed official documents) | ⏳ not started, register is a template | `data/source-register.v0.json` |
| Postcode → DSO table | 🟡 3 ranges from the ticket (Eindhoven/Enexis, Amsterdam/Liander, Rotterdam/Stedin), **unverified** | `backend/app/stages/s1_resolve_location.py`, C-T04 |
| Tavily retrieval, Nemotron extraction, options | 🟡 wired + mocked tests; live run not yet done; offline mode uses SYNTHETIC fixtures | `backend/app/tools/tavily.py`, `backend/app/stages/`, `data/fixtures/synthetic/` |
| Offline application pack: re-verifies every citation, date and kW against document sha256 + gate; withholds the pack on any failure; network-off guard | 🟡 built and tested locally; **not yet run in a Token Factory Sandbox** (runbook in the C-T21-T23 report) | `backend/app/sandbox/pack.py` |
| Gate-on vs gate-off A/B over a SYNTHETIC adversarial set | 🟡 measured as **local** arms from one snapshot; not yet Sandbox branches | `jobs/ab_branch_eval.py`, `runs/ab_experiment_results.json` |
| 50-area postcode sweep through the gated pipeline | 🟡 job + image written; **run offline on SYNTHETIC fixtures only**; not yet submitted as a Nebius Serverless Job | `jobs/sweep_50_postcodes.py`, `runs/sweep_summary.json`, `jobs/Dockerfile` |
| Frontend UI (Direction Card, ranked options, quote pill, gate report; A/B Gate Evidence tab) | ✅ builds; one direction per query | `frontend/src/App.tsx` |
| Static demo site (GitHub Pages): the same UI over a precomputed fixture-mode snapshot of 52 areas, both directions; no backend, no API calls | 🟡 builds (`make build-pages`); deploy workflow written, live only after it runs on `main` | `scripts/build_static_demo.py`, `frontend/src/data.ts`, [`docs/ci/README.md`](docs/ci/README.md) |
| Demo video, recorded by a script from the static demo; synthetic TTS voice-over | ✅ `docs/media/gridqueue-demo.mp4` / `.webm`, 170 s | `scripts/record-demo.ts`, [`scripts/README.md`](scripts/README.md) |
| CI | ⏳ workflow written, not yet enabled | [`docs/ci/README.md`](docs/ci/README.md) |

---

## ⚡ Try it (no API key needed)

Requires [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`).

```bash
git clone https://github.com/knarayanareddy/gridqueue-grid-connection.git
cd gridqueue-grid-connection
make sample   # gate + contracts + /v1/answer replayed end to end on SYNTHETIC fixtures, offline
make check    # ruff lint + format check, mypy, full pytest suite
make ab       # gate ON vs OFF over the SYNTHETIC adversarial set -> runs/ab_experiment_results.json
make sweep    # 50 postcode areas through the gated pipeline -> runs/sweep_summary.json (SYNTHETIC offline)
make api      # FastAPI on http://0.0.0.0:8000 (/health, /v1/info, POST /v1/answer, GET /v1/ab-results)

# UI (second terminal; proxies /v1 to the API on :8000)
cd frontend && npm ci && npm run dev    # http://localhost:5173 — try 5612 AB, 1012, 3011
```

Without both `NEBIUS_API_KEY` and `TAVILY_API_KEY` (or with `MOCK_EXTERNAL_CALLS=true`), `/v1/answer` answers
from the **SYNTHETIC** fixtures in `data/fixtures/synthetic/` and says so in the response and the UI.

| Command | Needs a key? | What it proves today |
|---|:---:|---|
| `make sample` | No | The gate rejects paraphrased quotes, drops dates and kW figures that the quote doesn't state, and the schemas reject undocumented dates and unquoted binding claims. `/v1/answer` returns contract-valid answers, and an invented date in (synthetic) model output never reaches the answer |
| `make check` | No | Lint, types and the full test suite pass from a clean clone |
| `make ab` | No | Same snapshot, two arms: with the gate off every fabricated date, kW, binding claim and route in the synthetic set reaches the answer; with it on, none do. Also reports what the gate **misses** (4 of 5 misattributed values) |
| `make sweep` | No | The pipeline runs 50 areas × 2 directions in well under 10 s, reports completed / failed / abstained separately, and every value in the summary is recomputable from the per-area rows. **Offline the inputs are synthetic, so the aggregates are not findings** |
| `make api` | No | The service starts and reports which keys are configured |

`make demo` (live end-to-end on a real postcode) is **planned**. `python jobs/sweep_50_postcodes.py --mode live`
exists but needs both keys and has not been run.

---

## 🎯 The problem

**Persona (SPEC §1):** Ruud, 46, owns a 22-person metalworking shop in a Brabant industrial park. He wants
60 kW of rooftop PV, a battery and two van chargers. His installer says the grid operator has "no capacity in
this area". Nobody can tell him if that's true, for how long, or what he can do instead. The answer is
scattered across PDFs from several organisations that don't share a vocabulary.

_A sourced national statistic and a real interview quote will be added here once collected (SPEC tickets
C-T26/C-T27). Unsourced numbers are deliberately left out._

## 🧠 The insights we're building on

1. **Capacity has a direction.** Congestion is registered separately for feed-in (*teruglevering*) and
   consumption (*afname*). A site can have no room to export solar while having plenty to run a workshop.
2. **A *codeerprognose* is explicitly non-binding, and it moves.** Presenting an indicative date as a promise is
   the most common way this information misleads people. Every date carries its binding status and source.
3. **"No capacity" is not the end of the conversation.** Non-firm (*niet-firm*) connections, flexibility
   contracts, time-shifting and group arrangements are real routes. The useful output is a ranked plan with
   the application route for each.

---

## 🛡️ How the gate works (built)

The gate (`backend/app/gate/gate.py`) is pure Python: no model calls, no network. A test parses its imports
and fails if any HTTP or model client appears. For each claim it returns one of three verdicts:

| Verdict | When | Effect |
|---|---|---|
| `FAIL` | The evidence quote does **not** occur in the source document (paraphrase or fabrication) | Claim rejected (`quote_not_found_in_document`) |
| `UNDETERMINED` | No quote, no source text, quote under 10 characters, an unparseable date, or the quote exists but **does not state** the asserted date / kW value | Value dropped; the answer abstains instead of guessing |
| `PASS` | The quote is in the source **and** every asserted date and kW figure appears in the quote | Claim may be shown with its source |

Matching is case-sensitive. Only text-extraction artefacts are normalised: whitespace and line breaks,
hyphenation at line ends, non-breaking spaces, curly quotes and dashes. Dates are matched in Dutch and English
("Q3 2028", "derde kwartaal van 2028", "14 juli 2028"), and the quarter, half or month must sit next to the
year. kW figures accept Dutch and English number formats and MW→kW conversion. The gate checks that a value
is **stated**, not that the sentence **means** it; that's why the quote is always shown to the user. The A/B
run measures this gap: a real publication date presented as the availability date, a 60 kW threshold read as
capacity, a consumption figure used for feed-in, and a "binding" claim backed by a non-binding sentence all pass.

---

## 🧪 Evidence by judging criterion

Each section says what is built, what is measured, and what has **not** been run. Commands reproduce every number.

### Technological Implementation

**Tavily + Nemotron Ultra + Token Factory Sandboxes, with a deterministic gate in front of the user.**

| Component | Status | Evidence |
|---|---|---|
| **Tavily** runtime retrieval | Wired: `/search` restricted to the operator's own domain, re-checked client-side, then `/extract`; every call ledgered. **Not yet run against the live API** | `backend/app/tools/tavily.py`, mocked tests in `backend/tests/test_tavily.py` |
| **Nemotron Ultra** extraction on Nebius Token Factory | Wired: OpenAI-compatible API, `response_format` `json_schema`, temperature 0; invalid output → abstention. Model id `TODO_VERIFY(C-T02)`. **Not yet called**; offline mode replays recorded SYNTHETIC output | `backend/app/stages/s3_extract.py` |
| **Deterministic citation gate** | Built: pure Python, 0 LLM calls; quote-in-source, date-in-quote, kW-in-quote, binding evidence, route evidence | `backend/app/gate/gate.py`, `backend/app/stages/s5_answer.py` |
| **Token Factory Sandbox** application pack | Built as a network-off guest command: re-hashes every document, re-verifies every citation, date and kW, and withholds the pack on any failure. **Not yet run in a Sandbox** (runbook in `reports/C-T21-T23.TASK_REPORT.md`) | `backend/app/sandbox/pack.py`, `backend/tests/test_sandbox_pack.py` |
| Gate-on vs gate-off A/B | Measured as two local arms from one snapshot, not yet as Sandbox branches | `make ab` → `runs/ab_experiment_results.json` |
| **Nebius Serverless Job** sweep | Job + container written; **not yet submitted** | `jobs/sweep_50_postcodes.py`, `jobs/Dockerfile` |

**A/B measured delta** (`make ab`; SYNTHETIC adversarial set, 29 hand-written cases, 36 labelled values). Each cell counts labelled
values that reached the final answer:

| Labelled values | Gate OFF | Gate ON | Note |
|---|---|---|---|
| Fabricated dates | 10/10 | **0/10** | dates not stated in the quoted source |
| Fabricated kW figures | 6/6 | **0/6** | incl. 250 → 2500 and 60 → 80 |
| Fabricated binding claims | 2/2 | **0/2** | invented "binding" / "onder voorbehoud" sentences |
| Fabricated application routes | 3/3 | **0/3** | invented energy-hub and collective routes |
| Misattributed (real quote, wrong meaning) | 5/5 | **4/5** | **the gate's known gap**: it checks that a value is stated, not what it means |
| Genuine values kept | 10/10 | **10/10** | 0 false rejects |

Gate ON ran 79 checks with 0 LLM calls. The UI shows the same table in the **A/B Gate Evidence** tab.

### Design

**Direction Cards + accessibility.**
- One Direction Card per direction: verdict, indicative date with a **binding chip**, the operator's quote
  in a source pill (document, retrieval time, sha256), ranked options with each application route quoted in Dutch,
  a gate report, and a "We will not guess" card with a copyable Dutch phone script when there is no position.
  Example (SYNTHETIC demo data): postcode 5612 AB gives feed-in *waiting list only*, Q3 2028, non-binding; consumption
  *capacity available*, 250 kW stated.
- The binding chip can be read without colour: each status has its own icon, border style (solid / dashed /
  dotted) and label.
- Keyboard and screen-reader basics in code: labelled inputs, a fieldset/legend for direction, a polite
  `aria-live` results region, an ARIA tablist with ←/→ keys, `lang="nl"` on Dutch quotes, visible
  `:focus-visible` styles, reduced-motion support. Every colour comes from `frontend/src/tokens.css`.
- **Not done:** no accessibility audit, no screen-reader test, no user testing.

### Potential Impact

**50-area sweep: a pipeline demonstration, not a finding yet.**
`jobs/sweep_50_postcodes.py` runs the same gated pipeline as `/v1/answer` for 50 postcode areas × both directions
and aggregates the share of areas with no firm capacity, the published indicative dates with their binding status,
and the operator-stated non-firm kW. Abstentions are reported separately, never counted as negatives. Failed areas
are counted, never padded.

- **Offline it reads the two SYNTHETIC fixture documents** (one Enexis, one Liander, none for Stedin). Every area
  of an operator therefore gets the same answer, so its aggregates say nothing about the Dutch grid and are not
  quoted here. What the run does show: 50 areas requested, 50 completed, 0 failed, and 16 Stedin areas
  abstaining because no document exists.
- Areas are an evenly spaced sample of the three postcode ranges the project maps today (unverified,
  `TODO_VERIFY(C-T04)`), not a curated list of commercial areas.
- **Still to do for impact evidence:** a live run (`--mode live`, both keys), submitted as a Nebius Serverless
  Job; ≥3 real interviews (SPEC §2). None have happened.

### Quality of the Idea

**The prior: an indicative date is non-binding until the operator's own words say otherwise.**
- Operators publish indicative dates (*codeerprognoses*) as estimates, and they move. GridQueue never shows a
  date without its binding status and the sentence it came from. The schema rejects a binding claim with no
  evidence quote, and an explicit non-binding marker in the document forces `non_binding`.
- Capacity has a direction (feed-in vs consumption are separate answers), and "no capacity" comes with the
  operator's own non-firm and flexibility routes.
- The refusal is a feature: with no verifiable position the answer is `NO_OFFICIAL_POSITION_FOUND` plus the
  question to ask the operator.
- **Known gap, measured:** the prior is only as strong as the marker list. A "binding" claim backed by a
  sentence that says *indicatieve* still passes (A/B case M04; see [LIMITATIONS](LIMITATIONS.md)).

**Models (planned, verify against the authenticated catalog, ticket C-T02):** `nvidia/Nemotron-3-Ultra-550b-a55b`
(position extraction), `nvidia/nemotron-3-super-120b-a12b` (options), `nvidia/nemotron-3-nano`
(pre-summarisation).

---

## 📁 Repository layout

```
├── LICENSE, README.md, LIMITATIONS.md, ARCHITECTURE.md, SPEC.md, Makefile
├── schemas/core-schemas.json   <- data contracts (JSON Schema 2020-12)
├── data/                       <- source register (template), domain lexicon, competitor subset
├── docs/                       <- delegation protocol, rubric, platform guide, decisions, CI template
├── backend/
│   ├── app/main.py             <- FastAPI app
│   ├── app/config.py           <- settings (env / .env)
│   ├── app/gate/gate.py        <- deterministic tri-state gate
│   ├── app/tf/ledger.py        <- append-only telemetry ledger
│   ├── app/sandbox/pack.py     <- offline application pack (stdlib + gate only)
│   └── tests/                  <- gate, schema-contract, ledger and API tests
├── frontend/                   <- React UI: Direction Card + A/B Gate Evidence tabs
├── jobs/ab_branch_eval.py      <- gate-on vs gate-off experiment (make ab)
├── jobs/sweep_50_postcodes.py  <- 50-area sweep, Serverless-Job ready (make sweep)
├── jobs/Dockerfile             <- one image: API (default) or sweep job
├── runs/ab_experiment_results.json <- latest A/B result (shown in the UI)
├── runs/sweep_summary.json     <- latest sweep (SYNTHETIC offline run)
├── video/script.md             <- locked 2:50 shot list
└── runs/sample_ledger.jsonl    <- example ledger line
```

## License
Apache License 2.0. See [`LICENSE`](LICENSE).
