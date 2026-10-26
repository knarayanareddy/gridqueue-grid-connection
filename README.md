# GridQueue — Energy Grid Interconnection Navigator & Flex Planner

> **Can I actually get power here, and when? GridQueue answers per direction (feed-in vs consumption) from
> official Dutch grid-operator documents, refuses to invent a date, and ranks the non-firm and flexibility
> routes you can use today.**
>
> _Headline number: pending. It will come from the gate-on vs gate-off experiment (SPEC ticket C-T23), e.g.
> "60 queries · 0 invented dates with the gate on · N without it". No figure goes here until it has been measured._

**Not legal or connection advice.** GridQueue reports what grid operators have published, at a stated
retrieval time. It does not predict capacity and is not affiliated with any grid operator.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
· [Limitations](LIMITATIONS.md) · [Architecture](ARCHITECTURE.md) · [Spec](SPEC.md)

**Target:** Nebius × NVIDIA Global AI Hackathon, Best Apps and Agents track (also eligible for Best Use of Tavily).

---

## ⚠️ Build status (honest, as of 26 Oct 2026)

This repository is in **Phase 0** of the plan in [`SPEC.md` §8](SPEC.md). The contracts and the deterministic
gate are built and tested. The retrieval → extraction → answer pipeline is **not built yet**.

| Component | Status | Where |
|---|---|---|
| Data contracts (JSON Schema, 14 types) | ✅ built, contract-tested | `schemas/core-schemas.json`, `backend/tests/test_schemas.py` |
| Deterministic citation gate: quote-in-source, date-in-quote, kW-in-quote | ✅ built, tested | `backend/app/gate/gate.py`, `backend/tests/test_gate.py` |
| Telemetry ledger (`runs/ledger.jsonl`) | ✅ built, tested; not yet wired to any model call | `backend/app/tf/ledger.py` |
| API skeleton (`/health`, `/v1/info`) | ✅ | `backend/app/main.py` |
| Design tokens | ✅ | `frontend/src/tokens.css` |
| Full answer gate (TTL, binding, route, no-position rules; determinism hash) | ⏳ planned | SPEC §6 |
| Source corpus (≥8 hashed official documents) | ⏳ not started, register is a template | `data/source-register.v0.json` |
| Postcode → DSO table | ⏳ not started | SPEC ticket C-T04 |
| Tavily retrieval, Nemotron extraction, options | ⏳ not started | SPEC §3 S2–S4 |
| Token Factory Sandbox pack, A/B branching, Serverless sweep | ⏳ not started | SPEC §3 S6, A/B and batch lanes |
| Frontend UI | ⏳ not started (only `package.json` + tokens) | `frontend/` |
| CI | ⏳ workflow written, not yet enabled | [`docs/ci/README.md`](docs/ci/README.md) |

---

## ⚡ Try it (no API key needed)

Requires [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`).

```bash
git clone https://github.com/knarayanareddy/gridqueue-grid-connection.git
cd gridqueue-grid-connection
make sample   # deterministic gate + schema contracts, offline
make check    # ruff lint + format check, mypy, full pytest suite
make api      # FastAPI on http://0.0.0.0:8000 (/health, /v1/info)
```

| Command | Needs a key? | What it proves today |
|---|:---:|---|
| `make sample` | No | The gate rejects paraphrased quotes, drops dates and kW figures that the quote doesn't state, and the schemas reject undocumented dates and unquoted binding claims |
| `make check` | No | Lint, types and the full test suite pass from a clean clone |
| `make api` | No | The service starts and reports which keys are configured |

`make demo` (live end-to-end on a real postcode) and `make batch` (Serverless sweep) are **planned**. They
are not available yet.

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
is **stated**, not that the sentence **means** it; that's why the quote is always shown to the user.

---

## 🧪 Judging criteria: plan vs evidence

Each row states the plan (from SPEC §2) and what evidence exists **now**.

| Criterion | Plan | Evidence today |
|---|---|---|
| **Technological Implementation** | Nemotron Nano/Super/Ultra routing on Token Factory; Tavily as runtime retrieval; hashed corpus with revision tracking; Sandbox network-off validation; Sandbox branching A/B; Serverless sweep; complete ledger | Gate + contracts + ledger, 100+ tests. No model calls yet |
| **Design** | Direction × date × options card; source pill on every date; greyscale-distinguishable binding chip; keyboard accessible | Design tokens only |
| **Potential Impact** | ≥200-area sweep with methodology; ≥3 real interviews | Not started |
| **Quality of the Idea** | Three insights above; refusal state (`NO_OFFICIAL_POSITION_FOUND`) shown on camera | Gate + schema enforce the refusal rules at contract level |

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
│   └── tests/                  <- gate, schema-contract, ledger and API tests
├── frontend/                   <- package.json + design tokens (UI not started)
├── jobs/Dockerfile             <- container image (sweep job pending)
└── runs/sample_ledger.jsonl    <- example ledger line
```

## License
Apache License 2.0. See [`LICENSE`](LICENSE).
