# GridQueue remediation plan

Future actions only. See [REVIEW.md](REVIEW.md); keep synthetic demo distinct from live advice.

## Dependencies and phase exits

| Phase | Task | Requires | Exit |
|---|---|---|---|
| Baseline | GQ-T1 | Owner provides synthetic environment | Documented reproduction |
| Attribution | GQ-T2 | GQ-T1 | Misattribution tests and domain review |
| Security | GQ-T3 | GQ-T1 | API and model boundary tested |
| Operations | GQ-T4 | GQ-T1 | Locked image and staged recovery |
| Independent acceptance | GQ-T5 | GQ-T2–T4 | Observed artifact and UX |

### GQ-T1 — Establish source and result baseline (GQ-01, GQ-04)

Prerequisite: approved isolated environment. Observed `README.md`, `backend/tests/`, `frontend/`.
1. Trace the actual request through retrieval, extraction, gate and answer, recording exact source and claim identifiers.
2. Reproduce the documented synthetic A/B evaluation with the existing defined project tooling; retain raw results and revision.
3. Inventory the four misattribution cases and identify each point where claim-to-quote binding fails.
4. Ask the owner to reconcile the README's conflicting live-execution claims using dated run and ledger evidence; record the conclusion or leave the status unresolved, then correct the README.

Deliverable: source/result baseline. Verify observed cases independently against source text, not by trusting the gate's own verdict.
- [ ] Synthetic results and limitations recorded.
- [ ] Static demo and live API paths distinguished.

### GQ-T2 — Strengthen binding (GQ-01)

Prerequisite: GQ-T1. Observed `backend/app/gate/gate.py`, `backend/app/stages/` in inventory; inspect before changes.
1. Define a claim contract covering operator, location, direction, date and source span with conservative unknown handling.
2. Implement and test cross-direction, wrong-operator, stale-source and real-quote/wrong-claim cases with independently labeled fixtures.
3. Establish an official-document corpus with recorded provenance, licensing, hashes, retrieval dates and an owner-approved currency/expiry policy; implement and verify stale or missing source handling.
4. Independently validate postcode/operator mappings against authoritative, current references, including boundaries and unsupported areas; record coverage and uncertainty.
5. Obtain domain-owner review of the corpus, source-currency controls, mapping evidence and a representative non-synthetic evaluation; display uncertainty and withhold unsupported answers.

Deliverable: binding implementation and evaluation report. Verify deliberate removal of a binding check makes an adversarial assertion fail; report precision and limitations rather than a fabricated guarantee.
- [ ] Known misattributions rejected or transparently withheld.
- [ ] Domain reviewer approves measured limitations.
- [ ] Domain owner accepts an available, provenance-verified official corpus and documented source-currency policy and controls before real advice.
- [ ] Domain owner accepts independently validated postcode/operator mappings and coverage, including unsupported-area handling, before real advice.

### GQ-T3 — Secure live requests (GQ-02; preventive)

Prerequisite: GQ-T1. Observed `backend/app/main.py`, provider modules in inventory.
1. Trace all public routes, provider keys, external URL access, logs and deployment authentication.
2. Add or enforce approved authentication, authorization, input/egress restrictions and per-user spend and rate budgets at the actual boundary.
3. Test unauthorized requests, hostile retrieved instructions, invalid inputs, timeouts and secret canaries in logs and responses.

Deliverable: threat model and live-path security tests. Verify removal of an authorization or source-boundary control causes a negative test to fail.
- [ ] Provider secrets absent from client and logs.
- [ ] Untrusted text cannot alter authorization or evidence requirements.

### GQ-T4 — Reproduce and recover deployment (GQ-03)

Prerequisite: GQ-T1. Observed `jobs/Dockerfile`, `backend/uv.lock`, Pages workflow.
1. Select an approved locked backend dependency build and pin image provenance.
2. Build and run the image in an isolated environment; verify non-root operation, health, provider outage and synthetic sweep output.
3. Define release, observability, retained data and backup policy; perform a staged restore or document why the selected deployment is stateless.

Deliverable: reproducible image and recovery record. Verify actual artifact revision and restored contents rather than relying on a successful build badge.
- [ ] Image build and failure handling observed.
- [ ] Restore observed or data-free architecture independently established.

### GQ-T5 — Independently accept the experience (GQ-04; preventive)

Prerequisite: GQ-T2–T4. Observed `frontend/src/App.tsx`, Pages workflow and [frontend/package.json:6-10](https://github.com/knarayanareddy/gridqueue-grid-connection/blob/b43f09778317fa4b18ae062232396009b0c2f154/frontend/package.json#L6-L10), which lists `dev`, `build` and `preview`, not a test script.
1. Inspect existing frontend tooling and checks; select suitable UI test tooling and define a `test` script in `frontend/package.json` if absent. Run the existing backend checks and frontend build without lowering thresholds.
2. Implement an automated UI regression assertion that synthetic fixtures are visibly labeled synthetic and cannot be represented as live; exercise reviewed live-mode labeling separately. Run the proposed `npm test` from `frontend/` after defining it, and verify the assertion fails when the label is deliberately made misleading, then restore the correct behavior.
3. Test keyboard, screen-reader, refusal, stale source and unsupported postcode behavior against synthetic and reviewed fixtures.
4. Independently inspect the deployed artifact and execute a rollback to a prior staged version; record exact observed outcomes.

Deliverable: signed-off evidence matrix and automated UI test with a defined command. Record the negative-test failure and the restored passing result; do not assume an existing frontend test suite.
- [ ] Accessibility and uncertainty communicated visibly.
- [ ] Synthetic/live labeling assertion passes for correct labeling and fails on deliberately misleading labeling.
- [ ] Deploy and rollback observed at the expected SHA.

## Acceptance and rollback policy

- [ ] GQ-01 is addressed or accepted with a domain-reviewed limitation.
- [ ] Before real advice, domain owner accepts source provenance and currency controls, the available official corpus, and independently validated postcode/operator mappings and coverage.
- [ ] API access, quotas, secrets and retention approved.
- [ ] Staged artifact, recovery and negative tests independently observed.

Real provider credentials, hosted API, non-synthetic advice and retention changes require owner approval. Retain prior static artifact and compatible API image, pause live processing on incident, and restore data only after an isolated recovery test. Rollback cannot undo advice already relied upon.
