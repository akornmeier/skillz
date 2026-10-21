# Local PR review runner

**Offline-only, release unqualified.** Real Pi SDK sessions run against synthetic transport in deterministic tests. CLI has no live transport and reads no provider credentials. Installation does not enable inference. Simulated reports cannot authorize upload. Paid calibration, provider certification and user rollout approval remain outstanding.

## Setup

After explicit scoped provisioning approval, from this repository root:

```sh
pnpm --dir skills/file-pr/scripts/local-review install --frozen-lockfile --ignore-scripts --ignore-pnpmfile
pnpm --dir skills/file-pr/scripts/local-review run validate
```

Node >=22.19.0, pnpm 12.9.1; exact SDK 1.3.0, TypeBox, TypeScript and Vitest pins in package/lock. `.npmrc` disables lifecycle scripts. No global Pi CLI installation required. `validate` runs strict typecheck, emitted build and only `test/*.test.ts`, never target-product suites. Fixture repos/state live outside skill discovery, with no remotes. Test files run serially, including controlled runtime-drift verification.

In an arbitrary target repository, resolve the helper from the loaded skill's location, not cwd:

```sh
RUNNER="/absolute/path/to/file-pr/scripts/local-review/dist/cli.js"
node "$RUNNER" --help
node "$RUNNER" review --repo /absolute/repo --base origin/main --head HEAD \
  --goal 'Describe requested behavior' --builder-model openai/gpt-6.1-sol \
  --attempt stable-filing-id --dry-run
node "$RUNNER" review --repo /absolute/repo --base origin/main --head HEAD \
  --goal 'Describe requested behavior' --builder-model openai/gpt-6.1-sol --attempt stable-filing-id
node "$RUNNER" verify --report /private/report.json --triage /private/triage.json \
  --repo /absolute/repo --base origin/main --head HEAD
```

Help is import-safe. Review dry-run reads/filter-checks local Git objects and hashes runtime without inference or state writes; verify dry-run describes intended work without reading report/triage. Normal `review` currently produces setup-error evidence without inference. `verify` always refuses simulated evidence. Stdout JSON, redacted stderr diagnostics. No auto-install, auth discovery, fetch, rebase, commit, push or GitHub writes.

| Exit | Meaning |
| --- | --- |
| 0 | Help/dry-run, or internal complete fixture with no actionable candidates. Not upload authority. |
| 10 | Complete fixture with candidates requiring parent triage. |
| 20 | Incomplete, uncertain, locked, exhausted or invalid evidence. |
| 21 | Stale identity or dirty source. |
| 30 | Setup/auth/identity failure, including disabled live transport and simulated verification. |

## Boundaries

- `contracts.ts` owns strict TypeBox schemas and derived types for policy, snapshots, findings, receipts, triage and ledger. Unknown fields reject. Canonical digests detect corruption/drift, not malicious edits by the same local user. Finding evidence proves location, not allegation truth. P0–P2 block unresolved; P3 alone does not.
- `snapshot.ts` pins base/head/merge-base/tree and full changed inventory. Base-side reads mean **merge-base**. Clean committed source only; no automatic staging. Sparse/assume-unchanged indexes reject. Source tools use filtered pinned blob text, not host paths or current checkout.
- Exactly `read_git(revision, path, start, end)` and literal `search_git(revision, literal, pathPrefix)` are exposed. Exclusions cover credential/private data, suspected secrets, binary/LFS, symlink/submodule, vendor/generated and oversized payloads. Changed excluded semantic source is incomplete. Lockfiles require their own ecosystem-matching manifest and expose summary only. Secret detection is conservative, not an export guarantee.
- Git uses isolated index/config, explicit credential-free environment and argv-only object operations. No checkout scripts, hooks, filters, fsmonitor, external diff/textconv, lazy fetch or network protocols execute on the source path. Submodule checkout contents are not read.
- `runtime.ts` owns pre-effect reservations and child lifetime; `runtime-child.ts` runs actual SDK sessions with empty resource loader, dedicated empty auth/agent directory, in-memory settings/session, only snapshot IPC tools, retries/compaction/cache warming off. Parent validates finalized response identity and authoritative settlement. Abort-ignoring fixture transport is terminated in its owned child. IPC disconnect exits workers after parent death; rejected persistence aborts and awaits both lenses before releasing ownership.
- `review.ts` runs two fresh lenses concurrently, validates quotes/changed lines/coverage, retains provenance and performs no judge call. One absolute round deadline bounds initial/in-flight Git subprocesses and remaining model time. It recomputes actual runtime/lock/prompt/tool/filter/settings identity during verification. Source changes/fixes/rebases invalidate earlier evidence; second round covers the full PR diff.
- Limits: two rounds, two lenses/round, three requests and eight source calls/lens, 120 seconds/round; 3,000 output tokens/request, 60 changed files, 128 KiB diff, 200 lines/8 KiB read, 50 hits/8 KiB search, 32 KiB complete serialized request. Lower validated ceilings cannot widen policy. Additional tree/scan/blob/Git bounds fail closed rather than slice context.
- Reports/triage/attempt state stay outside Git checkouts, default `~/.local/state/file-pr-review`. Directories 0700, files 0600; exclusive temporary writes, fsync and atomic rename. JSON authoritative; Markdown minimized. No full transcript persistence; finding snippets remain private. Per-attempt lock, round and request reservations precede effects. Exact completed identities reuse reports; unfinished/uncertain work never auto-resumes. Keep one attempt ID across repairs. Never delete uncertainty to reset budgets.
- Missing usage is unavailable/uncertain, not zero dollars. Zero-cost fixture reservations are explicitly simulated, not provider accounting or an approved $0.10 invoice guarantee. Cancellation does not establish remote billing cancellation.

## Qualification

Parent procedure: [local-review workflow](../../workflows/local-review.md). Baseline eval cases/profiles remain frozen; gate tests use a scripted boundary and disposable executable stubs, not actual GitHub publishing or proof an LLM follows instructions. See [calibration protocol](test/calibration/README.md) for frozen synthetic labels and separately approved live gates. No detection, latency, cost, vendor savings or behavioral-profile claims from fixtures.

Before a live adapter can be shipped/enabled: approve route/upstream privacy/source export/key access, certify exact availability/version/token/output/rate semantics and intercepted network limits, implement audited transport/spend settlement, run frozen calibration and all required skill/profile qualification, then obtain explicit sign-off. No configuration flag enables live execution in this build.
