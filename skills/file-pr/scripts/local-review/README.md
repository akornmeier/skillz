# Local review foundations (Phase 1 only)

Offline-only library. No reviewer runtime, CLI, model calls, credentials, GitHub integration or upload authorization. `Policy.live` must be `false`. Original skill remains unchanged until Phase 3.

## Setup and checks

From repository root, using Node >=22.19.0 (same engine as SDK 1.3.0) and pnpm 12.9.1:

```sh
pnpm --dir skills/file-pr/scripts/local-review install --frozen-lockfile --ignore-scripts
pnpm --dir skills/file-pr/scripts/local-review run validate
node evals/scripts/validate-cases.mjs
```

Direct dependencies are exact pins, including `@earendil-works/pi-coding-agent@1.3.0` and `typebox@1.3.27`. Package `.npmrc` disables lifecycle scripts. Vitest discovers only `test/*.test.ts` here, never copied product suites. Tests create disposable synthetic repos outside skill discovery and never configure a remote. The SDK is installed but not imported or initialized by Phase 1.

SDK design prerequisite inspected: installed 1.3.0 `docs/sdk.md` (complete) and `examples/sdk/12-full-control.ts` (complete). Future runtime must implement the plan's stronger isolation and disabled retries, not copy the example's permissive defaults.

## Contracts

`src/contracts.ts` owns strict TypeBox schemas and their derived static types. Unknown properties reject. Consumers should use these rather than duplicate shapes.

- `validateRequest` rejects unsafe refs and non-independent/unknown builder identity.
- `sealReport`/`validateReport` bind minimized report content and exact receipt identity with canonical SHA-256 digests. Digests detect corruption and mismatches, not malicious modifications by the same local user. They do not prove allegations true.
- `validateFindingEvidence` checks exact quote, span and changed-line overlap. Snapshot's `validateFinding` additionally enforces pinned source/filter access. Every candidate must pass it before sealing a report. Base-side findings refer to deleted lines at **merge-base**, not the intended base tip.
- P0–P2 remain actionable, including P2. P3 alone does not block. Parent still records evidence-backed dispositions for every finding. Fixed-at-SHA is not permission to reuse an old report after a fix.
- Incomplete/uncertain accounting cannot become a complete reusable report. Missing metrics are unavailable, never fabricated zeroes. Fixture zero costs describe synthetic responses only.
- `EXIT`: 0 complete/no actionable candidates, 10 candidates need triage, 20 incomplete, 21 stale/dirty, 30 setup/identity. None authorizes push.
- `saveReport`, `loadReport`, `saveAttempt` use dedicated private state outside checkouts. Default root is `~/.local/state/file-pr-review`. New directories are 0700, files 0600; writes use same-directory exclusive temporary files, fsync and atomic rename. JSON is authoritative; Markdown is a minimized summary. No source/transcript persistence beyond finding evidence snippets. Attempt ownership/locking and freshness authorization belong to Phase 2.

## Immutable source

`captureSnapshot(validatedRequest)` returns `{ snapshot, tools, validateFinding }`:

- `snapshot.payload` is the only initial source payload intended for a future reviewer. It contains goal, full changed-path inventory, complete filtered patches with surrounding lines, small relevant tests/contracts when they fit, and changed-path omissions. Serialized UTF-8 size is checked without slicing.
- `snapshot.identity` binds canonical repo/common Git directory, intended refs, resolved base/head/merge-base/tree IDs and payload digest. Intended base is resolved once; review uses merge-base…head. `snapshot.omissions` retains all filtered path/revision reasons for local coverage reporting, not automatic source export.
- `tools` has exactly `read_git(revision, path, start, end)` and `search_git(revision, literal, pathPrefix)`. `revision` is `base` (merge-base) or `head`. Both use filtered, hash-verified, pinned, in-memory Git blob text, never the current checkout. No shell or filesystem tool is exposed. Search reports `truncated` and `excludedFiles`; absence of hits does not prove complete repository coverage. A denied required read or truncated required search must make the future lens incomplete.
- User refs never become shell strings. Git uses `/usr/bin/git`, a credential-free environment and isolated config/index. Repo clean/process filters, fsmonitor, hooks, external diff, textconv, replace objects, lazy fetching and network protocols cannot execute on the read path. Initial metadata-only ref discovery uses Git; source reads use pinned blob IDs. Temporary metadata is removed before returning tools.
- Ordinary tracked, staged and nonignored untracked changes reject; sparse/assume-unchanged index flags also reject. Ignored private files are never added or exported. Submodule contents are never visited; gitlinks and symlink blobs are filtered, and changed ones block completeness.
- Secrets/private paths, non-UTF-8/binary data, LFS pointers, generated/vendor payloads and oversized blobs are filtered. Changed excluded source is incomplete. Lockfiles expose only object/size summary plus matching manifest context. Secret detection also checks goal and diff metadata. It is conservative, **not an export guarantee**.
- Pilot ceilings: 60 changed files, 128 KiB diff, 200 lines/8 KiB read, 50 hits/8 KiB search, 32 KiB serialized initial payload. Tree/scan/blob/Git-output/deadline bounds also apply before returning a snapshot. Future runtime must independently enforce the 32 KiB bound on every complete transport request, including prompts, tool schemas, history and outputs.

## Fixture evidence, not skill qualification

`test/gate-fixture.ts` is a scripted operation-log boundary with no process/network API. Tests distinguish lookup/fetch/metadata from writes; denied stub publishing, current receipt ordering, two rounds, evidence-backed dismissal and explicit bypass are fixture self-checks only. They do not execute the skill or claim behavioral qualification. All three existing eval cases/profiles and the original skill digest are frozen in `test/gate.test.ts`; eight gate scenarios were added before skill expansion.

Phase 2 owns SDK sessions, transport budgets, settlement, attempt locks, orchestration and freshness/triage authorization. Phase 3 owns executable skill integration and separately approved calibration. Live activation remains disabled.
