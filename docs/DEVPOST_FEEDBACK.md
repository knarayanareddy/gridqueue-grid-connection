# Feedback — GridQueue (Best Apps and Agents · Best Use of Tavily)

> Text for the Devpost feedback section ("Most Valuable Feedback", $100 + NVIDIA swag; judged on *completeness,
> viability and potential impact*), structured per `docs/templates/devpost-feedback.template.md`.
> Every point comes from something this project did or a doc page we visited (URLs inline). Where a point needs
> the live run (`docs/DEVPOST_SUBMISSION.md` §0, B1), it says `TODO(B1)` instead of guessing. Before pasting:
> fill the `TODO`s, and check `/rules` for where feedback goes (it may be a separate form).

**Built with:** NVIDIA Nemotron via Nebius Token Factory (OpenAI-compatible API, structured output with
`json_schema`). Pinned ids are `nvidia/Nemotron-3-Ultra-550b-a55b`, `nvidia/nemotron-3-super-120b-a12b` and
`nvidia/nemotron-3-nano`, **TODO_VERIFY(C-T02)** against the authenticated catalog. Also: Token Factory Sandboxes
(designed for; not yet run), Serverless AI Jobs (designed for; not yet run), Tavily Search + Extract.
**Where:** Netherlands · **When:** 26 Aug – 30 Oct 2026 · **Spend:** $0 so far. Every run to date is offline in
fixture mode; `TODO(B1)`: update after the live run.
**Repo:** https://github.com/knarayanareddy/gridqueue-grid-connection · **Live demo:**
https://knarayanareddy.github.io/gridqueue-grid-connection/ · **Contact:** `TODO(email or Discord handle)`

GridQueue answers "can I connect here, in which direction, and when?" for Dutch grid connections. Tavily finds the
grid operator's current documents, Nemotron proposes position claims as structured output, and a deterministic
Python gate keeps only values that are literally stated in the source. The workload is many short,
schema-constrained extractions over Dutch-language PDFs and web pages, plus a 50-area batch sweep.

**TL;DR: the three changes that would have saved us the most time**
1. A **CPU batch-job quickstart for Serverless AI Jobs** with a CPU preset, a secret passed as an env var, and
   the output written somewhere that outlives the job (§2, §5).
2. **Link the Sandboxes REST upload endpoint from the files guide**, and fix its title and its `Project` header
   placeholder (§3).
3. **A job-level output spec** (`spec.outputs`) or `nebius ai job download` for Serverless jobs (§5).

---

## 1. What worked, specifically, and why it mattered

- **Structured output with `json_schema` on Token Factory**
  ([doc](https://docs.tokenfactory.nebius.com/ai-models-inference/json)). We point the model's response format at
  the same JSON Schema 2020-12 file (`schemas/core-schemas.json`) that types our API, our tests and our gate.
  There is one contract for everything, and the gate never parses free text. That made a "no model in the gate"
  rule practical: the gate only ever sees typed claims, each with a quote field.
- **OpenAI-compatible base URL** (`https://api.tokenfactory.nebius.com/v1/`). The extractor is the stock `openai`
  client with a different `base_url`, so mocking it for 236 offline tests needed no Nebius-specific code.
- **A network-off check you can actually test.** The cookbook
  [*Prepare inputs, then verify with networking disabled*](https://docs.tokenfactory.nebius.com/sandboxes/cookbook/verify-with-networking-disabled)
  spawns with `"networking": {"enabled": false}` and asserts the boundary from inside the guest:
  ```sh
  for interface in /sys/class/net/*; do
      test "${interface##*/}" = lo
  done
  ```
  We copied that idea into a hard guard. Our application pack (`backend/app/sandbox/pack.py
  --require-network-off`) refuses to run if any interface other than `lo` exists. A documented check that needs
  no external host beats a promise. The page also says plainly that the saved image *"does not carry the earlier
  network setting"*, which saved us a wrong assumption.

## 2. Documentation gaps I hit

- **https://docs.nebius.com/serverless/quickstart/jobs.** I was preparing a CPU-only batch job (50 postcode areas
  × 2 directions, writing one JSON summary; 0.072 s of wall time offline, so the job is dominated by API calls).
  The quickstart is complete for its GPU example: CLI, Go, Python, JavaScript and REST, including
  `nebius ai job logs $JOB_ID`. For a non-GPU batch job it leaves out four things:
  1. **CPU-only platform/preset names.** The only example is `--platform gpu-l40s-a --preset 1gpu-8vcpu-32gb`.
     It links to "Compute platforms and presets" but gives no CPU example.
  2. **How to pass secrets or environment variables.** Our job needs `NEBIUS_API_KEY` and `TAVILY_API_KEY`.
  3. **Where a job should write its output.** The page says *"When the job is complete, Serverless AI
     automatically releases all allocated computing resources and the container disk of the job"*, and
     *"Checking job logs is available only in the web console and CLI"*. So a file written inside the container
     is gone, and logs cannot be fetched from the SDK or REST. Our workaround is to print the whole JSON result to
     stdout (`--stdout`) so it at least survives in the CLI logs.
  4. **Whether the job id is visible inside the container**, so the output can record which job produced it.

  Suggested addition: a second quickstart, *"CPU batch job that writes results to Object Storage"*, with a CPU
  preset, one secret passed as an env var, and an upload step.

## 3. Things that broke, or behaved surprisingly

- **My fault: I wrote down that the Sandboxes REST upload endpoint did not exist.**
  - **What happened:** our runbook said `TODO_VERIFY(sandbox-file-upload): the upload endpoint that returns
    that uuid was not found in the docs`. It exists:
    [`POST https://api.tokenfactory.nebius.com/sandboxes/v1/files`](https://docs.tokenfactory.nebius.com/api-reference/sandboxes/files/upload-a-file-to-the-server-the-body-must-be-a-file-content).
    It takes a raw `application/octet-stream` body plus the `Project` header and returns
    `{"uuid", "sha256", "size"}`; the uuid is what spawn's `files: {"/path": {"uuid": …}}` expects. I searched the
    guides and never opened the API reference's *Files* group.
  - **What made it easy to miss:**
    1. The guide
       [*Work with files and artifacts*](https://docs.tokenfactory.nebius.com/sandboxes/guides/work-with-files-and-artifacts)
       documents uploading only through the SDK (`files={"/guest/path": local_or_bytes}`, *"The SDK uploads local
       inputs before spawn"*). It links the REST **download** reference but not the REST **upload** one.
    2. The reference page's title is an unedited docstring: *"Upload a file to the server. the body must be a
       file content."* Searching for "upload file" mostly returns the *other* files API, the OpenAI-compatible
       [`POST https://api.tokenfactory.nebius.com/v1/files`](https://docs.tokenfactory.nebius.com/api-reference/examples/files).
       That one takes a multipart form with `purpose="batch"` and returns `{"id": "file-123", …}`: a different
       base path, body format and id type. It is easy to conclude "uploads are for batch inference only".
    3. The cURL sample on the Sandboxes upload page sends `--header 'Project: <api-key>'`, while the field
       description on the same page says *"Nebius project ID associated with the IAM token"*. The placeholder
       invites people to paste their API key into the `Project` header.
  - **Suggested fixes:**
    - one sentence in the files guide, "REST: `POST /sandboxes/v1/files` with the raw bytes, then pass the
      returned `uuid` in spawn's `files`", with a link;
    - a human title for the reference page;
    - `Project: <project-id>` in the sample.
- `TODO(B1)`: anything surprising in the first live run: request ids, latency, schema deviations, rate limits.

## 4. Numbers you might want

| Metric | Value |
|---|---|
| Total spend | **$0**, 0 external calls (all runs offline in fixture mode; ledger, `runs/sweep_summary.json` `cost`) · `TODO(B1)` |
| Gate: LLM calls | **0** by design; a test fails if the gate module imports an HTTP or model client |
| Gate on a SYNTHETIC adversarial set (29 hand-written cases) | Gate OFF accepted 10/10 fabricated dates; Gate ON blocked 21/21 fabricated values and kept 10/10 genuine ones; **4/5 misattributed values still passed** |
| Offline sweep, 50 areas × 2 directions | 0.072 s wall time, 50/50 completed, 0 failed (SYNTHETIC inputs, pipeline check only) |
| Latency p50/p95, tokens, cached tokens, Tavily calls per answer, % of Tavily results used | **Not measured**: needs the live run · `TODO(B1)` |
| Sandbox image build / cold start, Serverless Job wall time and cost | **Not measured**: not run yet |

## 5. What I wished existed

- **Serverless job output.**
  - *Use case:* a nightly re-check of 50+ postcode areas, because operators revise congestion forecasts without
    notice. The output is one JSON file that the website reads.
  - *Workaround:* print the JSON to stdout and scrape it from `nebius ai job logs`. That works only through the
    CLI or console, and only while the logs are retained.
  - *Request:* a job-level output spec (`spec.outputs: [{path, bucket}]`) or
    `nebius ai job download $JOB_ID --path …`, mirroring the Sandboxes
    [download-a-file-from-image](https://docs.tokenfactory.nebius.com/api-reference/sandboxes/inspect/download-a-file-from-image)
    endpoint.
- **Document provenance from Tavily.**
  - *Use case:* a citation gate needs to know *exactly* which document version a claim came from.
  - *Request:* `TODO(B1)`: check after the live run whether Tavily `extract` can return a content hash or a
    `Last-Modified`/ETag, so provenance does not depend on hashing our own copy.

## 6. Non-English / international notes

- `TODO(B1)`: Dutch-language Tavily queries against grid-operator domains (e.g. *"congestie teruglevering
  codeerprognose"* with `include_domains` set to the operator). Record how many results came back, how many
  survived the gate, and what the failures looked like (PDF text order, flattened tables, map-only portals).
- Already observed offline: Dutch number and date formats are the hard part of *checking* model output.
  "1.250 kW" is 1250 in Dutch and 1.25 in English, and "derde kwartaal van 2028" means Q3 2028. Our gate accepts
  both readings and matches Dutch and English date forms literally. A model that "helpfully" normalises a quote
  breaks literal matching, so the extraction prompt asks for the quote verbatim and the gate rejects anything
  that is not a substring of the source.

## 7. One thing I would tell a friend starting tomorrow

Build a fixture mode that runs the *real* pipeline on day one: it pays for itself in tests and demos. But make
**one live call on day two** and keep its ledger line, even if it costs a cent. The hackathon's hardest
requirements are about *runtime* use, and they are cheap to satisfy early and stressful to satisfy late. And read
the API reference's endpoint list before you write "not documented" anywhere.

---

**Thanks**, `TODO(name)`, `TODO(role)`, Netherlands.
