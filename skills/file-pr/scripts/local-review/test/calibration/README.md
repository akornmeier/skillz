# Frozen calibration protocol

**Prepared, not run.** Twelve synthetic patches: eight seeded actionable defects, four clean controls. No measured detection, false-positive, latency or cost results. Live adapter, approval and release qualification remain blocked.

`cases.json` contains before/after source maps. `gold.json` contains grading labels and expected triggers/impacts; never put labels, revealing IDs or this protocol in reviewer context. Byte hashes frozen before model calls and checked by `test/calibration.test.ts`:

- cases: `da451dcf22472bb2c543fa43f49bc23ebc8d9be80237071181ee629f9f21931b`
- gold: `aa330352b3f8fc098d1512e1311d318cde482767ed573af307cb7261c7bc55da`

## Offline preparation

Run package `validate` and repository case-definition validator first. Static fixture tests check frozen bytes, 8/4 labels, required caller/schema and error-path cases, actual changed paths and bounded nonsecret source. They do not claim execution of the seeded behavior or model grading.

For each case, materialize **only** its before source map into a disposable Git repository outside discovery roots, commit with neutral prose, create base ref, apply after source map and commit. No remote, product scripts or fixture labels in that tree. Use opaque per-case repo/attempt names and generic goal: `Review committed change for introduced defects`. The reviewer receives only pinned source, not JSON corpus files, gold IDs, labels, later fixes, other lens outputs or builder reasoning.

## Paid procedure, separately approved

1. Record explicit user authority outside checkouts: frozen corpus hashes, exact requested/returned Haiku model and provider/upstream/privacy, source export, exact scoped key access, certified token/output/rates, aggregate cost/time, top-level/nested request counts and expiry. Approval is not implemented by a flag. Missing controls mean no dispatch.
2. Ship and verify a separately reviewed live adapter first. Current CLI cannot perform calibration. Preserve fail-closed safety checks; do not use simulation as a substitute for paid qualification.
3. Run the twelve blinded patches with identical exact route/settings. Save both lenses' raw candidates, source/quote validation, omissions, terminal/incomplete outcomes and parent dispositions. Compare correctness alone against both lenses by reusing its artifacts, not rebilling a second correctness run. Preserve failed/incomplete samples.
4. Parent grades introduced defects against frozen triggers/impacts, not wording overlap. Record triage evidence and time. Publish per-case detected/missed/unsupported dispositions plus raw candidate count; do not hide parent workload or discard failed samples from coverage.
5. Promotion requires at least **6/8** seeded defects, including **caller-schema-mismatch** and **error-path-regression**, at most **1** triaged actionable false positive across **4** clean controls, and **zero gate safety violations**. Keep raw and triaged counts separate. Failure means revise/retest affected frozen cases within approved budget, never lower thresholds.
6. Record cold/warm startup, total/model-only latency, request count, input/output/cache tokens, known/unknown cost and parent triage time. Proposed targets: p50 <=45 seconds; every round <=120 seconds; review-only scheduled spend <=$0.10/attempt at approved rates. Missing metrics are unavailable, not zero. Scheduling cap is not an invoice guarantee; include parent work in end-to-end comparisons.
7. Run changed skill cases in fresh isolated sessions with stub publishing and explicitly approved nested Haiku allowance. Full release requires every case under all three required profiles, primary trace/assertion grading and the controls in repository `evals/README.md`. No real GitHub publishing or uncontrolled recursive review.
8. Obtain explicit acceptance of results and live defaults. Track first ten separately authorized real filings against verified subsequent GitHub findings and actual invoices, without changing subscriptions or enabling duplicate vendor runs. Tiny sample is not a quality SLA or proof of savings.

Retain approved primary artifacts privately under ignored `evals/runs/` or approved private storage, never public transcripts/source dumps. Use repository schema-1 run records for behavioral qualification. Current results: **Not run: no live adapter, source/key/privacy/spend authority or rollout sign-off.**
