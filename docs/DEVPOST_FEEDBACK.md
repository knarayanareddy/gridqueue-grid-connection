# Feedback — GridQueue (Best Apps and Agents · Best Use of Tavily)

> Draft for the Devpost "Most Valuable Feedback" field, structured per `docs/templates/devpost-feedback.template.md`.
> Every point below comes from something this project actually did or read. Where a point needs the live run
> (`docs/DEVPOST_SUBMISSION.md` §0, B1), it says `TODO(B1)` instead of guessing. Check `/rules` for where feedback
> is submitted (often a separate form).

**Built with:** NVIDIA Nemotron via Nebius Token Factory (OpenAI-compatible API, structured output with
`json_schema`; pinned ids `nvidia/Nemotron-3-Ultra-550b-a55b`, `nvidia/nemotron-3-super-120b-a12b`,
`nvidia/nemotron-3-nano`, **TODO_VERIFY(C-T02)** against the authenticated catalog) · Token Factory Sandboxes
(designed for; not yet run) · Serverless AI Jobs (designed for; not yet run) · Tavily Search + Extract
**Where:** Netherlands · **When:** 26 Aug – 30 Oct 2026 · **Spend:** $0 so far (every run to date is offline,
fixture mode; `TODO(B1)`: update after the live run)
**Repo:** https://github.com/knarayanareddy/gridqueue-grid-connection · **Contact:** `TODO`

GridQueue answers "can I connect here, in which direction, and when?" for Dutch grid connections. Tavily finds the
grid operator's current documents, Nemotron proposes position claims as structured output, and a deterministic
Python gate keeps only values that are literally stated in the source. The workload is many short,
schema-constrained extractions over Dutch-language PDFs and web pages, plus a 50-area batch sweep.

---

## 1. What worked, specifically, and why it mattered

- **Structured output with `json_schema` on Token Factory**
  ([doc](https://docs.tokenfactory.nebius.com/ai-models-inference/json)). We could point the model's response
  format at the same JSON Schema 2020-12 file (`schemas/core-schemas.json`) that types our API, our tests and our
  gate. There is one contract for everything, and the gate never has to parse free text. That made a "no model in
  the gate" rule practical: the gate only ever sees typed claims with a quote field.
- **OpenAI-compatible base URL** (`https://api.tokenfactory.nebius.com/v1/`). The extractor is the stock
  `openai` client with a different `base_url`, so mocking it for 236 offline tests needed no Nebius-specific
  code.
- **Sandbox networking can be turned off at spawn** (`networking.enabled: false`). The docs suggest checking
  that only `lo` is left in `/sys/class/net`, and we turned that into a hard guard: our application pack refuses
  to run if any other interface exists. A documented, testable check beats a promise. (Doc page URL:
  `TODO(url)`; we recorded the API base `https://api.tokenfactory.nebius.com/sandboxes/` but not the page.)

## 2. Documentation gaps I hit

- **https://docs.nebius.com/serverless/quickstart/jobs.** I was preparing a CPU-only batch job (50 postcode areas
  × 2 directions, writes one JSON summary). The quickstart is complete for its GPU example: CLI, Go, Python,
  JavaScript and REST, including `nebius ai job logs $JOB_ID`. For a non-GPU batch job, it leaves out four things:
  1. **CPU-only platform/preset names.** The only example is `--platform gpu-l40s-a --preset 1gpu-8vcpu-32gb`.
     It links to "Compute platforms and presets" but gives no CPU example.
  2. **How to pass secrets or environment variables** (our job needs `NEBIUS_API_KEY` and `TAVILY_API_KEY`).
  3. **Where a job should write its output.** The page says *"When the job is complete, Serverless AI
     automatically releases all allocated computing resources and the container disk of the job"* and *"Checking
     job logs is available only in the web console and CLI"*. So a file written inside the container is gone, and
     logs cannot be fetched from the SDK or REST.
  4. **Whether the job id is visible inside the container**, so the output can record which job produced it.

  Suggested addition: a second quickstart, *"CPU batch job that writes results to Object Storage"*, with a CPU
  preset, one secret passed as an env var, and an upload step.
- **Sandboxes: file upload.** Spawn accepts `files: {"/path": {"uuid": …}}`, and the SDK's `files=` argument
  uploads for you. But we could not find the **REST endpoint that uploads a file and returns that uuid**, so a
  non-Python client cannot follow the same path. We fell back to the SDK. (Page URL: `TODO(url)`.)

## 3. Things that broke, or behaved surprisingly

- **My fault: I postponed the first live call too long.** Fixture mode was so productive that every artefact
  ran end to end offline at $0: the UI, 236 tests, the A/B harness, the 50-area sweep, a static demo site and a
  recorded demo video. As a result, the *runtime* requirements (*"runs on Token Factory at runtime"*, and Tavily's
  *"functional runtime call"*) were still unmet three days before the deadline. Nothing on the platform was
  wrong; the lesson is in §7.
- `TODO(B1)`: anything surprising in the first live run: request ids, latency, schema deviations, rate limits.

## 4. Numbers you might want

| Metric | Value |
|---|---|
| Total spend | **$0**, 0 external calls (all runs offline in fixture mode; ledger) · `TODO(B1)` |
| Gate: LLM calls | **0** by design; a test fails if the gate module imports an HTTP or model client |
| Gate on a SYNTHETIC adversarial set (29 hand-written cases) | 21/21 fabricated values blocked; 10/10 genuine kept; **4/5 misattributed values still passed** |
| Offline sweep, 50 areas × 2 directions | Completes in well under 10 s on a laptop; 50/50 completed, 0 failed (SYNTHETIC inputs, pipeline check only) |
| Latency p50/p95, tokens, cached tokens, Tavily calls per answer, % Tavily results used | **Not measured**: needs the live run · `TODO(B1)` |
| Sandbox image build / cold start, Serverless Job wall time and cost | **Not measured**: not run yet |

## 5. What I wished existed

- **Use case:** a nightly re-check of 50+ postcode areas, because operators revise congestion forecasts without
  notice, and the output is one JSON file that the website reads. **Workaround:** none we could document from
  the quickstart, since the container disk is released and logs are console/CLI only. Our job writes to
  `$RUNS_DIR`, and we have not found the supported way to collect it. **Request:** a job-level output spec
  (`spec.outputs: [{path, bucket}]`) or `nebius ai job download $JOB_ID --path …`, mirroring the Sandboxes
  `inspect/{uuid}/download` endpoint (documented; our runbook uses it, not yet run).
- **Use case:** a citation gate needs to know *exactly* which document version a claim came from.
  **Request:** `TODO(B1)` (Tavily): whether `extract` can return a content hash or a `Last-Modified`/ETag, so
  retrieval provenance does not depend on hashing our own copy.

## 6. Non-English / international notes

- `TODO(B1)`: Dutch-language Tavily queries against grid-operator domains (e.g. *"congestie teruglevering
  codeerprognose"* with `include_domains` set to the operator). Record n returned, n usable after the gate, and
  what the failures looked like (PDF text order, tables flattened, map-only portals).
- Already observed offline: Dutch number and date formats are the hard part of *checking* model output.
  "1.250 kW" is 1250 in Dutch and 1.25 in English, and "derde kwartaal van 2028" means Q3 2028. Our gate accepts
  both readings and matches Dutch and English date forms literally.

## 7. One thing I would tell a friend starting tomorrow

Build a fixture mode that runs the *real* pipeline on day one: it pays for itself in tests and demos. But make
**one live call on day two** and keep its ledger line, even if it costs a cent. The hackathon's hardest
requirements are about *runtime* use, and they are cheap to satisfy early and stressful to satisfy late.

---

**Thanks**, `TODO(name)`, `TODO(role)`, Netherlands.
