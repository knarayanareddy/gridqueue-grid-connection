# SYNTHETIC fixtures — not official publications

Everything in this directory was **written by the GridQueue project** so that the `/v1/answer` pipeline can
run offline, with no API keys and no network (ticket C-T14-T19; SPEC C-T01 "make sample").

- `documents/*.txt` are **invented** documents. Areas, figures, dates and routes are made up. They mention
  real operator names only so that the postcode → operator routing can be exercised. **They are not
  publications of Enexis, Liander or Stedin**, and every file says so in its first line.
- `extractions/*.json` are **hand-written stand-ins for model output** (what Nemotron Ultra *might* return).
  The Liander feed-in file is deliberately adversarial: it invents a date, fabricates quotes and a route,
  so the deterministic gate can be seen rejecting them.
- `index.json` maps each operator to its scenario. It must declare `"_synthetic": true`, or the loader refuses
  it.

Whenever these fixtures are used, the API response has `retrieval.mode = "fixture"` and
`retrieval.synthetic = true`, the disclaimer carries a DEMO MODE notice, and the UI shows a banner.

| Operator (postcode range) | Scenario |
|---|---|
| Enexis (5600–5658) | Feed-in congested, waitlist, indicative date Q3 2028 stated as non-binding; consumption open with 250 kW stated |
| Liander (1000–1099) | Feed-in congested, **no date published**. The recorded model output invents one and the gate drops it. Consumption: conditional only |
| Stedin (3000–3089) | No document retrievable → `NO_OFFICIAL_POSITION_FOUND` + phone script |
