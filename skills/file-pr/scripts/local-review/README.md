# Local PR review runner

Shared Node CLI for **Claude Code and Pi**. Uses pinned Pi SDK internally, not Pi CLI or either harness's subscription/auth. Real OpenRouter dispatch is explicit opt-in through a scoped private approval and dedicated key file. No approval means no live review. Simulated/calibration evidence cannot authorize publishing. Paid calibration, harness qualification and user rollout signoff are separate from deterministic tests.

## Setup

After scoped provisioning approval, from this repository root:

```sh
pnpm --dir skills/file-pr/scripts/local-review install --frozen-lockfile --ignore-scripts --ignore-pnpmfile
pnpm --dir skills/file-pr/scripts/local-review run validate
```

Node >=22.19.0, pnpm 12.9.1, SDK 1.3.0 and exact TypeBox/TypeScript/Vitest pins. Lifecycle scripts disabled. Tests discover only `test/*.test.ts`, use synthetic private repos and intercepted HTTP, and never execute product suites. Pi invocation `/skill:file-pr`; Claude Code `/file-pr`. End-to-end qualification requires both harnesses, not merely shared-library tests.

## CLI and operator approval

In another repository resolve `RUNNER` from the loaded skill's absolute directory, not cwd:

```sh
RUNNER="/absolute/path/to/file-pr/scripts/local-review/dist/cli.js"
node "$RUNNER" --help
node "$RUNNER" draft-template
node "$RUNNER" review --repo /absolute/repo --base origin/main --head HEAD \
  --goal 'Describe requested behavior' --builder-model openai/gpt-6.1-sol \
  --attempt stable-filing-id --dry-run
```

Help/draft/dry-run do not read keys or generate. Review dry-run inspects local source/runtime; verify dry-run only describes intended work. JSON stdout, redacted stderr. No auto-install, auth discovery, fetch/rebase/stage/commit/push/GitHub writes. Scope and helper safety are the same in both harnesses.

Save a template only to an explicitly chosen **canonical private directory outside Git**, with file mode 0600 and owner permissions. It stays `DRAFT` until actual operator approval. Do not paste keys into chat. Key must be a separate private 0600 file, never an environment fallback or normal Pi/Claude auth. Approval names its exact path, model, full upstream tag, expected reported provider, privacy/ZDR/account-logging consent, source export, key read, expiry, limits and repository/base/attempt/head scopes. Choosing a route requires user approval; metadata availability doesn't grant consent.

Calibration purpose permits only scoped synthetic reviews. Filing additionally requires explicit user rollout signoff/evidence bound to current runtime hash. Head scopes are exact: authorize new fix SHA before second full review, retain attempt ID. Operator configuration records trusted authority; fields alone are not cryptographic proof of consent. The coding agent must not invent approvals.

```sh
node "$RUNNER" preflight --approval "$APPROVAL_JSON" \
  --repo "$REPO" --base "$BASE" --head HEAD --goal "$GOAL" \
  --builder-model "$BUILDER_MODEL" --attempt "$ATTEMPT_ID"
node "$RUNNER" review --approval "$APPROVAL_JSON" \
  --repo "$REPO" --base "$BASE" --head HEAD --goal "$GOAL" \
  --builder-model "$BUILDER_MODEL" --attempt "$ATTEMPT_ID"
node "$RUNNER" verify --approval "$APPROVAL_JSON" \
  --report "$REPORT_JSON" --triage "$TRIAGE_JSON" \
  --repo "$REPO" --base "$BASE" --head HEAD
```

Preflight checks fresh public model/route/pricing metadata, not key access or paid generation. Live review reads only approved key; host owns HTTP, workers never receive it. Production verifier checks current authority and metadata without reading key. Only live filing verification can authorize normal review gating; calibration and simulation always reject for upload. Parent triage/fixes and publishing procedure: [local-review workflow](../../workflows/local-review.md).

| Exit | Meaning |
| --- | --- |
| 0 | Command success; review has no actionable candidates. Help/dry-run/review-0 alone are not upload authority. |
| 10 | Complete review with candidates requiring parent triage. |
| 20 | Incomplete, uncertain, locked, exhausted or invalid evidence. |
| 21 | Stale identity or dirty source. |
| 30 | Setup/model/authority failure, including simulated upload verification. |

## Bounds and billing

- Two rounds, two concurrent fresh lenses, three generation requests and eight source calls/lens; whole-round 120-second deadline includes capture. Second round reviews full PR diff. No retry, compaction, judge, fallback, server tools/plugins or background continuation.
- 3,000 output tokens, 60 changed files, 128 KiB diff, 200 lines/8 KiB read, 50 hits/8 KiB search and **32 KiB final HTTP JSON**, including history/tools/route controls. Never slice required coverage. Byte bounds are not certified native token counts.
- Approved scheduling ceiling **$1.02/attempt**. At observed highest tier $0.50/M input, $2.50/M output, reserve full advertised 1M context plus capped output: **$0.5075/request**. Two concurrent holds fit. This is deliberately pessimistic reservation, not expected price. Example 20k input + 3k output at low tier is $0.0035 before other applicable charges; not measured usage.
- Serialized ledger reservations precede HTTP. Known actual usage/cost replaces hold and releases unused amount. Missing/invalid usage, failed HTTP, timeout/cancellation, over-reservation cost or failed persistence retains uncertainty, aborts sibling and blocks new dispatch/retry. Scheduling guard is not a provider invoice guarantee.
- Exact model and full upstream pinned; no fallback or redirect/retry. Fresh metadata validates all price tiers/capabilities and refuses unbounded charges/caching. Unit-price routing is not total-request budget. Requested regional tag and actual reported provider are recorded separately; metadata isn't independent data-residency proof.

## Source and state

Strict schemas/derived types in `contracts.ts`. Receipts bind actual runtime/SDK/lock/prompt/tools/filter/settings, execution mode and authority/admission identity. Digests detect drift/corruption, not a malicious local operator. Quotes establish location, not allegation truth. P0–P2 remain actionable; every candidate needs evidence-backed parent disposition.

Snapshots use pinned Git base/head/merge-base/tree, isolated config/index and credential-free argv-only object reads. Only `read_git` and literal `search_git`; no checkout scripts/hooks/filters/fsmonitor/textconv/lazy fetch/network. Changed secret/private/binary/LFS/symlink/submodule/vendor/generated/oversize source blocks completeness. Lockfiles expose summary plus exact ecosystem-matching manifest. Initial payload contains complete diff and required context only; unchanged tests/contracts remain accessible through bounded tools, not eager embedding. Conservative secret filtering is not an export guarantee.

Reports/triage/ledger live outside checkouts, default `~/.local/state/file-pr-review`: directories0700/files0600, exclusive temporary writes, fsync/atomic rename and attempt lock. No full transcript persistence beyond finding snippets. Exact completed identity can reuse; uncertain/interrupted state never auto-resumes. Parent waits for both workers on failures; IPC disconnect exits children after parent death. Reconcile owned lock/billing before explicit recovery; don't delete uncertainty to reset budgets.

## Calibration and rollout

[Calibration protocol](test/calibration/README.md) covers offline preparation, separately approved collection, explicit source-backed grading, both-harness evidence and human signoff. Commands:

```sh
node "$RUNNER" calibrate prepare --root "$PRIVATE_RUN" --id calibration-unique-id
node "$RUNNER" calibrate draft --root "$PRIVATE_RUN"
node "$RUNNER" calibrate run --root "$PRIVATE_RUN" --approval "$APPROVAL_JSON" --builder-model "$BUILDER_MODEL"
node "$RUNNER" calibrate grade --root "$PRIVATE_RUN" --judgments "$JUDGMENTS_JSON"
node "$RUNNER" calibrate qualify --root "$PRIVATE_RUN" --judgments "$JUDGMENTS_JSON" --records "$RECORDS_MANIFEST"
```

`run` needs a separate user-approved aggregate `calibrationBudget` in the same private approval, bound to prepared manifest hash. Draft budget is a proposal, not authorization. Grading never invokes a judge model. Qualification checks critical schema-1 record fields, complete case/profile coverage for Pi and Claude Code, current skill hash, assertion coverage and nonempty private local primary artifacts (<=32MiB each). It does not independently prove human assertion truth or fully validate every optional run-record field. Output remains `approved:false`, awaiting actual user signoff. Fixture tests cannot qualify live quality. No subscriptions/hooks/cloud account settings are changed.
