# SPEC — "GridQueue": can I actually get power here, and when?

**Idea C · Track: Best Apps and Agents · Also eligible: Best Use of Tavily ($3,000)**
**Version:** 1.0 · 26 Oct 2026 · **Build window:** Sun 26 Oct → Thu 30 Oct 2026, 19:00 CEST
**Role in the portfolio:** the **location-advantage** play. Zero competitors in energy/grid. Second pivot after Idea B.

> Read `docs/AGENT-DELEGATION-PROTOCOL.md` before dispatching any ticket.

---

## 1. Executive brief

### One-sentence pain
> *"I got a quote for 60 kW of solar on the workshop roof. The installer says the grid operator has 'no capacity
> in this area'. Nobody can tell me if that's true, for how long, or what I'm allowed to do instead. So the roof
> stays empty and I keep paying €0.34 a kWh."*

### Persona
**Ruud**, 46, owns a metalworking shop in a Brabant industrial park. 22 employees. Wants rooftop PV, a battery,
and two charge points for the vans. His installer gave up on the paperwork. He is not stupid — he is
**time-poor and the answer is scattered across nine PDFs published by four different organisations, none of
which use the same vocabulary.**

Secondary personas: **the installer** (does this ten times a week, wants a template answer), and **a housing
association / municipality** planning electrification across a portfolio of addresses.

### The 30-second hook
> Type an address (or a postcode) and what you want to connect: *"60 kW PV + 20 kW battery + 2× 22 kW chargers"*.
> Eight seconds later, above the fold:
> **"FEED-IN: NO FIRM CAPACITY REGISTERED FOR THIS AREA. CONSUMPTION: 25 kW MAY BE AVAILABLE."**
> **"The applicable non-binding forecast (codeerprognose) for your grid operator, published 14 Jul 2026,
> indicates the earliest indicative date for production capacity as Q3 2028 — it is explicitly non-binding and
> has moved twice."** ← with a link to the actual document and its retrieval timestamp
> **"Three things you can do now, ranked by how much they get you:"** [1. Apply for a non-firm (niet-firma)
> connection with a curtailment agreement — 60 kW today. 2. Register on the congestion queue — no date.
> 3. Time-shift your chargers under a flex contract — 44 kW of your 60.]
> Then, collapsed: the evidence — every date, every kW, every rule, each tied to a fetched document with a hash.

### One takeaway
**The honest answer to "can I get power here?" is a date, a direction, and a set of options — and most tools
invent the date. This one refuses to.**

### The named insider insights (there are three; say all of them in the video)
> **1. Capacity has a direction.** Congestion is registered separately for **feed-in (teruglevering / productie)**
> and **consumption (afname)**. A site can have no capacity to export solar power while having plenty to run a
> workshop — and almost every public-facing tool conflates them into one "is there capacity?" answer. Asking the
> wrong direction gives you the wrong answer with total confidence.
>
> **2. A `codeerprognose` is explicitly non-binding, and it moves.** Grid operators publish indicative forecasts
> of when capacity will return. They are not commitments. Presenting one as "you'll get capacity in Q3 2028"
> without saying it is non-binding and has already been revised is the single most common way this information
> misleads people. **This tool publishes the revision history** — which is only possible if you snapshot the
> documents over time, which is exactly what the corpus lets you do.
>
> **3. "No capacity" is not the end of the conversation.** There are structured routes that a non-specialist never
> finds: a **non-firm (niet-firma) connection** with a curtailment arrangement, a **flexibility/transport
> agreement on custom terms** (`transportovereenkomst op maat` / `flexcontract`), congestion-management
> participation, time-shifting, and group/collective arrangements. The valuable output is not a verdict — it is
> a **ranked action plan with the real application route for each**.

All three are things an intelligent outsider would not guess, and all three are demonstrable on camera.

### Why this wins against this specific field
- **Zero of 833 competitor repos** touch grid connection capacity. The whole energy/climate cluster is **8
  repos**: `crossfarm` (climate-analogue farming), `wattwise` (reschedules GPU workloads to clean grid periods —
  nearest neighbour, different problem), `bantay-ilog` (river flood warning), `PHAZE` (haze tracker), `demeter`
  (WhatsApp tiffin orders), `agrofield-agent` (post-storm soybean scouting), `agent-joules` (energy per agent
  step), `Agric_orion`. See `data/competitor-subset.csv` (25 rows incl. logistics/civic/housing neighbours).
- **You are in Eindhoven, North Brabant — Enexis territory, one of the worst congestion regions in Europe.**
  You can reach a real installer, a real SME and possibly a real grid-operator communications person in an
  afternoon. That is the customer interview Ricky and Selena both demanded, and none of the 833 repos has it.
- The **gate is the product**: refusing to invent a date in a domain where a wrong date costs someone a
  €40,000 investment decision is not a technicality, it is the entire value proposition.
- **Tavily is genuinely load-bearing** — the documents change, the forecasts get revised, the national guidance
  evolves. There is no way to hard-code this. That makes Best Use of Tavily ($3,000) a real qualification, not
  decoration.
- Nebius is **Amsterdam-headquartered** and ran a Builders & Brews in Amsterdam. A Dutch/EU infrastructure problem
  lands well with this panel.

### Scope discipline — read this now
This is a **Dutch demonstration of a generalisable pipeline**. Say that explicitly in the README and the video:
*"a generalisable retrieval-and-verification pipeline for any distribution-grid-constrained region; demonstrated
on the Netherlands because that is where the public data is worst-fragmented and where we can reach the
customers."* That framing converts a local project into a general one without any extra build. If time allows,
add **one** non-Dutch region as a second demo (a German Netzbetreiber congestion page, or an Irish/UK DSO
constraint register) to prove the generality claim — **but only after the Dutch demo is finished.**

---

## 2. Success criteria mapped to the four judging criteria

| Criterion | How GridQueue earns it | Measurable target |
|---|---|---|
| **Technological Implementation (25%)** | Nemotron tiers; **Tavily as a load-bearing runtime dependency**; a document corpus with per-document hashes + retrieval timestamps + **revision tracking**; **Sandbox network-off** validation of the generated application pack; **Sandbox branching** for gate-on/gate-off; **Serverless Job** for the postcode sweep; complete ledger | Ledger ≥95% coverage; ≥40 official documents ingested with hashes; ≥3 documents with a tracked revision; A/B delta published |
| **Design (25%)** | The answer is a **direction × date × options** card, not a wall of text; a **map**; every claim expandable to its source document with the retrieval timestamp visible; custom "utility paperwork" design system | Stranger gets a usable answer in ≤60 s; every date on screen has a visible source pill |
| **Potential Impact (25%)** | Grid congestion is a named national crisis with published numbers; **≥3 real interviews** (an SME, an installer, ideally a grid operator or municipality); **batch sweep over ≥200 postcode areas** producing an original map + table | ≥1 real quote with permission; ≥1 real cost-of-delay number from an interview; sweep published with methodology |
| **Quality of the Idea (25%)** | Three named insider insights; the gate's refusal to invent a date **shown on camera**; abstention when there is no official position; zero competitors | All three insights in README + video; the "NO OFFICIAL POSITION FOUND" state demonstrated live |

---

## 3. Architecture

```
  address/postcode + what you want to connect (kW, direction, flexible?)
        │
        ▼
 ┌────────────────────────────────────────────────────────────────────────────┐
 │ S1 resolve_location                                                        │
 │    postcode → gemeente → province → DSO (Enexis/Liander/Stedin/…) →        │
 │    TenneT region → congestion area id(s)                                   │
 │    Deterministic: a static mapping table you build from public sources,    │
 │    NOT a model guess. A wrong DSO invalidates everything downstream.       │
 └──────────┬─────────────────────────────────────────────────────────────────┘
            ▼
 ┌────────────────────────────────────────────────────────────────────────────┐
 │ S2 retrieve_documents      TAVILY + direct fetch, per query:               │
 │      • the DSO's current congestion register for this area                 │
 │      • the DSO's current codeerprognose (indicative forecast)              │
 │      • TenneT's national/regional congestion position                      │
 │      • ACM's congestion-management framework decisions                     │
 │      • national guidance published in the last 90 days                     │
 │    Every document: url, retrieved_at, sha256, publisher, publication_date, │
 │      language, extraction (PDF/XLSX/HTML), licence                         │
 │    REVISION TRACKING: compare sha256 + publication_date against previous   │
 │      snapshots in the corpus; if changed, record a revision event.         │
 │      ← this is how you can publish "this forecast has moved twice"         │
 └──────────┬─────────────────────────────────────────────────────────────────┘
            ▼
 ┌────────────────────────────────────────────────────────────────────────────┐
 │ S3 extract_positions       Nemotron ULTRA over the retrieved documents:    │
 │    For (location, direction ∈ {feed_in, consumption}, requested_kW):       │
 │      • is congestion REGISTERED for this area, in this direction?          │
 │      • is the queue OPEN, CLOSED or WAITLIST?                              │
 │      • what is the INDICATIVE earliest date, and is it BINDING?            │
 │      • what capacity class is currently offered, if any?                   │
 │      • which non-firm / flex routes are available here?                    │
 │    Output: PositionClaim[] — each with document_id, verbatim_quote,        │
 │      publication_date, binding ∈ {binding, non_binding, unknown}           │
 │    Nemotron NANO pre-summarises long PDFs to fit context; ULTRA reasons.   │
 │    ⚠ binding MUST be extracted from the document's own wording. If the     │
 │      document does not say, binding="unknown" — never assume binding.      │
 └──────────┬─────────────────────────────────────────────────────────────────┘
            ▼
 ┌────────────────────────────────────────────────────────────────────────────┐
 │ S4 options                 Nemotron SUPER: generate candidate actions       │
 │    (non-firm connection + curtailment; flex/transport agreement;           │
 │     congestion-management participation; time-shifting profile; battery    │
 │     with export limit; collective/group arrangement; queue registration;   │
 │     reduce requested capacity; phase the installation)                     │
 │    Each option: estimated_kW_enabled, prerequisites, application_route,    │
 │      who_to_contact, evidence_document_ids                                 │
 └──────────┬─────────────────────────────────────────────────────────────────┘
            ▼
 ┌────────────────────────────────────────────────────────────────────────────┐
 │ S5 GATE (pure Python, no LLM)                                              │
 │    • every DATE must be tied to a retrieved document with a publication_   │
 │      date and a sha256; no document → the date is DROPPED                  │
 │    • every kW figure must come from a document quote or from a computed    │
 │      profile, never from prose                                             │
 │    • every option must name a real application route with a citation       │
 │    • binding must be non-null; if unknown, the answer is labelled          │
 │      "binding status not stated in the source" — never silently binding    │
 │    • document age > ttl → the claim downgrades to "verify this"            │
 │    • if NO position could be established for this location+direction:      │
 │         → verdict = NO_OFFICIAL_POSITION_FOUND                             │
 │         → the answer is "call your netbeheerder, here is the exact number   │
 │            and the exact question to ask"                                  │
 │         NEVER invent a date. This refusal IS the product.                  │
 │    Deterministic; hash asserted.                                           │
 └──────────┬─────────────────────────────────────────────────────────────────┘
            ▼
 ┌────────────────────────────────────────────────────────────────────────────┐
 │ S6 plan + artifact         TOKEN FACTORY SANDBOX                           │
 │    Rank options by estimated_kW_enabled against the request; build a       │
 │    printable APPLICATION PACK: the question to ask the DSO in their own    │
 │    vocabulary, the documents to attach, the ranked options with routes,    │
 │    a one-page load-profile worksheet for the flex conversation, and every  │
 │    source with its retrieval timestamp.                                    │
 │    Validate inside the Sandbox with the GUEST NETWORK DISABLED, then       │
 │    download bytes and sha256.                                              │
 └────────────────────────────────────────────────────────────────────────────┘

 CROSS-CUTTING: citation registry · ledger · document corpus with revision history

 BATCH LANE (Nebius Serverless Job, overnight):
   jobs/sweep.py → S1..S5 over ≥200 postcode areas (all congestion-registered areas + a control sample)
     → original map + table: which areas are open/closed/waitlist, in which direction, with what indicative date
     → published at /sweep with a methodology box. THIS IS YOUR POTENTIAL-IMPACT EVIDENCE.

 A/B LANE (Sandbox branching):
   one immutable image(corpus + 60 test queries)
     ├─ branch gate_on  → how many invented/unsupported dates survive?
     └─ branch gate_off → how many?
   The delta is your headline: "without the gate, N of 60 answers contained a date with no source document."
```

### Component justification (cut anything that fails)

| Component | Serves the hook? | Verdict |
|---|---|---|
| Direction-aware positions (feed-in vs consumption) | **Yes — insight #1** | Keep |
| Binding status + revision history | **Yes — insight #2** | Keep |
| Ranked action plan with real routes | **Yes — insight #3** | Keep |
| Refusal state (NO_OFFICIAL_POSITION_FOUND) | **Yes — it IS the product** | Keep |
| Sandbox application pack | Yes — the action | Keep |
| Postcode sweep + map | Yes — Potential Impact evidence | Keep |
| User accounts / saved searches | No | **CUT** |
| Automatic application submission | No, and legally risky | **CUT** (Next Steps) |
| Real-time grid frequency / spot-price integration | No | **CUT** |
| A chatbot | No — a form gives a better answer | **CUT** |
| Non-Dutch regions | Only as a stretch after the Dutch demo is done | **Conditional** |

---

## 4. Data model

Authoritative prose here; machine-checkable contract in `schemas/core-schemas.json`.

### 4.1 `ConnectionRequest` (input)
`id, address_or_postcode, country="NL", requested: [{kind ∈ {pv, battery, ev_charger, heat_pump, industrial_load,
other}, kw, direction ∈ {feed_in, consumption, both}, flexible (bool), max_curtailable_kw (float|null),
time_window (str|null)}], asker_role ∈ {owner, installer, municipality, housing_association, other}`

### 4.2 `LocationResolution` (S1) — **deterministic, no LLM**
`postcode, gemeente, provincie, dso, dso_evidence_citation, tennet_region, congestion_area_ids[],
resolution_method ∈ {static_table, api_lookup}, resolved_at`

> Build the postcode→DSO mapping from a public source and record it. **A wrong DSO silently invalidates every
> downstream claim**, so this must be deterministic and cited, and it must abstain when a postcode is not covered
> rather than guessing.

### 4.3 `SourceDocument` (S2)
`document_id, publisher, title, url, publication_date, retrieved_at, sha256, format ∈ {pdf,xlsx,html,xml,json},
language, licence, extraction_method, pages_or_rows, is_current (bool), superseded_by (document_id|null),
revision_of (document_id|null), revision_event_id (str|null)`

### 4.4 `RevisionEvent` — the differentiator
`id, document_family (e.g. "enexis-codeerprognose-brabant"), previous_sha256, new_sha256, previous_publication_date,
new_publication_date, detected_at, what_changed (str|null), indicative_date_before (str|null),
indicative_date_after (str|null)`

> You will not have months of history. **What you CAN do in 4 days:** ingest the current documents, and where a
> document itself states its own revision history (many forecasts and registers do — "v3, revised 14 Jul 2026,
> previous indication Q1 2028 → Q3 2028"), **extract that stated history** and publish it. Then start your own
> snapshot cron so the corpus genuinely tracks revisions going forward, and say that in the README. Extracting a
> document's own stated revision history is honest and immediately publishable; pretending you tracked it
> yourself for months is not.

### 4.5 `PositionClaim` (S3)
```
{ "id":"pc_…", "location":{…}, "direction":"feed_in|consumption",
  "congestion_registered": true|false|"unknown",
  "queue_status": "OPEN|CLOSED|WAITLIST|UNKNOWN",
  "indicative_earliest_date": "2028-Q3" | null,
  "date_granularity": "year|quarter|month|exact|range|none",
  "binding": "binding|non_binding|unknown",
  "binding_evidence_quote": "…",
  "available_capacity_kw": 25.0 | null,
  "capacity_basis_quote": "…",
  "document_id": "doc_…", "verbatim_quote": "…", "page_or_row": "p.7",
  "publication_date": "2026-07-14", "confidence": 0.0-1.0 }
```

### 4.6 `Option` (S4)
`id, kind ∈ {non_firm_connection, flex_transport_agreement, congestion_management_participation, time_shift_profile,
battery_with_export_limit, collective_arrangement, queue_registration, reduce_requested_capacity, phase_installation,
other}, estimated_kw_enabled (float|null), estimate_basis ∈ {document_quote, computed_profile, model_estimate},
prerequisites[], application_route (str), who_to_contact (str), evidence_document_ids[], ranked (int),
confidence, **model_estimate_flag (bool) — when true the UI must visually mark it as an estimate, not a fact**

### 4.7 `Answer` (S5/S6)
`answer_id, request, location, per_direction: [{direction, verdict ∈ {CAPACITY_AVAILABLE, NO_FIRM_CAPACITY,
WAITLIST_ONLY, NO_OFFICIAL_POSITION_FOUND, UNDETERMINED}, headline, position_claim, gate_report}],
options_ranked[], action_first {primary, copy_targets, phone_script}, artifact {sha256, …},
gate {checks_run, checks_passed, rejected_claims[], abstentions[], determinism_hash},
cost, timings_ms, disclaimer`

`phone_script` is a small thing with outsized value: **the exact question to ask the grid operator, in their
vocabulary.** e.g. *"Is er voor postcode 5612XX, richting teruglevering, een vast (firma) transportvermogen
beschikbaar, of komt mijn aanvraag op de wachtlijst? En is een niet-firma aansluiting met een
curtailmentregeling mogelijk?"* Nobody else will think to ship that. It is the single most useful output for
Ruud, and it is trivially buildable.

### 4.8 `Rule` (`data/rules/answer-rules.json`)
Not a statute table — a **presentation and safety** rule table:
`GQ-DATE-01` (no date without a cited document), `GQ-BINDING-01` (binding must be extracted, never assumed),
`GQ-DIRECTION-01` (every answer must state its direction; a direction-less answer is invalid),
`GQ-KW-01` (kW figures must be quoted or computed, never prose), `GQ-ROUTE-01` (every option needs a real
application route with a citation), `GQ-TTL-01` (document older than TTL → downgrade to "verify this"),
`GQ-NOPOSITION-01` (no position → NO_OFFICIAL_POSITION_FOUND + phone script, never a guess),
`GQ-ESTIMATE-01` (model estimates visually flagged), `GQ-DISCLAIMER-01` (disclaimer on every answer).

---

## 5. Model & platform usage matrix

| Model / feature | Stage | Job | Why this tier |
|---|---|---|---|
| Nemotron 3 **Nano** | S2 pre-summarisation of long PDFs; S1 fallback disambiguation | Chunk a 60-page register into quotable passages cheaply | Volume work; the hard reasoning is later |
| Nemotron 3 **Super** | S4 options generation | Produce candidate actions with prerequisites and routes | Mid-tier suffices; 10× cheaper than Ultra |
| Nemotron 3 **Ultra** | S3 position extraction | Read a register + a forecast + a framework decision and extract a direction-aware, binding-aware position | This is genuinely hard multi-document legal/technical reasoning — the exact case the track text names Ultra for |
| **Structured output / JSON** | S3, S4 | Positions and options as validated schemas | Makes the gate possible |
| **Tavily** | S2 | **Load-bearing**: locate the *current* documents, because URLs and versions change constantly | Qualifies for Best Use of Tavily ($3,000). Log every call with query, timestamp, results used/rejected |
| **Cached Tokens** | S3 | The framework-decision preamble repeats per query | Measure the saving |
| **Token Factory Sandboxes** | S6 | Build + validate the application pack with networking disabled | Proves the pack is internally consistent and cites only documents you actually hold |
| **Sandboxes branching** | A/B | gate_on vs gate_off over 60 test queries → count invented dates | The headline experiment |
| **Serverless Job** | Batch | ≥200-postcode sweep overnight → original map | Track text encourages it |
| **Serverless Endpoint** | Deploy | Host the API | Track text encourages it |
| **Object Storage (AI Cloud)** | Corpus | Store PDFs + snapshots durably through judging | Optional but solves the "demo dies in December" risk elegantly |

---

## 6. The deterministic gate — pseudocode

```python
# backend/app/gate/gate.py — NO LLM CALLS. Enforced by a test that monkeypatches the TF client to raise.

DATE_RE   = re.compile(r"\b(20\d{2})(?:[-/ ](Q[1-4]|\d{1,2}|H[12]))?\b")
KW_RE     = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kW|MW)\b", re.I)

def build_answer(request, location, claims, options, docs, rules) -> Answer:
    rejected, abstentions, per_direction = [], [], []

    for direction in ("feed_in", "consumption"):
        dclaims = [c for c in claims if c.direction == direction]

        # GQ-DATE-01 — no date survives without a cited, in-TTL document.
        for c in dclaims:
            if c.indicative_earliest_date:
                doc = docs.get(c.document_id)
                if doc is None:
                    rejected.append(Reject(c, "date_without_document")); c.indicative_earliest_date = None; continue
                if not doc.verbatim_supports(c.verbatim_quote):        # substring check, code not model
                    rejected.append(Reject(c, "quote_not_found_in_document")); c.indicative_earliest_date = None; continue
                if doc.age_days(now()) > rules["GQ-TTL-01"].ttl_days:
                    rejected.append(Reject(c, "document_stale")); c.downgrade_to_verify = True

        # GQ-BINDING-01 — never assume binding.
        for c in dclaims:
            if c.binding == "unknown" and c.indicative_earliest_date:
                c.binding_label = "binding status not stated in the source"

        # GQ-KW-01 — numbers from documents or computation, never prose.
        for c in dclaims:
            if c.available_capacity_kw is not None and not c.capacity_basis_quote:
                rejected.append(Reject(c, "kw_without_quote")); c.available_capacity_kw = None

        # GQ-ROUTE-01 — every option needs a real, cited route.
        usable_options = []
        for o in options:
            if not o.application_route or not o.evidence_document_ids:
                rejected.append(Reject(o, "option_without_route")); continue
            if any(docs.get(d) is None for d in o.evidence_document_ids):
                rejected.append(Reject(o, "option_cites_missing_document")); continue
            usable_options.append(o)

        # GQ-NOPOSITION-01 — refuse rather than invent.
        if not dclaims or all(c.congestion_registered == "unknown" for c in dclaims):
            per_direction.append(DirectionResult(direction, verdict="NO_OFFICIAL_POSITION_FOUND",
                headline="We could not establish an official position for this location and direction.",
                action_first=phone_script(location, direction),
                abstentions=[Abstain("no_position",
                    "No current published register or forecast for this DSO/area/direction was retrievable. "
                    "We will not guess a date.", fix_instruction=phone_script(location, direction))]))
            continue

        per_direction.append(DirectionResult(direction, verdict=classify(dclaims), headline=…, position_claim=best(dclaims)))

    return Answer(per_direction=per_direction, options_ranked=rank(usable_options, request),
                  gate=Gate(rejected_claims=rejected, abstentions=abstentions,
                            determinism_hash=sha256_canonical(per_direction)))
```

**The A/B experiment (C-T23) is the single most persuasive artifact in this project:** run the identical 60
queries with the gate bypassed and **count how many answers contain a date with no source document.** If the
number is >0 — and with an LLM asked "when will capacity return?" it will be — you have quantified the exact
harm this product prevents. Put that number in the first line of the README.

---

## 7. Repository layout

As `docs/PLATFORM-CAPABILITIES.md §7`, plus:
```
backend/app/stages/{s1_resolve_location.py … s6_plan_artifact.py}
backend/app/gate/{gate.py,rules_loader.py,quote_check.py}
backend/app/corpus/{fetch.py,hash.py,revisions.py,pdf_extract.py}
backend/app/sandbox/{client.py,images.py,branching.py,pack.py}
backend/app/tools/tavily.py
data/geo/{postcode_dso.csv,gemeente_provincie.csv,congestion_areas.csv}
data/corpus/documents/*.pdf|json      data/corpus/index.duckdb
data/corpus/revisions.jsonl           data/rules/answer-rules.json
data/fixtures/queries/*.json          eval/{queries.csv,labels.csv,run_eval.py}
jobs/{Dockerfile,sweep.py}            frontend/src/{tokens.css,routes/,components/,map/}
```

---

## 8. Phase plan & exit criteria

| Phase | Window | Exit criterion |
|---|---|---|
| **0** | Sun 26 Oct → 23:00 | Repo + licence + CI; credits confirmed; catalog snapshot; **≥8 official source documents located and hashed**; postcode→DSO table built for ≥1 province; answer-rules v0; design tokens; hook doc |
| **1** | Sun 23:00 → Mon 09:00 | Schemas frozen; citation registry + ledger + **document corpus with hashes** live; golden fixtures; `make check` green from clean clone |
| **2** | Mon → 23:00 | **One real postcode → a direction-aware answer with cited dates on screen.** Screen-record it |
| **3** | Tue 28 Oct | ≥40 documents ingested; ≥3 revision events extracted; Sandbox pack validated network-off; A/B invented-date count; ≥200-postcode sweep launched; 3 interviews; abstention proven |
| **4** | Wed 29 Oct 08:00–16:00 | **FEATURE FREEZE.** Map + UI states + accessibility; deployed; reachable from incognito + mobile; LIMITATIONS with real numbers |
| **5** | Wed 16:00 → Thu 30 Oct 18:00 | Video ≤2:50 public; README complete; Devpost copy + feedback; clean-clone test; **SUBMITTED** |

---

## 9. Task tickets

### Phase 0 — Commit & de-risk (Sun 26 Oct)

```
ID: C-T01  TITLE: Bootstrap repo, licence, CI, Makefile
PHASE: 0   OWNER: devops-agent  DEPENDS_ON: —  BLOCKS: all
SPEC: Identical to A-T01. Plus: a `make corpus` target that (re)fetches and re-hashes the document corpus, and
      a `make sample` target that runs one committed fixture query end to end with NO API key (replayed
      responses) so a judge can try it instantly.
ACCEPTANCE: `make check` green on skeleton; `make sample` runs offline with no key.
VERIFY: git clone <url> /tmp/t && cd /tmp/t && make check && make sample
```

```
ID: C-T02  TITLE: Credits + authenticated model catalog snapshot
PHASE: 0   OWNER: backend-agent DEPENDS_ON: C-T01  BLOCKS: C-T06, C-T09
SPEC: As A-T02. Additionally confirm a model with a **long context window** is available (Ultra) — this project
      feeds whole registers into one call, so context length is a hard constraint. Record the context limit per
      model in docs/MODEL-USAGE.md and design the Nano pre-summarisation stage around it. Note the competitor-
      observed **16,000-token output limit on Ultra** and chunk accordingly.
ACCEPTANCE: snapshot committed; context limits recorded; three ledger lines.
VERIFY: jq -r '.[] | select(.id|test("nemotron";"i")) | [.id, .context_length] | @tsv' data/model-catalog.snapshot.json
```

```
ID: C-T03  TITLE: Source discovery — locate the real documents (HUMAN + data-agent, the critical path)
PHASE: 0   OWNER: human + data-agent  DEPENDS_ON: C-T01  BLOCKS: C-T05, C-T14
DELIVERABLE: data/source-register.v0.json (populate it) ; docs/DATA-SOURCES.md
SPEC: For each entry in data/source-register.v0.json, find the CURRENT live URL, fetch it, record sha256,
      publication_date, publisher and licence. Use Tavily for discovery where a URL is unknown — this is a
      legitimate early use of the API and proves it works.
      ⚠️ URLs for government and grid-operator publications change constantly. DO NOT hard-code from memory or
      from this spec. Discover, verify, record, and design the retrieval layer to re-discover at runtime.
      Minimum set to locate today: (1) one DSO congestion register (start with the one for your own region —
      Enexis if you are in Brabant), (2) that DSO's codeerprognose / indicative forecast, (3) TenneT's national
      congestion position, (4) at least one ACM decision on the congestion-management framework,
      (5) one national/sector overview of where congestion exists.
ACCEPTANCE: ≥8 documents fetched and hashed; ≥1 DSO register; ≥1 forecast; ≥1 ACM decision; docs/DATA-SOURCES.md
            records publisher, URL, publication date, retrieval timestamp, sha256 and licence for each.
VERIFY: python scripts/verify_corpus.py --min-documents 8 --require-hashes
KILL CRITERION: if fewer than 4 documents are retrievable by Sun 20:00, escalate — pivot to Idea A or B.
```

```
ID: C-T04  TITLE: Postcode → gemeente → province → DSO mapping table (deterministic)
PHASE: 0   OWNER: data-agent    DEPENDS_ON: C-T01  BLOCKS: C-T11
DELIVERABLE: data/geo/postcode_dso.csv ; data/geo/gemeente_provincie.csv ; data/geo/congestion_areas.csv ;
             scripts/build_geo.py ; docs/DATA-SOURCES.md (geo section)
SPEC: Build from public sources (a national open-data postcode→gemeente dataset; each DSO's published service
      area list). Four-digit postcode granularity is sufficient. Include the DSO's own evidence citation for
      every mapping row. Where a postcode is not covered, the resolver MUST abstain rather than guess.
      Dutch postcode ranges map cleanly to municipalities; verify against a second source for ≥20 rows.
ACCEPTANCE: ≥1 full province covered at 4-digit granularity (target: all of NL); 20 spot-checked rows correct;
            unmapped postcodes return an explicit abstain; every row has a source citation.
VERIFY: python scripts/build_geo.py --verify --sample 20
```

```
ID: C-T05  TITLE: Answer-rules v0
PHASE: 0   OWNER: data-agent + human  DEPENDS_ON: C-T03  BLOCKS: C-T18
DELIVERABLE: data/rules/answer-rules.json
SPEC: The nine GQ-* rules from SPEC §4.8, each with: rule_id, statement, detector, severity, ttl_days where
      applicable, and a plain-Dutch and plain-English user-facing message. Include the phone-script templates
      per DSO and per direction (GQ-NOPOSITION-01) — write these in correct Dutch, using the operators' own
      vocabulary (transportvermogen, firma/niet-firma, teruglevering, afname, wachtlijst, congestiemanagement,
      flexcontract, curtailment). Have a native speaker check them.
ACCEPTANCE: 9 rules; every rule has a detector name that exists in the gate module's dispatch table; phone
            scripts in NL and EN for ≥3 DSOs, checked by a native speaker (record who).
VERIFY: jq '.rules | length' data/rules/answer-rules.json && jq -r '.rules[].rule_id' data/rules/answer-rules.json
```

```
ID: C-T06  TITLE: Token Factory client wrapper + ledger + cached-token accounting
PHASE: 0   OWNER: backend-agent DEPENDS_ON: C-T02  BLOCKS: all model stages
SPEC: As A-T06, plus explicit handling for long-document inputs: chunking with overlap, per-chunk ledger lines,
      and a `context_truncated` status when a document exceeds the model's window. Truncation must never be
      silent — a truncated document cannot support a date claim.
ACCEPTANCE: a 60-page PDF is chunked, each chunk logged; a deliberately over-long input produces
            status="truncated" and the gate refuses to accept any claim citing it.
VERIFY: cd backend && uv run pytest tests/test_ledger.py tests/test_chunking.py -q
```

```
ID: C-T07  TITLE: Design system — "utility paperwork"
PHASE: 0   OWNER: frontend-agent DEPENDS_ON: C-T01  BLOCKS: C-T13, C-T20
CONTEXT: docs/JUDGING-RUBRIC.md §3
DELIVERABLE: frontend/src/tokens.css ; frontend/src/components/primitives.tsx ; docs/DESIGN.md
SPEC: Metaphor = a grid operator's written determination letter, modernised. Palette: utility blue-grey #1B2A38,
      paper #F4F2ED, live-wire amber #F2A900 for "non-binding / indicative", a firm-capacity green #2C7A4B,
      a no-capacity red #B3352C, and a slate #7C8794 for unknown/abstained. Type: a neutral humanist sans for
      body; **monospace for every date, kW figure, postcode, sha256 and retrieval timestamp** — the numbers are
      the product, so they must look like data, not prose. Hairline rules, left-aligned, generous line length
      control, no cards-within-cards.
      Primitives: DirectionCard (feed-in / consumption side by side — insight #1 made visible), DateClaim
      (mono date + binding chip + source pill + retrieved_at), BindingChip (BINDING / NON-BINDING / UNKNOWN —
      never visually identical), OptionCard (rank, estimated kW with an ESTIMATE flag when model-derived,
      route, contact), PhoneScriptCard (copyable Dutch text), EvidenceDrawer, MapPanel, ProgressRail,
      StopButton, AbstentionNotice.
      FORBIDDEN: purple→pink gradients; glassmorphism; emoji iconography; centred hero + 3 cards; raw Tailwind
      colour classes in components; any stock map-tile styling left unmodified; a date rendered in a body font.
ACCEPTANCE: docs/DESIGN.md explains the metaphor; DirectionCard renders two directions with visibly different
            verdicts; BindingChip's three states are distinguishable in greyscale AND for deuteranopia;
            a screenshot is committed.
VERIFY: cd frontend && npm run build && npx tsc --noEmit
```

```
ID: C-T08  TITLE: Hook doc + persona doc + the three insights (CONTENT)
PHASE: 0   OWNER: content-agent DEPENDS_ON: —  BLOCKS: C-T20, C-T37, C-T40
DELIVERABLE: docs/HOOK.md
SPEC: One page: the 30-second hook with exact on-screen strings; Ruud in his own words; **all three insights**
      as single sentences; the one takeaway; the cut list; and the "generalisable pipeline, Dutch demonstration"
      framing sentence from SPEC §1.
ACCEPTANCE: ≤1 page; reads aloud in ≤45 s; three insight sentences with no hedge words; the framing sentence present.
```

### Phase 1 — Contracts

```
ID: C-T09  TITLE: Freeze core schemas
PHASE: 1  OWNER: backend-agent DEPENDS_ON: C-T04, C-T05  BLOCKS: all
DELIVERABLE: schemas/core-schemas.json ; backend/app/models.py ; backend/tests/test_schemas.py
SPEC: Transcribe SPEC §4 into JSON Schema + Pydantic v2. Round-trip every fixture. Key integrity assertions:
      a PositionClaim with indicative_earliest_date set but document_id null MUST fail validation;
      a PositionClaim with binding=null MUST fail validation (unknown is a valid enum value, null is not);
      an Option with estimate_basis="model_estimate" MUST carry model_estimate_flag=true.
ACCEPTANCE: all fixtures validate; the three integrity assertions each have a failing-input test.
VERIFY: cd backend && uv run pytest tests/test_schemas.py -q
```

```
ID: C-T10  TITLE: Document corpus with hashes + revision tracking
PHASE: 1  OWNER: data-agent    DEPENDS_ON: C-T03  BLOCKS: C-T12, C-T15
DELIVERABLE: backend/app/corpus/{fetch.py,hash.py,revisions.py,pdf_extract.py} ; data/corpus/index.duckdb ;
             data/corpus/revisions.jsonl ; tests/test_corpus.py
SPEC: fetch(url) → bytes + sha256 + retrieved_at + content-type. PDF/XLSX/HTML text extraction with page/row
      numbers preserved (so a quote can be located). index.duckdb over SourceDocument. revisions.py: on each
      fetch, compare sha256 and publication_date against the stored snapshot for the same document_family; on
      change, append a RevisionEvent. ALSO: parse a document's OWN stated revision history where present
      (version tables, "previous indication" wording) and record those as RevisionEvents with
      source="document_self_reported" — that is how you can publish revision history on day one, honestly.
      verbatim_supports(quote) does an exact normalised-substring check against the extracted text and returns
      the page/row where it was found. THIS FUNCTION IS THE GATE'S BACKBONE.
ACCEPTANCE: ≥8 documents indexed with hashes; re-fetching an unchanged document produces no RevisionEvent;
            a changed document produces one; ≥1 document_self_reported revision extracted;
            verbatim_supports returns True for a real quote and False for a paraphrase (test both).
VERIFY: cd backend && uv run pytest tests/test_corpus.py -q && jq -s length data/corpus/revisions.jsonl
```

```
ID: C-T11  TITLE: S1 resolve_location (deterministic, no LLM)
PHASE: 1  OWNER: backend-agent DEPENDS_ON: C-T04, C-T09  BLOCKS: C-T19
DELIVERABLE: backend/app/stages/s1_resolve_location.py ; tests/test_s1.py
SPEC: Pure lookup over data/geo/*.csv. Returns LocationResolution with a citation for the DSO assignment.
      Abstains when the postcode is unmapped, malformed, or outside NL (unless a non-NL region has been added).
      NO model call. Determinism asserted.
ACCEPTANCE: 50 test postcodes resolve to the correct DSO (spot-check ≥10 by hand against the operator's own
            service-area page and record the URLs); unmapped input abstains; zero LLM calls in the module.
VERIFY: cd backend && uv run pytest tests/test_s1.py -q
```

```
ID: C-T12  TITLE: Citation registry (document citations are first-class)
PHASE: 1  OWNER: backend-agent DEPENDS_ON: C-T10  BLOCKS: C-T18
DELIVERABLE: backend/app/citations.py ; tests/test_citations.py
SPEC: As A-T10, with kind="source_document" (locator = document_id + url + publication_date, quote = verbatim,
      sha256 required, ttl from answer-rules GQ-TTL-01) and kind="computed" (locator = the computation and its
      inputs, ttl=null, trust=primary). trust="model_derived" rejected. A citation whose sha256 does not match
      the corpus entry is rejected.
ACCEPTANCE: a citation with a mismatched sha256 is rejected; a stale document citation expires; model_derived raises.
VERIFY: cd backend && uv run pytest tests/test_citations.py -q
```

```
ID: C-T13  TITLE: Backend + frontend skeletons
PHASE: 1  OWNER: backend-agent + frontend-agent  DEPENDS_ON: C-T07, C-T09  BLOCKS: C-T20
SPEC: Backend: GET /healthz; POST /api/answer; GET /api/answer/{id}; GET /api/answer/{id}/events (SSE);
      GET /api/corpus (list documents with hashes, publication dates, revision counts — public transparency
      page); GET /api/sweep; GET /api/ledger/summary. CORS for the deployed origin + localhost.
      Frontend routes: / (the query form), /answer/:id, /corpus, /sweep, /dev/tokens. Vite proxy /api → :8000.
ACCEPTANCE: /api/corpus returns ≥8 documents with hashes; frontend builds with zero external network references
            except the map tile provider (which must be self-hostable or gracefully degrade).
VERIFY: cd backend && uv run pytest tests/test_api.py -q && cd ../frontend && npm run build
```

```
ID: C-T14  TITLE: Tavily integration — discovery AND runtime currency
PHASE: 1  OWNER: backend-agent DEPENDS_ON: C-T06, C-T10  BLOCKS: C-T15
DELIVERABLE: backend/app/tools/tavily.py ; backend/app/corpus/discover.py ; tests/test_tavily.py
SPEC: Two modes. (1) DISCOVERY: given a query like "Enexis congestieregister Noord-Brabant 2026", return ranked
      candidate URLs; the corpus fetcher validates each before ingesting. (2) RUNTIME CURRENCY: per answer,
      check whether a newer version of each cited document exists, and whether national guidance changed in the
      last 90 days. Log every call: query, results_returned, results_used, results_rejected, rejection reasons,
      latency, cost. Rejected results are RECORDED, not silently dropped — showing "6 results, 2 used, 4
      rejected as stale or off-topic" is exactly the evidence display Telltale was praised for.
      If Tavily is unreachable the run continues on the cached corpus but the answer is labelled
      "currency check unavailable — corpus snapshot from <date>" and may not claim to be current.
ACCEPTANCE: discovery finds ≥5 of the 8 seed documents from a cold query; a runtime call is logged per answer;
            with Tavily disabled the answer degrades visibly and honestly.
VERIFY: cd backend && uv run pytest tests/test_tavily.py -q && jq 'select(.kind|startswith("tavily"))' runs/ledger.jsonl | head
```

```
ID: C-T15  TITLE: Golden-fixture harness + offline replay
PHASE: 1  OWNER: eval-agent    DEPENDS_ON: C-T10, C-T14  BLOCKS: C-T33
DELIVERABLE: backend/tests/golden/ ; backend/tests/conftest.py ; eval/queries.csv
SPEC: VCR-style recorded responses so `pytest --offline` costs nothing and never flakes. 10 golden queries with
      hand-written expected answers, covering: a congested area with a non-binding forecast; an open area; a
      waitlist-only area; a location where feed-in is congested but consumption is not (**the key fixture for
      insight #1**); an unmapped postcode → abstain; a stale document → downgrade; a query with no official
      position → NO_OFFICIAL_POSITION_FOUND. eval/queries.csv = 60 rows for the A/B experiment.
ACCEPTANCE: `pytest -q --offline` green with zero network; the direction-split fixture produces two different
            verdicts for the same address.
VERIFY: cd backend && uv run pytest -q --offline
```

### Phase 2 — Spine (Mon 27 Oct)

```
ID: C-T16  TITLE: S2 retrieve_documents
PHASE: 2  OWNER: backend-agent DEPENDS_ON: C-T10, C-T11, C-T14  BLOCKS: C-T17
SPEC: Given a LocationResolution, resolve the document set: the DSO's register for the congestion area, the
      DSO's forecast, the national position, the framework decision, and any recent guidance found via Tavily
      discovery. Fetch, hash, index, extract text with page/row numbers, and detect revisions. Cache by
      (url, sha256) so repeated queries don't re-fetch. Respect rate limits and publisher politeness; set a
      real User-Agent identifying the project. On any fetch failure, record it and continue with what was
      retrieved — a partial corpus with an honest note beats a total failure.
ACCEPTANCE: for 5 real postcodes across ≥2 DSOs, ≥3 documents retrieved each with hashes; a deliberately broken
            URL degrades gracefully with a visible note; no re-fetch on a cache hit.
VERIFY: cd backend && uv run pytest tests/test_s2.py -q
```

```
ID: C-T17  TITLE: S3 extract_positions (Nano chunk → Ultra reason)
PHASE: 2  OWNER: backend-agent DEPENDS_ON: C-T16, C-T09  BLOCKS: C-T18
DELIVERABLE: backend/app/stages/s3_extract_positions.py ; backend/app/prompts/{summarise,extract_positions}.md ;
             tests/test_s3.py
SPEC: Nano pass: for each document, extract candidate passages containing dates, kW figures, area names, queue
      status words and binding language — each with its page/row. Ultra pass: given the request, the location and
      the candidate passages, emit PositionClaim[] with verbatim_quote, document_id, page_or_row, binding and
      binding_evidence_quote, per direction.
      ENFORCE IN CODE: verbatim_quote must pass corpus.verbatim_supports(); a quote that is a paraphrase is
      rejected and the claim dropped. binding must be one of the three enum values extracted from the document's
      own wording — if the document does not state it, binding="unknown" (never a silent default to binding).
      A claim whose cited document was truncated in context is rejected (see C-T06).
      Report the Nano→Ultra hand-off so you can publish "Nano screened N passages, Ultra reasoned over M".
ACCEPTANCE: on 5 golden fixtures, positions match hand labels; a mocked paraphrased quote is rejected;
            binding="unknown" is produced when the source is silent (test with a fixture that omits it);
            direction split works on the key fixture.
VERIFY: cd backend && uv run pytest tests/test_s3.py -q
```

```
ID: C-T18  TITLE: S4 options + S5 gate
PHASE: 2  OWNER: backend-agent DEPENDS_ON: C-T05, C-T12, C-T17  BLOCKS: C-T19
DELIVERABLE: backend/app/stages/{s4_options.py,s5_gate.py} ; backend/app/gate/{gate.py,rules_loader.py,quote_check.py} ;
             tests/test_gate.py
SPEC: S4 = Super generates candidate Options with routes and evidence_document_ids. S5 = SPEC §6 exactly, pure
      Python, no LLM imports (assert with a monkeypatch test). Implement all nine GQ-* rules. Build the
      phone_script from the rule templates per DSO + direction. Classify per direction into
      CAPACITY_AVAILABLE / NO_FIRM_CAPACITY / WAITLIST_ONLY / NO_OFFICIAL_POSITION_FOUND / UNDETERMINED.
      Determinism asserted by hash.
ACCEPTANCE: 10/10 golden fixtures produce the hand-labelled verdict per direction; a date with no document is
            dropped and appears in rejected_claims; a stale document downgrades to "verify this"; an unmapped
            postcode yields NO_OFFICIAL_POSITION_FOUND with a correct Dutch phone script; determinism stable
            across 3 runs; the gate module imports no LLM client.
VERIFY: cd backend && uv run pytest tests/test_gate.py -q
```

```
ID: C-T19  TITLE: POST /api/answer end to end
PHASE: 2  OWNER: backend-agent DEPENDS_ON: C-T11, C-T16, C-T17, C-T18  BLOCKS: C-T20, G2
SPEC: S1→S5 with SSE stage events, an abort Event, and a per-run budget guard. Concurrent-safe. Store Answer at
      runs/answers/{id}.json. Cache S1–S3 by (postcode4, direction, corpus snapshot id) so repeat queries are
      fast and cheap — and record the cache hit in the ledger.
ACCEPTANCE: a real postcode returns a direction-aware answer in <40 s cold, <3 s warm; 6 concurrent runs succeed.
VERIFY: for i in 1 2 3 4 5 6; do curl -s -XPOST localhost:8000/api/answer -H 'content-type: application/json' -d '{"address_or_postcode":"5611AA","requested":[{"kind":"pv","kw":60,"direction":"feed_in"}]}' & done; wait
```

```
ID: C-T20  TITLE: Frontend — the answer view (direction cards above the fold)
PHASE: 2  OWNER: frontend-agent DEPENDS_ON: C-T07, C-T19  BLOCKS: G2
SPEC: Above the fold, in order: (1) the query form — postcode + what you want to connect, with 6 one-click
      sample queries including one that abstains; (2) **DirectionCard × 2 side by side** — feed-in and
      consumption, each with its verdict, headline and DateClaim; (3) the primary action (phone script, copyable
      in Dutch); (4) the ranked options with estimated kW and an ESTIMATE flag where model-derived.
      BELOW the fold, collapsed: EvidenceDrawer with every PositionClaim as a row — mono date, BindingChip,
      source pill expanding inline to the verbatim quote + publication date + retrieval timestamp + sha256
      prefix + external link (new tab, noopener); the revision history for each cited document family; the
      Run cost panel; the disclaimer.
      ProgressRail with real stage names + elapsed + StopButton. Every control has a tooltip, especially the
      direction selector and the "flexible?" toggle.
ACCEPTANCE: a teammate reaches a usable answer with zero instruction in ≤60 s (timed, recorded); the same
            address shows two different verdicts by direction; every date on screen has a visible source pill;
            works at 360 px.
VERIFY: cd frontend && npm run build && timed manual test logged
```

### Phase 3 — Proof (Tue 28 Oct)

```
ID: C-T21  TITLE: S6 application pack in a Token Factory Sandbox
PHASE: 3  OWNER: sandbox-agent DEPENDS_ON: C-T18, C-T19  BLOCKS: C-T22
DELIVERABLE: sandbox/image/{Dockerfile,validate.py,templates/pack.html.j2} ; backend/app/sandbox/* ;
             backend/app/stages/s6_plan_artifact.py ; tests/test_s6.py
SPEC: One reusable image (pin the immutable UUID in docs/MODEL-USAGE.md) containing the answer rules, validate.py,
      the template and WeasyPrint. Per answer, generate a printable A4 APPLICATION PACK: the request as submitted;
      the per-direction determination with every date, its binding status and its source (publisher, title,
      publication date, retrieval timestamp, sha256 prefix, URL); the ranked options with prerequisites, routes
      and contacts; a one-page load-profile worksheet for the flex conversation (half-hourly kW by day type,
      curtailable share, battery charge/discharge window); the Dutch phone script; a source list; the disclaimer.
      Retain, download bytes, sha256 locally, compare.
ACCEPTANCE: packs generated for all 10 golden queries; local hash == sandbox hash; image UUID reused; the pack
            for a NO_OFFICIAL_POSITION_FOUND answer still renders usefully (phone script + what to ask for).
VERIFY: cd backend && uv run pytest tests/test_s6.py -q && ls runs/artifacts | wc -l
```

```
ID: C-T22  TITLE: Sandbox validator with the guest network DISABLED  ← showpiece
PHASE: 3  OWNER: sandbox-agent DEPENDS_ON: C-T21  BLOCKS: C-T37
DELIVERABLE: sandbox/image/validate.py ; backend/app/sandbox/network_off.py ; tests/test_sandbox_network_off.py
SPEC: Re-validate the finished pack inside the Sandbox with networking disabled. Checks: every date in the pack
      resolves to an embedded document record with a sha256; every binding label is present and non-null; every
      option has a route and a contact; every direction has a verdict; the phone script is in Dutch and mentions
      the correct DSO; no placeholder text; the disclaimer is present; every source citation includes a retrieval
      timestamp. Emit a signed validation report.
      **The point, and say it in the video:** the pack can be proven to cite only documents we actually hold,
      with no ability to reach the internet and fabricate a source.
ACCEPTANCE: validator passes on 10/10; a deliberately injected unsupported date FAILS validation and the pack is
            withheld; the UI shows "validated offline · sha256 …".
VERIFY: cd backend && uv run pytest tests/test_sandbox_network_off.py -q
```

```
ID: C-T23  TITLE: Sandbox branch A/B — count the invented dates  ← THE headline number
PHASE: 3  OWNER: sandbox-agent DEPENDS_ON: C-T18, C-T21  BLOCKS: C-T37, C-T40
DELIVERABLE: scripts/ab_gate.py ; runs/reports/ab-gate.json ; docs/img/ab-invented-dates.svg ; tests/test_ab.py
SPEC: One immutable image containing the corpus snapshot and the 60 test queries. Branch twice: `gate_on` and
      `gate_off` (model output becomes the answer directly). Run the identical 60 queries down both arms.
      Count, per arm: answers containing a DATE with no supporting document; answers containing a kW figure with
      no quote; answers stating binding status the source never gave; answers with an option lacking a route.
      Publish the delta as a bar chart and one sentence.
      Expected result: gate_off invents dates, gate_on refuses. **If gate_off invents zero, say so honestly —
      and then report the abstention rate instead, which will still show the difference.**
ACCEPTANCE: both arms n=60; the four counters reported per arm; the chart renders; the README's first line states
            the delta with real numbers.
VERIFY: python scripts/ab_gate.py --report && jq '.arms[] | {arm,n,dates_without_document,kw_without_quote}' runs/reports/ab-gate.json
```

```
ID: C-T24  TITLE: Postcode sweep as a Nebius Serverless Job  ← Potential Impact evidence
PHASE: 3  OWNER: devops-agent  DEPENDS_ON: C-T19  BLOCKS: C-T25
DELIVERABLE: jobs/Dockerfile ; jobs/sweep.py ; docs/SWEEP-METHODOLOGY.md
SPEC: Submit a Serverless Job that runs S1–S5 (skip S6) over **≥200 postcode areas**: every area with a
      registered congestion condition, plus a random control sample of areas without, so the map is not
      cherry-picked. For each: feed-in verdict, consumption verdict, queue status, indicative date + binding
      status, source document id, abstention flag. Be polite: cache aggressively (S1–S3 are cacheable by
      postcode4 + corpus snapshot), ≤1 req/2s to any publisher, real User-Agent.
      Emit runs/reports/sweep-YYYYMMDD.json. Report n_completed and n_failed separately. **Never pad.**
      Publish at /sweep as a map + table with a full methodology box: n, area selection method, corpus snapshot
      id and date, dates of the run, cache policy, exclusions, known biases (e.g. "areas where the operator
      publishes no machine-readable register are abstentions, not negatives").
ACCEPTANCE: job completes; n_completed ≥200; per-area results include direction, binding status and source;
            total cost logged; methodology box complete and honest about abstentions.
VERIFY: jq '.summary' runs/reports/sweep-*.json
FALLBACK: run the identical script locally as a long process; record runner="local_process" honestly.
```

```
ID: C-T25  TITLE: /sweep and /corpus pages — results and sources in public
PHASE: 3  OWNER: frontend-agent DEPENDS_ON: C-T24, C-T10  BLOCKS: C-T37
SPEC: /sweep = a Leaflet map (self-hosted tiles or a provider that will not die in December; degrade to a table
      if tiles fail) coloured by feed-in verdict, with a toggle for consumption verdict, plus a sortable table
      and the methodology box. /corpus = **every document in the corpus with publisher, title, URL, publication
      date, retrieval timestamp, sha256, and revision count.** Publishing your entire source list is the single
      strongest trust signal available to this project and costs one page.
ACCEPTANCE: every number on /sweep matches the JSON (scripted diff); /corpus lists ≥40 documents with hashes;
            the map degrades to a table when tiles are blocked.
VERIFY: python scripts/check_sweep_page_matches_report.py
```

```
ID: C-T26  TITLE: Abstention paths + the "we will not guess" demo
PHASE: 3  OWNER: eval-agent    DEPENDS_ON: C-T18  BLOCKS: C-T38
DELIVERABLE: data/fixtures/abstention/*.json ; tests/test_abstention.py
SPEC: Prove every abstention path on real inputs: an unmapped postcode; an area with no published register; a
      stale document beyond TTL; a Tavily outage; a budget exhaustion; a truncated document; a direction with no
      position while the other direction has one. Each must produce a calm, useful state with a **concrete next
      action** (usually the Dutch phone script). This is the on-camera heart of the project.
ACCEPTANCE: 7/7 abstain correctly with distinct reason codes; each carries a phone script or an equivalent next
            action; the UI state is visually distinct from "no capacity" (never alarm someone for a data gap).
VERIFY: cd backend && uv run pytest tests/test_abstention.py -q
```

```
ID: C-T27  TITLE: Talk to 3 real people (HUMAN TASK — your location advantage)
PHASE: 3  OWNER: human         DEPENDS_ON: C-T20  BLOCKS: C-T37, C-T40
SPEC: Find 3: (a) an SME owner who has been refused or delayed a connection — Brabant is full of them;
      (b) a solar/PV or electrical installer who files these requests weekly; (c) ideally someone at a
      municipality, a housing association, or a grid operator's communications team. Show them the demo. Ask:
        1. What did you actually want to connect, and what happened?
        2. How did you find out? Who told you? How long did it take?
        3. What did the delay cost you — in euros, in months, in a project you cancelled?
        4. Did anyone offer you a non-firm connection or a flex contract? Did you understand what that meant?
        5. Would a tool that gives you a dated, sourced answer and a ranked action plan be useful? Where would
           it mislead you?
      Record one 20-second clip OR one quotable sentence + first name and role, with permission. Write
      reports/C-T27.INTERVIEWS.md. **You need at least one real euro figure for the cost of delay** — that is
      your Potential Impact number and no public statistic will give it to you.
ACCEPTANCE: 3 conversations documented; ≥1 usable quote with permission; **≥1 real cost-of-delay figure with its
            source named**; ≥1 product change logged in DECISIONS.md.
NOTE: Ricky, verbatim: *"even if you're not a subject matter expert… you should be going out and talking to
      potential customers before you build any features."*
```

```
ID: C-T28  TITLE: Revision-history extraction (insight #2, made real)
PHASE: 3  OWNER: data-agent    DEPENDS_ON: C-T10  BLOCKS: C-T25, C-T37
SPEC: For each document family, extract any self-reported revision history (version tables, "v3, revised …",
      "previous indication …"). Emit RevisionEvents with source="document_self_reported". Where a forecast's
      indicative date has moved, publish **before → after → source quote**. Set up an hourly/daily snapshot cron
      (a GitHub Action on a schedule is free and durable) so the corpus genuinely tracks revisions from now on,
      and state in the README that live tracking began on <date> while the historical revisions are the
      documents' own.
ACCEPTANCE: ≥3 RevisionEvents with source="document_self_reported"; ≥1 showing a date that moved, with quotes for
            both; the scheduled snapshot Action committed and its first run logged.
VERIFY: jq -s 'map(select(.source=="document_self_reported")) | length' data/corpus/revisions.jsonl
```

```
ID: C-T29  TITLE: Ledger aggregates + cost report
PHASE: 3  OWNER: backend-agent DEPENDS_ON: C-T06, C-T24  BLOCKS: C-T37
SPEC: As A-T33/B-T33: totals, per-model and per-stage cost, cache-hit rate (this project caches heavily —
      report it), p50/p95 latency, failure counts by class, Tavily call economics (calls, $, % results used),
      Nano→Ultra hand-off volumes, and the all-Ultra counterfactual. Publish the table with interpretation.
ACCEPTANCE: docs/MODEL-USAGE.md has real numbers incl. the counterfactual and the cache-hit rate;
            GET /api/ledger/summary returns the same JSON.
VERIFY: python scripts/ledger_report.py --markdown > docs/MODEL-USAGE.md && grep -c "US\$" docs/MODEL-USAGE.md
```

```
ID: C-T30  TITLE: Load-profile computation for the flex conversation (the practical half of insight #3)
PHASE: 3  OWNER: backend-agent DEPENDS_ON: C-T19  BLOCKS: C-T21
SPEC: A deterministic (no LLM) half-hourly load/generation profile estimator from the ConnectionRequest: PV by
      orientation-free typical curve scaled to kWp, battery charge/discharge window, EV charger sessions,
      heat pump profile, industrial base load. Then compute, per option: how much of the request each option
      actually enables, and what the curtailable share would have to be for a non-firm connection to work.
      Every number is computed, labelled estimate_basis="computed_profile", and shown with its assumptions.
      **This is the difference between "you could get a flex contract" and "a flex contract with a 12 kW
      curtailment cap covers 44 of your 60 kW, and here is the half-hourly profile that shows it."**
ACCEPTANCE: profiles generated for all 10 golden fixtures; each option's estimated_kw_enabled traces to a
            computed value with stated assumptions; a sensitivity note shows how the answer changes if the PV
            curve is 20% worse.
VERIFY: cd backend && uv run pytest tests/test_profile.py -q
```

### Phase 4 — Polish (Wed 29 Oct) — FEATURE FREEZE

```
ID: C-T31  TITLE: Onboarding — sample queries, first-run explainer, glossary
PHASE: 4  OWNER: frontend-agent DEPENDS_ON: C-T20  BLOCKS: G4
SPEC: 6 one-click sample queries with 4-word labels, including one that abstains and one that splits by
      direction. A dismissible 2-sentence first-run overlay. A tooltip on EVERY control. And a **glossary** —
      because this domain is vocabulary-dense and a non-specialist judge will hit words they don't know:
      transportvermogen, firma/niet-firma, teruglevering, afname, codeerprognose, congestiemanagement,
      flexcontract, curtailment, netcongestie. Each glossary term expands inline with one plain sentence in
      both Dutch and English. This single component does more for the Design score than any visual polish.
ACCEPTANCE: every domain term appearing anywhere in the UI is in the glossary (scripted check); a first-time
            user completes a query with zero instruction (3 people, timed, median ≤60 s).
```

```
ID: C-T32  TITLE: Empty / loading / error / degraded states
PHASE: 4  OWNER: frontend-agent DEPENDS_ON: C-T31  BLOCKS: G4
SPEC: Seven designed states: empty; running (ProgressRail + elapsed + StopButton); partial corpus ("3 of 5
      documents retrieved — answer may be incomplete", visible); Tavily unavailable ("currency check
      unavailable — corpus snapshot from <date>"); abstained; full error with retry and reason; budget
      exhausted. Never show a raw stack trace.
ACCEPTANCE: 7 states each with a designed component and a screenshot in docs/img/states/.
```

```
ID: C-T33  TITLE: Eval — measure the gate on 60 real queries
PHASE: 4  OWNER: eval-agent    DEPENDS_ON: C-T15, C-T23  BLOCKS: C-T37
DELIVERABLE: eval/{labels.csv,run_eval.py} ; runs/reports/eval.json ; docs/EVAL.md
SPEC: Label 60 queries twice (two labelers, blind). Compute: verdict accuracy per direction; **date-support
      rate** (fraction of dates in answers backed by a cited document — must be 1.000 with the gate on);
      binding-status accuracy; abstention rate and abstention appropriateness; option-route completeness;
      Cohen's kappa between labelers. Flag classes with <5 examples as INSUFFICIENT and publish no accuracy for them.
ACCEPTANCE: kappa reported; date-support rate = 1.000 for gate_on (if not, fix the gate before anything else);
            confusion matrix committed; INSUFFICIENT flagged.
VERIFY: python eval/run_eval.py --report && jq '{date_support_rate, kappa}' runs/reports/eval.json
```

```
ID: C-T34  TITLE: Accessibility pass (and make it visible)
PHASE: 4  OWNER: frontend-agent DEPENDS_ON: C-T32  BLOCKS: G4
SPEC: Full keyboard nav with visible focus; skip link; the DirectionCards use a two-column layout that stacks
      and remains semantically ordered for a screen reader; BindingChip states distinguishable in greyscale and
      under deuteranopia simulation; colour never the only signal (glyphs on every verdict); contrast ≥4.5:1
      verified; the map has a complete table equivalent that is not hidden behind an interaction; aria-live on
      the verdict; prefers-reduced-motion; the PDF pack is tagged and screen-reader navigable. Then add an
      accessibility line to the video script and a paragraph to README + Next Steps.
ACCEPTANCE: axe-core reports 0 critical/serious violations; a keyboard-only query completes; the map's table
            equivalent is reachable without a mouse; colour-blind simulation screenshots committed.
VERIFY: cd frontend && npx @axe-core/cli http://localhost:5173 --exit
```

```
ID: C-T35  TITLE: Responsive + deploy (Serverless Endpoint + static host)
PHASE: 4  OWNER: devops-agent  DEPENDS_ON: C-T19, C-T34  BLOCKS: G4, G5
SPEC: 360/768/1280/1920 px. Containerise the backend; deploy as a **Nebius Serverless Endpoint**; frontend to a
      free static host. Store the document corpus in **Nebius Object Storage** (or commit the small text
      extractions and gitignore the PDFs) so it survives through judging. Point VITE_API_BASE at the endpoint;
      CORS for the exact origin.
ACCEPTANCE: works from a fresh incognito window AND a phone on cellular; no localhost in the built bundle;
            the corpus is reachable by the deployed backend without re-fetching from publishers.
VERIFY: grep -rn "localhost\|127.0.0.1" frontend/dist || echo clean; curl -s $DEMO/healthz
```

```
ID: C-T36  TITLE: Durability hardening + judge runbook
PHASE: 4  OWNER: devops-agent  DEPENDS_ON: C-T35  BLOCKS: G5
SPEC: This project has an unusual December risk: **publisher URLs change**, so a live-fetch demo can rot.
      Therefore the deployed demo must run primarily from the **snapshotted corpus** (with hashes and retrieval
      timestamps visible), using Tavily only for the currency check, and degrading honestly when Tavily or a
      publisher is unavailable. Reserve ≥$10 credits. Pin all versions. docs/JUDGE-RUNBOOK.md with exact steps
      and expected results, including `make sample` with no API key. Hourly uptime ping. Video public. Repo public.
ACCEPTANCE: the demo returns a full, correctly-cited answer with all external publishers blocked (simulate it);
            a non-teammate follows the runbook successfully; ≥$10 credits confirmed.
```

```
ID: C-T37  TITLE: LIMITATIONS.md with real failure cases
PHASE: 4  OWNER: content-agent DEPENDS_ON: C-T23, C-T33, C-T26, C-T27  BLOCKS: G5
CONTEXT: docs/templates/LIMITATIONS.template.md
SPEC: Real numbers and ≥4 concrete failure cases with screenshots. Must cover: coverage (which DSOs and areas are
      in the corpus and which are not, by name); that a codeerprognose is non-binding and moves, with the
      revision evidence; that the tool reports the *published official position*, not a prediction, and is not a
      substitute for a formal application or a grid operator's determination; abstention rate and what it means;
      load-profile assumptions and their sensitivity; that options are informational and prerequisites vary by
      operator; the date-support rate; the eval's INSUFFICIENT classes; the accessibility gaps and plan; and the
      disclaimer that this is not legal, financial or engineering advice.
ACCEPTANCE: every claim backed by a number, citation or screenshot; a sceptical read finds no unbacked sentence;
            the coverage table names the operators you do NOT cover.
```

```
ID: C-T38  TITLE: README.md complete
PHASE: 4  OWNER: content-agent DEPENDS_ON: C-T25, C-T29, C-T23  BLOCKS: G5
CONTEXT: docs/templates/README.template.md
SPEC: First line = the A/B invented-date number. Then: the one-sentence problem; a screenshot of the two
      DirectionCards showing different verdicts for the same address; **the three insider insights**; the
      generalisable-pipeline framing; how NVIDIA Nemotron models are used (tiering table with real costs, Nano
      hand-off volumes, cache-hit rate); **where Token Factory accelerated the workflow** (Sandbox network-off
      validation, branching A/B, cached tokens, Serverless Job sweep, structured output); other Nebius services
      (Serverless Endpoint, Object Storage); the sweep headline with its methodology; the revision history
      finding; a 5-minute quickstart incl. `make sample` with no API key; architecture diagram; /corpus link;
      LIMITATIONS.md and JUDGE-RUNBOOK.md links; data attribution and licences; the disclaimer; licence.
ACCEPTANCE: clean clone + quickstart works; `make sample` runs offline; all required highlight areas present with
            real numbers; the disclaimer appears in the first screen.
VERIFY: git clone <url> /tmp/r && cd /tmp/r && make sample && make check
```

```
ID: C-T39  TITLE: docs/ — DECISIONS, DISCREPANCIES, DESIGN, DATA-SOURCES, EVAL, SWEEP-METHODOLOGY, DOMAIN-LEXICON
PHASE: 4  OWNER: content-agent DEPENDS_ON: C-T29  BLOCKS: G5
SPEC: DECISIONS.md ≥15 entries. DISCREPANCIES.md ≥3 (publisher URL changes and vocabulary mismatches are rich
      material here — and raw material for the Devpost feedback prize). DATA-SOURCES.md complete with hashes.
      Promote data/domain-lexicon.md content into a published glossary page.
ACCEPTANCE: all seven docs present and internally consistent; every document in DATA-SOURCES.md has a hash.
```

### Phase 5 — Package (Wed 16:00 → Thu 30 Oct 18:00)

```
ID: C-T40  TITLE: Video script + shot list (≤2:50)
PHASE: 5  OWNER: content-agent + human  DEPENDS_ON: G4  BLOCKS: C-T41
CONTEXT: docs/templates/video-script.template.md ; docs/HOOK.md
SPEC:
  0:00–0:18  the problem, in Ruud's words, with the real cost-of-delay euro figure from C-T27 on screen and its
             source named as "interview, <role>, <date>". Plus one public congestion statistic with its source.
  0:18–0:40  THE DIRECTION INSIGHT, shown not told: one postcode. Left card: "FEED-IN — no firm capacity."
             Right card: "CONSUMPTION — 25 kW may be available." Same address, same moment. Caption:
             "Capacity has a direction. Most tools don't ask which one."
  0:40–1:05  THE BINDING INSIGHT: expand the date claim → BindingChip says NON-BINDING → open the revision
             history → "this forecast moved from Q1 2028 to Q3 2028." Caption: "A codeerprognose is not a
             promise, and it moves."
  1:05–1:30  THE ACTION INSIGHT: the ranked options with computed kW, the load-profile worksheet, and the Dutch
             phone script being copied. Download the application pack.
  1:30–1:55  THE REFUSAL, on camera: a postcode with no official position → NO_OFFICIAL_POSITION_FOUND →
             the phone script. Caption: "It will not invent a date. That is the product."
  1:55–2:20  how it works: architecture; name the model tiers and the Nano→Ultra hand-off; Tavily as a runtime
             dependency with results-used/results-rejected shown; the Sandbox validating the pack with the
             **network disabled**; sha256 match.
  2:20–2:40  the proof: the A/B invented-date chart; date-support rate = 1.000; the sweep map with n; kappa;
             the ledger incl. the all-Ultra counterfactual and the cache-hit rate.
  2:40–2:50  LIMITATIONS out loud: coverage, non-binding forecasts, not a substitute for a formal application.
             Next steps incl. the accessibility plan and other regions. Close on the framing: "a generalisable
             pipeline, demonstrated where the data is worst."
  RULES: no copyrighted music; no third-party logos used to imply endorsement (grid operators' names appear as
         text citations, which is fine — do not reproduce their logos as branding); public YouTube; captions on.
ACCEPTANCE: reads aloud ≤2:50; every shot numbered with an owner; the three insight shots are each ≤25 s.
```

```
ID: C-T41  TITLE: Shoot and edit the video
PHASE: 5  OWNER: human  DEPENDS_ON: C-T40  BLOCKS: G5
SPEC: One pass per shot. Upload PUBLIC. Verify ≤2:59 and that the link works logged-out.
ACCEPTANCE: public URL; ≤3:00; the DirectionCard shot is unbroken; captions present.
KILL CRITERION: not shot by Wed 20:00 → cut to 90 s: problem → direction split → refusal → architecture → framing.
```

```
ID: C-T42  TITLE: Devpost submission copy
PHASE: 5  OWNER: content-agent DEPENDS_ON: C-T38  BLOCKS: G5
SPEC: Title; tagline ≤80 chars; Inspiration (Ruud + the euro figure, sourced as an interview); What it does;
      How we built it (tiers, Nano→Ultra hand-off, Tavily runtime dependency, corpus hashing + revision
      tracking, Sandbox network-off, branching A/B, Serverless Job sweep, Serverless Endpoint, cached tokens —
      real numbers); Challenges (≥3, specific: publisher URL rot, non-binding language extraction, direction
      conflation, long-document context limits); Accomplishments (the invented-date delta, date-support 1.000,
      sweep n, revision history recovered); What we learned (the three insights + one platform learning);
      What's next (other regions, automatic application drafting, a snapshot API for operators); the required
      Nebius/Nemotron highlight; built-with tags. Every number must match the README.
ACCEPTANCE: all sections present; no number disagrees with the README; the disclaimer appears.
```

```
ID: C-T43  TITLE: Devpost feedback section (10 × $100 + swag)
PHASE: 5  OWNER: human  DEPENDS_ON: docs/DISCREPANCIES.md  BLOCKS: G5
CONTEXT: docs/templates/devpost-feedback.template.md
SPEC: ≥400 words, ≥6 specific points, ≥4 with numbers or quoted doc URLs, ≥1 concrete feature request. Material
      unique to this project: long-document context handling and the 16k-token output limit's effect on
      multi-document extraction; whether Token Factory could expose per-document chunk-level caching; Tavily's
      behaviour on non-English (Dutch) government queries — a genuinely useful observation for a Tavily-owned
      prize; Sandbox image size limits with WeasyPrint; whether Object Storage + Serverless Endpoint made a
      durable demo easy; rate limits under a 200-area sweep.
ACCEPTANCE: specific, technical, constructive; ≥4 numbers; includes the Dutch-language Tavily observation.
```

```
ID: C-T44  TITLE: Final verification sweep + SUBMIT
PHASE: 5  OWNER: human + eval-agent  DEPENDS_ON: all  BLOCKS: —
SPEC: (1) clean clone → `make sample` offline → works, then README quickstart with a key → works;
      (2) fresh incognito → demo → answer in ≤60 s; (3) phone on cellular; (4) demo works with all external
      publishers blocked (corpus-snapshot mode); (5) video public ≤3:00; (6) LICENSE at repo root;
      (7) every number identical across README / Devpost / video; (8) ≥$10 credits left; (9) uptime ping running;
      (10) /corpus lists every document with hashes; (11) LIMITATIONS present with real numbers;
      (12) feedback written; (13) disclaimer visible in UI, pack, README and video.
      Then submit. Screenshot the confirmation. Email every teammate.
ACCEPTANCE: all 13 checked in reports/C-T44.FINAL.md with evidence; submitted by Thu 29 Oct 18:00 CEST.
```

---

## 10. Test & verification plan

| Layer | What |
|---|---|
| Corpus | fetch + hash stability; re-fetch produces no revision event; a change produces one; `verbatim_supports` True for a real quote, False for a paraphrase |
| Geo | 50 postcodes resolve correctly; ≥10 hand-verified against operator pages; unmapped → abstain; no LLM in the module |
| Contract | date without document_id fails validation; binding=null fails validation; model_estimate without the flag fails |
| Chunking | a 60-page PDF chunks with overlap; over-long input → status=truncated and its claims are unusable |
| Golden | 10 fixtures → expected per-direction verdicts, offline-replayed |
| Adversarial | paraphrased quote → rejected; stale document → downgraded; unsupported date → dropped; option without a route → dropped |
| Abstention | 7 paths, each with a distinct reason and a concrete next action |
| Determinism | same input + same corpus snapshot → identical determinism_hash across 3 runs |
| Integration | 6 concurrent runs; warm-cache <3 s |
| Eval | 60 queries, double-labelled, kappa, **date-support rate must be 1.000 with the gate on** |
| Experiment | Sandbox branch A/B, n=60 per arm, four invented-content counters |
| Sweep | ≥200 areas, n_completed/n_failed separate, methodology box |
| Load | 6 parallel users on the deployed demo |
| Durability | demo works with external publishers blocked; `make sample` with no API key |

---

## 11. Design system summary (full brief in C-T07)

**Metaphor:** a grid operator's written determination letter, modernised. Utility blue-grey on paper, hairline
rules, left-aligned, bureaucratic but calm. **Every date, kW figure, postcode, hash and timestamp in monospace**
— the numbers are the product and must look like data, not prose.

The **DirectionCard pair is the hero**: two cards, same address, different answers. That single layout choice
makes insight #1 visible without a word of narration. **BindingChip** must render BINDING / NON-BINDING /
UNKNOWN so differently that a colour-blind user in greyscale can still tell them apart — because confusing them
is the exact harm this product exists to prevent.

---

## 12. Risk register & pivots

| # | Risk | Likelihood | Detection | Mitigation | Pivot |
|---|---|---|---|---|---|
| R1 | **Official documents not retrievable / not machine-readable** | **Med–High** | **C-T03, Sun 20:00** | Try Tavily discovery + direct fetch + PDF/XLSX extraction; start with your own region's operator; fall back to national overview pages | **Fatal → switch to Idea A or B** |
| R2 | Publisher URLs rot before judging | **High** | C-T36 | Corpus-snapshot-first architecture; hashes + timestamps visible; Tavily only for currency | Snapshot mode is the demo; live mode is a bonus |
| R3 | Too Dutch for a global panel | Med | Video review | The three insights are universal (direction, non-binding forecasts, ranked options); state the generalisable-pipeline framing; add one non-Dutch region if time allows | Reframe around any regulated-utility queue |
| R4 | Long documents exceed context | Med | C-T06 | Nano pre-summarisation with page/row preservation; truncation never silent | Chunk + map-reduce; report the hand-off volumes |
| R5 | Cannot find real interviewees | Low–Med | C-T27, Tue 12:00 | Brabant installers and SMEs are everywhere; a LinkedIn message and a phone call; a local installer association | Use a documented public case (a named company's public complaint to ACM) as the persona evidence |
| R6 | Sweep blocked or too slow | Med | C-T24, Tue 18:00 | Aggressive caching by postcode4; ≤200 areas; polite rate limits | Shrink to n=80 and publish honestly |
| R7 | A/B shows zero invented dates | Low | C-T23 | Report the abstention-rate delta instead, honestly | Not a failure — a different finding |
| R8 | Credits exhausted | Low | Ledger budget guard | Nano-first, heavy caching, offline tests | Shrink the sweep |
| R9 | Legal/advice exposure | Med | C-T37 | Disclaimer everywhere; report the published position, never a prediction; abstain rather than guess | Narrow to information-only, drop option ranking |
| R10 | Scope creep (other regions, chatbot, auto-application) | **High** | Every gate | Component table §3; feature freeze at Phase 4 | Cut to the hook |

---

## 13. Team allocation

| Person | Lanes | P0 | P1 | P2 | P3 | P4 | P5 |
|---|---|---|---|---|---|---|---|
| **P1 — backend/gate** | backend, gate | C-T01, C-T06 | C-T09, C-T11, C-T12 | C-T17, C-T18, C-T19 | C-T29, C-T30 | C-T36 | C-T44 |
| **P2 — data/corpus** | data, corpus, sandbox, jobs | C-T03, C-T04, C-T05 | C-T10 | C-T16 | C-T21, C-T22, C-T23, C-T24, C-T28 | C-T35 | C-T41 (edit) |
| **P3 — frontend/design** | frontend, map | C-T07 | C-T13 | C-T20 | C-T25 | C-T31, C-T32, C-T34 | C-T41 (shoot) |
| **P4 — eval/content/human** | eval, content, Tavily | C-T02, C-T08 | C-T14, C-T15 | — | C-T26, C-T27 | C-T33, C-T37, C-T38, C-T39 | C-T40, C-T42, C-T43 |

**Critical path:** C-T03 → C-T10 → C-T16 → C-T17 → C-T18 → C-T19 → C-T20 → **G2** → C-T21 → C-T22/C-T23 →
C-T24 → C-T38 → C-T40 → C-T41 → submit.
**C-T03 (finding the documents) is the real bottleneck — start it before anything else, today.**

---

## 14. Definition of Done — project level

- [ ] All tickets DONE or explicitly parked with a reason in `docs/DECISIONS.md`
- [ ] `make check` green from a clean clone; **`make sample` works with no API key**
- [ ] ≥40 official documents ingested, hashed, indexed, publicly listed at `/corpus`
- [ ] ≥3 RevisionEvents extracted, ≥1 showing a date that moved with quotes for both
- [ ] Postcode→DSO table covering ≥1 province (target all NL), spot-checked
- [ ] 60-query double-labelled eval; kappa published; **date-support rate = 1.000 with the gate on**
- [ ] A/B invented-date experiment published with n=60 per arm and four counters
- [ ] ≥200-area sweep published with a full methodology box, n_completed and n_failed separate
- [ ] Sandbox application pack validated **with networking disabled** and hash-verified
- [ ] All abstention paths proven; NO_OFFICIAL_POSITION_FOUND shown on camera with a Dutch phone script
- [ ] DirectionCards show different verdicts for the same address (insight #1 visible without narration)
- [ ] BindingChip's three states distinguishable in greyscale and under deuteranopia simulation
- [ ] Glossary covers every domain term that appears in the UI
- [ ] Ledger covers ≥95% of calls; all-Ultra counterfactual and cache-hit rate published
- [ ] ≥3 real interviews; ≥1 quote with permission; **≥1 real cost-of-delay euro figure**; ≥1 product change
- [ ] `LIMITATIONS.md` names the operators you do NOT cover
- [ ] Demo works from the corpus snapshot with all external publishers blocked
- [ ] Accessibility audited and called out in the video
- [ ] Disclaimer visible in UI, pack, README and video
- [ ] `LICENSE` at repo root; repo public; video public ≤3:00
- [ ] `docs/JUDGE-RUNBOOK.md` followed by a non-teammate; ≥$10 credits reserved; uptime ping running
- [ ] Devpost feedback written with ≥4 numbers, incl. the Dutch-language Tavily observation
- [ ] **Submitted by Thu 29 Oct 18:00 CEST**
