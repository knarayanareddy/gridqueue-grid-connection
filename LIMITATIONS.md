# Limitations & Honest Failure Modes — GridQueue

> **Read this before relying on any output from this repository.** GridQueue's value is knowing when it
> cannot answer. Every number below comes from a command in the repo; anything not yet measured says so.

---

## 1. What this is NOT

- **GridQueue reports official published positions, not predictive grid physics.** It reads what a grid
  operator (*netbeheerder*) has published and repeats it with the operator's own words, source and retrieval
  time. It does **not** model the grid: no load-flow or capacity calculation, no prediction of when congestion
  ends, no estimate of its own. If the operator has published nothing verifiable, the answer is
  `NO_OFFICIAL_POSITION_FOUND`.
- **Indicative forecasts (*codeerprognoses*) remain legally non-binding.** Operators publish indicative dates
  as estimates that can change. They are not a commitment to connect you or to have capacity by that date,
  and they give you no right to either. GridQueue shows every date with its binding status and the sentence it
  came from. It never presents a date as a promise and never produces a date of its own.
  `TODO_VERIFY(operator-wording)`: quote each covered operator's own non-binding statement here once official
  documents are in the corpus. The project's terminology note is in `data/domain-lexicon.md`.
- **Not connection or legal advice.** Only your grid operator can tell you what capacity you will be offered.
  A GridQueue answer does not replace a formal connection application.
- **Not affiliated** with Enexis, Liander, Stedin, Westland Infra, Coteq, Rendo, TenneT, ACM or Netbeheer
  Nederland. Names are used only in citations.

## 2. Current build status (26 Oct 2026)

| Part | State |
|---|---|
| Pipeline (postcode → operator → retrieval → extraction → gate → answer → UI) | Built. **Has only run offline on SYNTHETIC fixtures** |
| Live Tavily retrieval and Nemotron extraction | Wired and unit-tested with mocks. **Never run against the real APIs** |
| Application pack (hash re-verification, network-off guard) | Built and tested locally. **Never run in a Token Factory Sandbox** |
| Gate-on vs gate-off A/B | Measured as two local arms on a synthetic, hand-written set. **Not a measurement of real model output** |
| 50-area sweep | Job and container written; run offline on synthetic fixtures. **Never submitted as a Serverless Job; no real-grid figures** |
| Official document corpus | **Does not exist yet.** 0 official documents |

## 3. Coverage

| Dimension | Covered | Not covered |
|---|---|---|
| Country | Netherlands only | Everywhere else |
| Grid operators | **None with official documents.** Synthetic demo fixtures exist for Enexis and Liander. Stedin has no fixture, which demonstrates the abstention path | Every Dutch operator until its documents are in the corpus: Enexis, Liander, Stedin, Westland Infra, Coteq, Rendo |
| Postcodes | Three postcode4 ranges (5600–5658 Enexis/Eindhoven, 1000–1099 Liander/Amsterdam, 3000–3089 Stedin/Rotterdam; 249 values), taken from a ticket and **not verified** against the operators' service-area publications (`TODO_VERIFY(C-T04)`) | Every other postcode abstains (`unmapped_postcode`) |
| Directions | Feed-in and consumption, separately; one direction per request | Answers that merge the two directions are invalid by contract |
| Document types | Plain text from Tavily extract; synthetic text fixtures | PDF/XLSX parsing, scanned or image-only PDFs (no OCR planned), map-only portals |
| Connection scale | Not modelled (`connection_scale: "unknown"`) | Kleinverbruik specifics (e.g. 3×25 A households) |

## 4. Known failure modes of what *is* built

| # | Failure mode | Cause | What happens |
|---|---|---|---|
| 1 | **Correct quote, wrong meaning** (measured) | The gate checks that a date or kW figure is *stated* in the quote, not what the sentence *means* | In the A/B set, **4 of 5** misattributed values passed with the gate on: a publication date used as the availability date, a 60 kW eligibility threshold read as capacity, a consumption limit used for feed-in, and a "binding" claim. **Mitigation:** the verbatim quote is always shown next to the value |
| 2 | **Non-binding marker missed** (measured) | Only explicit terms ("niet bindend", "onder voorbehoud", …) force `non_binding`. "indicatief" is shown as a marker but does not force it, and the inflected "indicatieve" is not detected at all | A "binding" claim backed by an *indicatieve datum* sentence passes (A/B case M04). Fix planned: require a binding/non-binding term in the evidence quote and match inflections |
| 3 | **Extraction artefacts beyond normalisation** | Ligatures, columns read out of order, table cells flattened | The quote isn't found and the claim fails. This errs towards refusal, never towards invention |
| 4 | **Ambiguous number formats** | "1.250 kW" is 1250 in Dutch and 1.25 in English | Both readings count as support. A wrong value passes only if the quote literally contains a number that reads that way |
| 5 | **Two-digit or textual years** | "Q3 '28", "over twee jaar" | Not accepted as date support, so the date is dropped. Deliberately strict |
| 6 | **Stale documents** | Operators revise registers and forecasts without notice | GQ-TTL-01 (60-day TTL for registers) is **not enforced in code yet**. Every answer shows its retrieval time |
| 7 | **Wrong operator for a postcode** | The postcode → operator table is unverified (§3) | A wrong operator means the wrong documents are searched. Retrieval is restricted to that operator's domain, so the likely result is an abstention rather than a wrong answer |
| 8 | **Sweep aggregates on synthetic data** | Offline, the sweep reads two synthetic documents | Every area of an operator gets the same answer; the aggregates reflect only the sample split per operator. They are labelled SYNTHETIC and are not quoted as findings |

## 5. Measured numbers

| Number | Value | Source |
|---|---|---|
| Fabricated dates reaching the answer, gate OFF / ON | 10/10 / **0/10** | `make ab` → `runs/ab_experiment_results.json` (SYNTHETIC set, 29 hand-written cases) |
| Fabricated kW figures, gate OFF / ON | 6/6 / **0/6** | same |
| Fabricated binding claims / routes, gate ON | 0/2 / 0/3 | same |
| All fabricated values blocked, gate ON | 21/21 | same |
| Misattributed values passing, gate ON | **4/5** | same; failure modes 1–2 |
| Genuine values kept (false rejects) | 10/10 (0) | same |
| Values reaching the answer with the gate on that were correct | 10/14 | same (10 genuine + 4 misattributed reached it) |
| Sweep areas requested / completed / failed | 50 / 50 / 0 | `make sweep` → `runs/sweep_summary.json` (SYNTHETIC; pipeline check only) |
| Official documents in the corpus | 0 | `data/source-register.v0.json` is a template |
| Operators covered with official documents | 0 | §3 |
| Cost of the runs above | $0: no external calls | ledger; fixture mode |
| Abstention rate, p50/p95 latency, cost per answer on real queries | **Not measured.** Needs a live run | — |
