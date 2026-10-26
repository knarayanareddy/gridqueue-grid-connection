# Limitations & Honest Failure Modes — GridQueue

> **Read this before relying on any output from this repository.** GridQueue's value is knowing when it
> cannot answer. This file is updated as the build progresses. Numbers marked _TBD_ are filled in only once
> measured.

---

## 1. What this is NOT
- **Not connection advice and not a grid operator.** It reports what operators have *published*, at a stated
  retrieval time. Only your grid operator (*netbeheerder*) can tell you what capacity you will be offered.
- **Not a forecast.** Indicative dates (*codeerprognose*) are the operator's own, explicitly non-binding
  estimates. GridQueue never produces a date of its own.
- **Not affiliated** with Enexis, Liander, Stedin, Westland Infra, Coteq, Rendo, TenneT, ACM or Netbeheer
  Nederland. Names are used only in citations.

## 2. Current build status (26 Oct 2026)
The pipeline that answers a real postcode **does not exist yet**. Only the contracts, the claim-level gate and
the ledger are built. See the build-status table in the [README](README.md). Until stages S1–S4 exist,
GridQueue answers no real-world questions.

## 3. Coverage

| Dimension | Covered | Not covered |
|---|---|---|
| Country | Netherlands (planned) | Everywhere else. A non-Dutch region is a stretch goal only |
| Grid operators | _None yet. No documents are ingested._ Planned first: the operator for North Brabant | All other Dutch DSOs until their documents are in the corpus. **This list will name each uncovered operator explicitly.** |
| Postcodes | _None yet_ (postcode → DSO table not built) | Unmapped postcodes always abstain (`unmapped_postcode`) |
| Directions | Feed-in and consumption, separately | Answers that merge the two directions are invalid by contract |
| Document types | Planned: PDF, HTML, XLSX, CSV, GeoJSON | Scanned or image-only PDFs (no OCR planned) and interactive map-only portals with no downloadable data |
| Connection scale | _TBD_: grootverbruik first | Kleinverbruik specifics (e.g. 3×25 A households) not modelled |

## 4. Known failure modes of what *is* built

| # | Failure mode | Cause | What happens |
|---|---|---|---|
| 1 | **Correct quote, wrong meaning** | The gate checks that a date or kW figure is *stated* in the quote, not that the sentence *means* it. E.g. "not before Q3 2028" supports the token `2028-Q3` | The claim passes. **Mitigation:** the verbatim quote is always shown next to the value. Planned: binding / negation marker detection from `data/domain-lexicon.md` |
| 2 | **Extraction artefacts beyond normalisation** | Ligatures, columns read out of order, or table cells flattened by PDF extraction | The quote isn't found and the claim is `FAIL`ed. This errs towards refusal, never towards invention |
| 3 | **Ambiguous number formats** | "1.250 kW" is 1250 in Dutch and 1.25 in English | Both readings are accepted as support for the asserted value. A wrong value can only pass if the quote literally contains a number that reads that way |
| 4 | **Two-digit or textual years** | "Q3 '28", "over twee jaar" | Not accepted as date support → `UNDETERMINED`. Deliberately strict |
| 5 | **Stale documents** | Operators revise registers and forecasts without notice | _Planned_ GQ-TTL-01 downgrade (60-day TTL for registers). **Not yet enforced in code** |
| 6 | **Publisher URLs rot before judging** | Operators restructure sites without redirects | _Planned_ corpus-snapshot-first design, with Tavily used to check currency |

## 5. Measured numbers
_TBD. Each row gets filled in only once measured._ Documents ingested · operators covered · postcodes mapped ·
A/B invented-date counts (gate on / off) · abstention rate · cost per answer · p50/p95 latency.
