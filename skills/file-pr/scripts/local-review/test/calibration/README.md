# Frozen calibration and rollout

**Tooling is implemented; paid measurements are not implied.** Twelve synthetic patches: eight seeded actionable defects, four clean controls. Deterministic fixtures do not establish model quality or either harness's behavior.

Frozen before model calls:

- `cases.json`: `da451dcf22472bb2c543fa43f49bc23ebc8d9be80237071181ee629f9f21931b`
- `gold.json`: `aa330352b3f8fc098d1512e1311d318cde482767ed573af307cb7261c7bc55da`

Gold IDs, labels, grading prose and this protocol never enter reviewer repositories/context. Parent grader sees them only for scoring. No extra LLM judge.

## Prepare offline

Run package `validate` and repository definition validator. Resolve `RUNNER` from loaded skill directory, then choose a new canonical private root outside Git:

```sh
node "$RUNNER" calibrate prepare --root "$PRIVATE_RUN" --id unique-calibration-id
node "$RUNNER" calibrate draft --root "$PRIVATE_RUN"
```

Preparation creates 12 opaque Git repositories with neutral before/after commits, a base ref and only frozen source maps. Private `prepared.json` records exact repo/head/attempt scope, corpus/gold/runtime/skill hashes. Source inventory and Git object IDs are checked again before collection, not merely trusted from labels. Existing/partial preparations aren't overwritten or auto-recovered. No network or key reads.

Draft output fills those exact scopes and proposes aggregate budget. It stays `DRAFT`, with key/export/privacy permission false. User must choose/approve exact OpenRouter model/upstream/privacy/key-file access and scope. No automatic authority from a config flag or template. Operator records are trusted instructions, not cryptographic proof of consent.

## Approve and collect

A real private approval needs `purpose: calibration`, exact prepared scopes and an explicit user-approved `calibrationBudget`:

```json
{
  "by": "user",
  "preparedHash": "HASH_OF_PREPARED_MANIFEST",
  "expiresAt": 1799999999999,
  "maxCostUsd": 12.24,
  "maxRequests": 72,
  "maxDurationMs": 1440000
}
```

These are proposed maxima, **not approved spending**. Choose actual values before changing outer approval status to `approved`. Aggregate budget expiry cannot exceed outer approval expiry; manifest hash must match. Collection carries absolute expiry through setup and each sample, requiring enough approved time for the whole next 120-second round. Do not reset relative lifetime after async work.

The approved per-attempt scheduling ceiling is $1.02. Conservative holds reserve advertised full context at highest tier, currently $0.5075/request; actual known settlement releases unused amount. This isn't expected call cost or an invoice guarantee. One calibration case consumes one snapshot round, at most six generation calls. Collection reserves full attempt allowance/six requests before each sample, releases only known unused budget, and stops on unknown/incomplete effects. Smaller aggregate budgets may stop earlier even when ordinary expected token charges are low.

```sh
node "$RUNNER" calibrate run --root "$PRIVATE_RUN" \
  --approval "$APPROVAL_JSON" --builder-model "$BUILDER_MODEL"
```

Source export/key access occurs only here under explicit authority. No GitHub publishing, product scripts, fixes, third round, provider fallback or generation retries. `collection.json` records each sample's report digest, request count, wall time and known/unknown cost. Full diff/coverage and actual SDK/provider checks still apply. Both lens artifacts are retained so correctness-alone versus combined scoring reuses responses instead of rebilling.

Collection is one-shot. Crash, failed provider, simulation, missing usage, stale source or exhausted/expired budget leaves blocked evidence and holds, never a passed sample. Inspect/reconcile provider billing and owned state before a separately approved new trial. Never rename folders or reset IDs to evade uncertainty.

## Grade explicitly, from evidence

Create a private 0600 judgments file covering all 12 case IDs from `prepared.json` and every raw finding ID in saved sample reports. Abbreviated shape:

```json
{
  "schema": 1,
  "runId": "unique-calibration-id",
  "assessor": "actual assessor",
  "cases": [{
    "id": "caller-schema-mismatch",
    "triageMs": null,
    "findings": [{
      "id": "ACTUAL_FINDING_ID",
      "disposition": "supported",
      "matchesSeed": true,
      "evidence": "SHA:api.ts:line plus caller/test evidence establishing the frozen trigger and impact"
    }]
  }]
}
```

Repeat for all cases; use empty findings only for zero candidates. `dismissed` also needs concrete evidence. `matchesSeed` needs a supported actionable introduced finding anchored in the seed's file; don't mark unrelated allegations as detections. Parent/source/test judgment supplies defect truth, not exact quote matching or model confidence.

```sh
node "$RUNNER" calibrate grade --root "$PRIVATE_RUN" --judgments "$JUDGMENTS_JSON"
```

`grade.json` retains all cases, raw candidate workload, both-lens and correctness-only detection, false positives, triage time, requests/cost observations and unavailable metrics. Clean-control actionable allegations retained as supported count as false positives; dismissed raw candidates remain visible. Missing/incomplete cases don't enter pass numerators or qualify.

Promotion requires >=6/8 defects, including **caller-schema-mismatch** and **error-path-regression**, <=1 triaged actionable false positive across four clean controls, complete actual live reports and no safety failures. Proposed measured targets: p50 <=45 seconds, every round <=120 seconds, scheduled observed review spend <=$0.10/sample. $0.10 remains a performance target, not the $1.02 admission ceiling. Unknown cold/warm startup or model-only timing stays `null`, never zero. Failure means repair/retest within approval, not lower thresholds. Tiny corpus is not reliability/SLA/savings evidence.

## Qualify both harnesses

Run all current `file-pr` eval cases under all three required profiles, separately for **Pi and Claude Code**, using approved isolated sessions, stub publishing, no real GitHub effects and explicit top-level/nested model budgets. Existing repository `evals/README.md` owns run records and containment/primary-evidence grading. This tool does not execute that paid matrix or certify isolation on your behalf.

For 11 cases, matrix is 66 records. Count is derived from current definitions, not hardcoded. Each schema-1 record needs exact provider/model/thinking/fixture/skill revision, every expected/forbidden assertion passed with primary local evidence, loaded SKILL path and:

```json
{"toolConfiguration":{"harness":"pi","skillBundleHash":"CURRENT_SKILL_HASH","runtimeHash":"CURRENT_RUNTIME_HASH"}}
```

Use `claude-code` for that harness. Both hashes must match current calibration/runtime; instruction-only equality cannot qualify a changed provider/receipt implementation. A private `records.json` manifest lists relative run-record paths under its directory:

```json
{"files":["pi/case/profile.json","claude-code/case/profile.json"]}
```

Actual manifest needs entire matrix. Assertion/evidence references are relative to each record, remain within manifest directory, point to nonempty canonical 0600 owner-owned local files <=32MiB. Missing/stale/duplicate/cross-root records or absent assertions fail. Checker validates critical fields, coverage and artifact identity, not every optional schema-1 field or semantic truth of assessor claims.

```sh
node "$RUNNER" calibrate qualify --root "$PRIVATE_RUN" \
  --judgments "$JUDGMENTS_JSON" --records "$RECORDS_MANIFEST"
```

Qualification regrades primary calibration artifacts and checks current matrix. It emits `qualification.json` with hashes and **approved:false**, awaiting actual user acceptance. Do not call fixture coverage, intercepted HTTP or mechanical file checks a real harness/model pass. Only user can accept results and authorize current-runtime production filing through separate rollout signoff in filing approval. No automatic live default activation.

After acceptance, first ten real filings remain separately authorized; compare verified unique catches, false positives, total time and invoices without changing subscriptions or enabling duplicate vendor runs. No savings claim until measured. Current coding run performs no paid calibration, real harness matrix, credential access, source export or production rollout.
