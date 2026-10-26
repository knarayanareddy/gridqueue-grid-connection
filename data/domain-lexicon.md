# Domain lexicon — Dutch grid connection capacity

**Feeds C-T05 (rule wording), C-T07 (tooltips), C-T31 (the in-UI glossary), C-T40 (video narration).**

This is the single highest-leverage artifact in Idea C for the **Design** score, because the domain is
vocabulary-dense and a non-Dutch judge will hit words they cannot infer. Every term below needs:
(a) a one-sentence plain-English gloss, (b) a one-sentence plain-Dutch gloss, (c) a tooltip of ≤12 words.

> **Rule: every domain term that appears anywhere in the UI must be in this file, and every entry here must be
> reachable from a tooltip or the glossary page.** C-T31's acceptance test scripts that check.

---

## 1. The core vocabulary

| Dutch term | Plain English | Why it matters here | Tooltip (≤12 words) |
|---|---|---|---|
| **netcongestie** | grid congestion | The whole problem. The grid in an area cannot carry everything people want to push through it | Too much demand or supply for the local grid to carry |
| **netbeheerder** | grid operator / distribution system operator (DSO) | The body that answers the question and that you must apply to | The company that owns and operates your local power grid |
| **transportvermogen** | transport capacity | The formal name for the contracted right to move power through the grid, in kW | Your contracted right to move power through the grid |
| **firma** | firm (capacity) | Capacity guaranteed to be available whenever you want it | Guaranteed-available capacity, whenever you need it |
| **niet-firma** | non-firm (capacity) | Capacity that the operator may curtail. **This is the main practical escape route** and almost nobody outside the sector knows it exists | Capacity the operator may switch off at busy times |
| **afname** | consumption / offtake | **Direction 1.** Power flowing from grid to you | Power flowing from the grid to you |
| **teruglevering** | feed-in / injection | **Direction 2.** Power flowing from you to the grid | Power flowing from you back into the grid |
| **productiecapaciteit** | production capacity | The feed-in side, in operator language | How much you're allowed to send into the grid |
| **codeerprognose** | coding forecast / indicative capacity forecast | The document that contains "the date". **Explicitly non-binding.** Insight #2 | An indicative forecast of when capacity returns — not a promise |
| **indicatief** | indicative | The word that means "not a commitment". Detect it and never hide it | Indicative means not guaranteed and subject to change |
| **niet-bindend** | non-binding | The formal statement that a date is not a commitment | Officially not a commitment; the date can move |
| **wachtlijst** | waiting list | The queue. Being on it usually means no date | You're queued; usually no guaranteed date |
| **congestieregister** | congestion register | The published record of which areas are congested, in which direction | The official list of congested areas and directions |
| **congestiemanagement** | congestion management | The regulatory framework for handling congestion — the source of the flex routes | The official framework for managing congestion with flexible use |
| **flexcontract** | flex contract | A contract where you accept curtailment in exchange for capacity now | Trade guaranteed availability for capacity available right now |
| **transportovereenkomst op maat** | customised transport agreement | A individually negotiated capacity arrangement rather than a standard one | A capacity agreement negotiated for your specific situation |
| **curtailment / afregeling** | curtailment | The operator switching your feed-in or load down. The cost of non-firm capacity | The operator reducing your feed-in or load at peak times |
| **afschakelbaar vermogen** | switchable / interruptible capacity | Load you agree can be cut. Key input to a flex conversation | Load you agree can be switched off on request |
| **groepstransportovereenkomst** | collective transport agreement | Multiple parties sharing a capacity allocation as a group | Several parties sharing one capacity allocation together |
| **energiehub / hub-and-spoke** | energy hub | A site where multiple parties share grid capacity — a real, growing pattern | A shared-capacity site for multiple connected parties |
| **aansluiting** | connection | The physical grid connection | Your physical connection to the grid |
| **aansluitwaarde / aansluitcapaciteit** | connection value / capacity | The contracted maximum of your connection, in kW or A | The contracted maximum capacity of your connection |
| **hoofdzekering** | main fuse | The physical limiter at your connection; its amp rating × voltage sets your ceiling | Your physical limiter; its rating caps your capacity |
| **grootverbruik** | large-consumption connection | A connection above the small-consumer threshold, with different rules and a different application route | Business-scale connection with different rules and process |
| **kleinverbruik** | small-consumption connection | Household-scale connection | Household-scale connection with simpler rules |
| **netverzwaring** | grid reinforcement | Upgrading cables and substations. The only permanent fix, and it takes years | Upgrading the grid — the permanent fix, taking years |
| **station / onderstation** | substation | The bottleneck asset that usually determines when capacity returns | The substation that usually determines when capacity returns |
| **kabelbezetting** | cable loading | How full the cables are | How full the local cables currently are |
| **rood gebied / congestiegebied** | red area / congestion area | An area officially flagged as congested | An area officially flagged as congested |
| **capaciteitsgrens** | capacity limit | The stated ceiling | The stated maximum capacity for the area |
| **aanvraag** | application | The thing you file | The formal request you submit |
| **vooronderzoek / haalbaarheidsonderzoek** | feasibility study | What an operator or engineer does before committing capacity | A study of whether your request is feasible |
| **indicatiewaarde** | indicative value | An unofficial number. Must be flagged as such in the UI | An unofficial estimate, not a commitment |

## 2. The two words that make insight #1 work

> **`afname` (consumption) and `teruglevering` (feed-in) are separate quantities with separate congestion
> states.** A 60 kWp solar installation needs feed-in capacity. A workshop with two van chargers needs
> consumption capacity. A site with both needs both — and can be refused for one and approved for the other.
>
> The UI must make this impossible to miss: two DirectionCards, side by side, same address, possibly different
> verdicts. Any single "is there capacity here?" answer is wrong by construction.
>
> There is a third, subtler case worth handling if time allows: **time-separated direction.** A battery charges
> (consumption) at night and discharges (feed-in) in the day, so it consumes capacity in both directions but
> never simultaneously. That is exactly what a curtailment/flex arrangement can exploit, and it is the kind of
> detail that makes the tool feel like it was built by someone who has actually had this conversation.

## 3. Words that must be treated with suspicion by the extraction stage

These are the words that turn a confident-looking number into a misleading one. The S3 prompt must look for them
explicitly, and the gate must downgrade any claim whose source contains them without labelling the claim:

| Word | Effect |
|---|---|
| `indicatief`, `naar verwachting`, `prognose`, `raming` | The figure is an estimate, not a commitment |
| `niet-bindend`, `onder voorbehoud`, `kan wijzigen` | Explicit non-binding language — must set `binding="non_binding"` |
| `streefdatum` | A target date, not a promised date |
| `mogelijk`, `in beginsel`, `onder voorwaarden` | Conditional availability |
| `afhankelijk van` | A dependency that changes the answer |
| `peildatum`, `geldig tot` | A validity window — a document past its window must not be presented as current |

> If a document says a date is *indicative* and your UI renders it as a plain date, you have built the exact
> thing this project exists to prevent. **The BindingChip is not decoration; it is the integrity mechanism.**

## 4. Cross-language notes for the non-Dutch stretch region

If a second region is added, the vocabulary does **not** translate one-to-one and must get its own lexicon
section rather than being forced into the Dutch terms:

| Concept | NL | DE | UK/IE | US |
|---|---|---|---|---|
| grid operator | netbeheerder | Netzbetreiber | DNO / DSO | utility / transmission provider |
| congestion | netcongestie | Netzengpass | network constraint / congestion | congestion / interconnection queue backlog |
| connection request | aansluiting aanvragen | Netzanschluss beantragen | connection application / offer | interconnection request |
| queue | wachtlijst | Warteliste / Warteschlange | connection queue | interconnection queue (with a position number) |
| indicative date | codeerprognose (niet-bindend) | indikative Planung | indicative connection date / energisation date | estimated in-service date |
| firm capacity | firma | feste Kapazität | firm capacity | firm capacity / CFIS |
| flexible / curtailable | niet-firma, flexcontract | flexibel / abschaltbare Leistung | flexible connection agreement | flexible interconnection / energy-storage hybrid |

The US model is notably different: an **interconnection queue with numbered positions and study phases**, which
maps onto `queue_status` and `indicative_earliest_date` but adds a `queue_position` field. Handle that by
allowing an optional region-specific extension object rather than polluting the core schema.

---

## 5. The phone script templates (GQ-NOPOSITION-01)

When there is no official position, the answer is not "we don't know" — it is **the exact question to ask, in
their vocabulary.** Have a native Dutch speaker verify these (C-T05).

**Generic, feed-in, large connection:**
> *"Goedendag, ik wil voor postcode <postcode> een zakelijke aansluiting aanvragen met <X> kW
> teruglevercapaciteit (zonnepanelen). Is er voor dit gebied firma transportvermogen beschikbaar richting
> teruglevering, of komt mijn aanvraag op de wachtlijst? En als er congestie is: is een niet-firma aansluiting
> met een curtailmentregeling of een flexcontract mogelijk, en wat is daarvoor de aanvraagroute?"*

**Generic, consumption:**
> *"Goedendag, voor postcode <postcode> wil ik <X> kW extra afnamecapaciteit aanvragen (laadpalen en
> warmtepomp). Is er afnamecapaciteit beschikbaar, of geldt er congestie voor afname in dit gebied? Zo ja, is
> deelname aan congestiemanagement of een afschakelbare regeling een optie?"*

**Installer variant (files these weekly — wants the reference number and the route, not an explanation):**
> *"Voor een zakelijke aanvraag op <postcode>: graag de huidige congestiestatus per richting (afname en
> teruglevering), de actuele codeerprognose met versienummer, en of een niet-firma transportovereenkomst
> mogelijk is met een maximaal afregelbaar vermogen van <Y> kW."*

> Recording these as first-class outputs — with a copy button and a note about which operator they go to — is
> a very small build and it is the thing a real user will actually paste into an email.
