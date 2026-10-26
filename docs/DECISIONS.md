# Decisions log

Format: date · decision · why · consequences. Newest first.

---

## 2026-10-26 · Review fixes (repo review, Phase 0)

**D-001 · Gate verdict semantics: FAIL vs UNDETERMINED.**
`FAIL` = the evidence quote provably does not occur in the source (paraphrase or fabrication →
`quote_not_found_in_document`). `UNDETERMINED` = insufficient evidence: missing quote, missing source, quote
< 10 chars, unparseable date, or the quote exists but does not state the asserted date/kW
(`date_not_in_quote`, `kw_without_quote`). *Why:* the v0 README promised "downgrade to UNDETERMINED" while the
code returned FAIL for everything. This split keeps "the model made it up" distinguishable from "we can't
confirm it". Both outcomes drop the value from the answer.

**D-002 · Gate matching is case-sensitive and normalises only extraction artefacts.**
Normalised: NFKC, whitespace and line breaks, soft hyphens, zero-width characters, curly quotes and dashes.
A hyphen at a line break is accepted both joined and kept. *Why:* the v0 exact-substring check rejected
real quotes that PDF extraction had wrapped across lines. Anything looser than this stops being "verbatim".

**D-003 · Period expressions must be adjacent to a four-digit year.**
"Q3 2028", "derde kwartaal van 2028" and "juli 2028" are accepted. A stray "Q3" elsewhere in the quote, "may"
the verb, and two-digit years ("Q3 '28") are not. *Why:* false support for a date is the exact harm this
product exists to prevent, so the gate errs towards UNDETERMINED.

**D-004 · Schema v1.0.0 → v1.1.0, despite the "FROZEN after C-T09" note.**
Changes are bug fixes, not new fields:
- the `then` branches of GQ-DATE-01, GQ-BINDING-01, GQ-KW-01, self-reported RevisionEvent and
  LocationResolution now require non-null strings (previously `"x": null` satisfied `required`)
- an ISO-like partial-date `pattern` on indicative dates (free text was accepted despite the description)
- Option `computed_profile` requires ≥1 assumption, and `model_estimate` requires the flag to be present
- `LedgerLine` and `Citation` were `$ref`s into `../../A-redflag-eu-product-safety/...`, which doesn't exist in
  this repo. They are now defined locally, from docs/PLATFORM-CAPABILITIES.md and SPEC C-T12.

**D-005 · Settings: no fake default API key.**
`nebius_api_key` defaults to `None` (was `"mock-key"`), and settings are read by pydantic-settings from the env
or `<repo>/.env`. Code must check `settings.has_nebius_key` and fall back to offline replay. *Why:* a fake key
turns "not configured" into a confusing 401 at runtime.

**D-006 · Ledger location is configurable (`RUNS_DIR`).**
v0 derived the path from the module's position on disk. Installed into site-packages (the Docker image), that
pointed inside the Python install. The jobs image sets `RUNS_DIR=/data/runs`.

**D-007 · README states build status explicitly; unsourced numbers removed.**
"Over 9,000 businesses waitlisted", "50 postal-code areas mapped" and "0 hallucinated dates" had no source or
measurement. Text copied from other project ideas (marketplace delisting orders, electronics rework,
solder boards) is removed. The headline number slot is reserved for the C-T23 A/B result.

**D-008 · CI workflow stays in `docs/ci/` until a maintainer enables it.**
The push token lacks the `workflow` scope. The CI badge is removed until the workflow exists, so it doesn't
show a broken badge. See docs/ci/README.md.

**D-009 · Explicit ruff rule selection.**
ruff 0.17 changed its default rule set. The rules are pinned in `backend/pyproject.toml` so `make check`
doesn't change meaning with the installed version.

## 2026-10-26 · C-T14-T19 (Tavily retrieval, `/v1/answer`, Direction Card)

**D-010 · Live and fixture data are never mixed.**
`/v1/answer` runs **live** only if `NEBIUS_API_KEY` and `TAVILY_API_KEY` are both set and
`MOCK_EXTERNAL_CALLS` is false. Otherwise it runs on SYNTHETIC fixtures, with `retrieval.synthetic = true`, a
disclaimer notice and a UI banner. If live retrieval fails, the answer abstains (`tavily_unavailable`) instead
of falling back to fixtures. *Why:* a silent fallback would present invented documents as the operator's
current position.

**D-011 · The model proposes, code disposes.**
Ultra returns *proposals* that must match a strict JSON schema. `s5_answer.py` keeps a value only when
`DeterministicGate` finds it in the fetched text:
- The claim quote must be verbatim. Otherwise the claim is rejected.
- The document must distinguish feed-in from afname. Otherwise the claim is rejected (`direction_conflated`).
- A date must be stated in the quote, **and** the document's publication date must be verified. Otherwise
  the date is dropped.
- A kW figure must appear in its own verbatim quote.
- A binding statement must come with its own verbatim quote. Otherwise binding becomes `unknown`.
- An explicit non-binding marker (lexicon §3) forces `non_binding`.
- An option route must be verbatim **and** name the route kind.

`llm_calls_in_gate` is always 0. Removing the gate makes the tests fail (checked by mutation).

**D-012 · Search is restricted to the operator's domain, twice.**
Tavily `include_domains` uses its default `restrict` mode. Each result URL is also re-checked client-side
before extraction. At most 3 documents are kept, ranked by Tavily score. Rejected URLs and the reasons are
returned in `retrieval.results_rejected`.

**D-013 · One direction per request.**
The ticket's API takes a single `direction`, so `per_direction` has exactly one entry. Asking both directions
means two calls.

**D-014 · Verdict and option ranking are deterministic tables.**
- Congestion not registered → `CAPACITY_AVAILABLE`, or `PARTIAL_CAPACITY` when the stated kW is below the
  request.
- Congestion registered → `WAITLIST` gives `WAITLIST_ONLY`, `CONDITIONAL` gives `NON_FIRM_ONLY`, `CLOSED`
  gives `NO_FIRM_CAPACITY`, anything else gives `UNDETERMINED`.
- Registration unknown, or no surviving claim → `NO_OFFICIAL_POSITION_FOUND`, plus the lexicon §5 phone
  script.
- Options are ranked: stated kW ≥ request first, then stated kW descending, then a fixed kind order, then id.
  No model confidence is used in ranking.

## 2026-10-26 · C-T21-T23 (offline application pack, gate-on vs gate-off A/B)

**D-015 · The pack re-verifies everything it prints, and is withheld on any failure.**
`build_pack` takes a bundle (`QueryResponse` + document texts) and re-checks it with no network:
- every document text must hash to its `sha256`;
- a citation is used only if it is `source_document`, has a matching sha256, and its quote passes GQ-QUOTE;
- every claim quote, date, kW, binding statement, option route and option kW is re-run through the gate
  against the hash-verified text.

Any failure raises `PackVerificationError` and no bytes are produced (CLI exit 2). The pack is deterministic for
a given bundle and is returned with its own sha256. It imports only the stdlib and `app.gate.gate`, so it can run in
a guest with no packages and no network.

**D-016 · The gate-off arm is a flag on S5, not a second pipeline.**
`AssembleAnswer(verify=False)` keeps the same S1–S3 snapshot and verdict tables but takes model proposals
as-is (only an unknown document id is refused, because the answer could not be built). `run_stages` was split
out of `answer_query` so both arms can start from one `RunContext`. `/v1/answer` has no way to set the flag;
a test posts `verify: false` and checks the gate still ran.

**D-017 · Four plus two counters.**
The SPEC's four counters (dates without document, kW without quote, binding not stated, option without route)
are reported as `spec_counters`. Each one is backed by a labelled `fabricated_*` counter with its total. Two
more counters are reported: `genuine` (false rejects) and `misattributed`, where the quote is real but means
something else. That counter is where the gate is weak (4 of 5 pass), and hiding it would overstate the result.

**D-018 · A verified option kW cites its own quote.**
When an option's kW figure is verified against a quote other than its route quote, S5 now adds a citation for
that quote. The pack can then show where the figure came from.

**D-019 · A/B results are committed and served read-only.**
`make ab` writes `runs/ab_experiment_results.json`. `GET /v1/ab-results` serves it (404 with the command to run
if it is missing). A test fails if the committed file differs from a fresh run (ignoring `generated_at`).
