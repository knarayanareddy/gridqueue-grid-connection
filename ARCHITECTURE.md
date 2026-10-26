# Architecture & Dataflow — GridQueue

The authoritative design is [`SPEC.md` §3](SPEC.md). This page summarises it and marks what is built.
**Legend:** ✅ built · ⏳ planned.

```mermaid
flowchart TD
    In["Address / postcode + what to connect<br/>(kW, direction, flexible?)"] --> S1
    S1["⏳ S1 resolve_location<br/>postcode → gemeente → DSO → congestion area<br/>static cited table, NO LLM, abstains if unmapped"] --> S2
    S2["⏳ S2 retrieve_documents<br/>Tavily discovery + direct fetch<br/>sha256 + retrieved_at + revision tracking"] --> S3
    S3["⏳ S3 extract_positions — Nemotron Ultra<br/>(Nano pre-summarises long PDFs)<br/>PositionClaim per direction, verbatim quote, binding status"] --> S4
    S4["⏳ S4 options — Nemotron Super<br/>non-firm, flex contract, time-shift, …<br/>each with an application route + evidence"] --> S5
    S5["S5 GATE — pure Python, no LLM<br/>✅ quote-in-source · date-in-quote · kW-in-quote<br/>⏳ TTL · binding label · route · no-position · determinism hash"] --> S6
    S6["⏳ S6 plan + application pack<br/>validated in a Token Factory Sandbox, guest network disabled"]

    S5 -->|PASS| Show["claim shown with its source"]
    S5 -->|UNDETERMINED| Drop["value dropped, answer abstains<br/>(+ Dutch phone script)"]
    S5 -->|FAIL| Rej["claim rejected, logged in gate report"]

    Ledger[("✅ runs/ledger.jsonl<br/>every model / Tavily / Sandbox call")]
    S2 -.-> Ledger
    S3 -.-> Ledger
    S4 -.-> Ledger
    S6 -.-> Ledger
```

Side lanes (all ⏳): **batch sweep** (`jobs/sweep.py` on a Nebius Serverless Job, ≥200 postcode areas incl. a
control sample) and **A/B** (Sandbox branching, gate-on vs gate-off over 60 queries, counting invented dates).

---

## Key subsystems

### 1. Contracts — `schemas/core-schemas.json` ✅
JSON Schema 2020-12 for every object that crosses a stage boundary. Many integrity rules are enforced at the
contract level, before the gate runs:
- a `PositionClaim` with an `indicative_earliest_date` must carry a `document_id`, a `verbatim_quote` and a
  non-null `publication_date` (GQ-DATE-01); dates must be ISO-like partial dates (`2028-Q3`, `2028-07`, …)
- an asserted `binding` / `non_binding` status needs the source's own words (GQ-BINDING-01)
- a kW figure needs a `capacity_basis_quote` (GQ-KW-01)
- a resolved location needs a DSO evidence citation
- a `model_estimate` option must set `model_estimate_flag` (GQ-ESTIMATE-01)
- `Citation.trust` cannot be `model_derived`

Tests: `backend/tests/test_schemas.py`.

### 2. Deterministic gate — `backend/app/gate/gate.py` ✅ (partial)
Pure Python, no network. A test parses the module's imports and rejects any HTTP or model client.
`DeterministicGate.evaluate()` returns `PASS` / `FAIL` / `UNDETERMINED` for one claim against one source
document; the semantics are in the [README](README.md#️-how-the-gate-works-built). The per-answer orchestration
from SPEC §6 (`build_answer`: TTL downgrade, binding labelling, option route checks, NO_OFFICIAL_POSITION_FOUND,
determinism hash) is not built yet.

Tests: `backend/tests/test_gate.py`.

### 3. Telemetry ledger — `backend/app/tf/ledger.py` ✅
Append-only JSONL, one line per external call, matching the `LedgerLine` contract. Writes take an exclusive
file lock so concurrent workers can't interleave lines. The location is `settings.runs_dir` (env `RUNS_DIR`,
default `<repo>/runs`). The Token Factory client wrapper that calls it (SPEC ticket C-T06) is not built yet.

Tests: `backend/tests/test_ledger.py`.

### 4. Sandbox verification — `backend/app/sandbox/` ⏳
Planned: build and validate the printable application pack inside a Token Factory Sandbox with guest networking
disabled, then record its sha256. This shows the pack only cites documents we actually hold. It is not a
guarantee against every form of leakage.
