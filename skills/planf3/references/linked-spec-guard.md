# Linked spec guard

The PR course/spec guard for `full-send`, `half-send`, and `babysit-pr`. It stops a PR from silently changing accepted plan criteria, accepted `specs/COURSE.md` text, protected paths, or `Status: Accepted` ADRs. `scripts/spec_guard.py` does every git, ref, blob, and survival step; this page says when to call it and what to decide. Run `python3 <planf3-directory>/scripts/spec_guard.py <subcommand> ... --json`.

Exit 0 is mechanically clean, but still read any non-empty judgment fields (`changed_paths`, `spec_course_adr_diffs`, `base_constraints`). Exit 1 is a guard violation: fix it or Ask. Exit 2 is bad input, an unreachable remote, a lost baseline, or a ref conflict: Ask.

## 1. Start, resume, or skip

- **Resume first.** When continuing a run (a watcher wake, the Step 4 to Step 5 handoff, a new session with saved IDs), call `spec_guard.py pin --resume --guard-prefix <p> --invocation-id <id>` before anything else.
- **Fresh run.** After checking out the named branch: `spec_guard.py pin --base-remote <remote> --base-branch <base>` (or `--local-base <base>` without a remote) `--push-remote <remote> --branch <branch>`. For an open PR add `--repo <owner/repo> --pr <n> --head-sha <headRefOid> --branch <headRefName>`, plus `--checkout-owns-pr` only after confirming the local checkout is that PR. Pass each spec the user, PR title, or PR body names with `--spec <path>` (the script does not parse PR text). At `pre-push`, pass the outgoing commit as `--cand-sha <sha>`.
- **Lost IDs.** If a fresh `pin` returns `resume_required` with non-empty `prior_runs` (it scans the PR and branch namespaces), resume that run or Ask. Never skip.
- **Skip.** `guard: n/a` means no spec is bound and neither the base nor the candidate touches `specs/COURSE.md`. Keep `initial_head_sha` and `initial_merge_base`, and at every later gate call `spec_guard.py pin --run-start-head <initial_head_sha> --run-start-merge-base <initial_merge_base> [--cand-sha <sha>] [--pre-rebase-head <sha>] [--pending-lease <sha|absent>]`. While it still says `guard: n/a`, stay skipped but push its exact `cand_sha`. Once it returns IDs, adopt them and run every remaining gate and `cleanup`; if that happens at the rebase gate, run `rebase-pin` with the new IDs before rebasing.
- **Carry both IDs.** Keep `guard_prefix` and `invocation_id` across wakes, checkouts, and handoffs, and pass `--guard-prefix <p> --invocation-id <id>` on every call after `pin`. `check`, `survival`, and `rebase-pin` also need the same base flags on every call, and `rebase-pin` the same `--push-remote` and `--branch`.

## 2. Gates while guarded

1. **Before editing**, read `pin`'s `base_constraints` from the fetched `base_sha`: Protected Boundaries, Non-Goals, and `Status: Accepted` decisions and ADRs.
2. **Before each commit**, run `spec_guard.py check --stage pre-commit`.
3. **Before each rebase**, on a clean tree, run `spec_guard.py rebase-pin --pre-rebase-head <HEAD>` (guarded) or `spec_guard.py pin --pre-rebase-head <HEAD>` (`guard: n/a`). Keep the returned `pre_rebase_head`, `pending_lease` (`absent` when the branch is unpublished), and `push_endpoint` until a post-rebase push succeeds. A second rebase before that push passes the kept `--pre-rebase-head <pre_rebase_head> --pending-lease <pending_lease>`, not the current `HEAD`. Rebase onto the returned `base_sha`, then run `spec_guard.py survival` at once (also after `git rebase --abort`).
4. **On `remote_head_diverged` or a rejected lease push**, never merge remote commits into the rewritten head. Save the post-rebase commits on a backup ref, reset to `pre_rebase_head`, integrate the remote-only commits there, cherry-pick the saved commits back, rerun the gate, and rebase again. Ask only on a conflict.
5. **Before every push**, on a clean tree, run `spec_guard.py check --stage pre-push --cand-sha <HEAD>` (or `pin --cand-sha` while skipped). Push only its returned `cand_sha`, to the `push_endpoint` you kept from `pin` or the rebase gate (`check`, and any call without `--push-remote`, returns none):
   - Ordinary update: `git push <push_endpoint> "${cand_sha}:refs/heads/<branch>"`, a normal fast-forward with no lease. Only the first push of an unpublished branch (`observed_remote_sha` is null) adds `--force-with-lease=refs/heads/<branch>:`.
   - After a rebase, guarded or `guard: n/a`: `git push --force-with-lease=refs/heads/<branch>:<pending_lease> <push_endpoint> "${cand_sha}:refs/heads/<branch>"`, leaving the value after `:` empty when `pending_lease` is `absent`. Never use a later reading, and never a lease without its expected value.
6. **Filing (`full-send` Step 4).** Push the validated `cand_sha` first, then use `file-pr` publish-only: its title, body, and PR creation on that pushed head and base, with zero commits or pushes inside `file-pr`. If an edit is needed, leave `file-pr`, commit, rerun `pre-push`, and push the new `cand_sha`. When guarded, run `spec_guard.py bind-pr --repo <owner/repo> --pr <n>` right away and hand the returned PR `guard_prefix` and the `invocation_id` to Step 5.
7. **Before calling the PR ready or merging**, even with zero bot comments, run `spec_guard.py check --stage final --repo <owner/repo> --pr <n> --head-sha <headRefOid>` (or `pin` against the fresh base and live head while skipped).
8. **On terminal completion**, run `spec_guard.py cleanup`, then `spec_guard.py cleanup --prune-stale --older-than-days 14`. Skip cleanup when handing off to `babysit-pr`.

## 3. Takeover, CI guard, and merging

A **qualifying required CI guard** is a trusted, always-run required status check (branch protection or a ruleset) that must run and conclude `success` (never `skipped` or `neutral`), runs this mechanical validation, and fails closed on any unapproved `accepted_criteria_changed`, `governed_course_changes`, bound-spec deletion, or `protected_path_hits` unless a human or CODEOWNERS review gates it. It treats local `approvals.json` items as unapproved. For a non-queue merge it must run on the actual merge candidate, or on the PR head with GitHub's "Require branches to be up to date before merging" on; for a merge queue it must run on `merge_group`. It is absent by default: assume none until you have verified one.

- **Takeover check.** Without a qualifying guard, whenever the guard is active, `prior_runs` is non-empty, or right before a push whose pre-push `pin --cand-sha` activates it: the PR is open, auto-merge is off, and it is not in an unguarded merge queue. Under `full-send` or `half-send`, disable auto-merge or dequeue it (Ask if blocked). Standalone `babysit-pr` Asks instead of flipping the user's setting. A PR that stays `guard: n/a` needs no takeover.
- Never enable auto-merge early while checks or reviews are pending. At the Merge gate, re-run `spec_guard.py pin` against the freshly fetched base and the live PR head.
- Always head-pin a direct merge to the checked `cand_sha`: `pull_request_merge` with `expectedHeadSha: <cand_sha>` and `auto: false`, or `gh pr merge --match-head-commit <cand_sha>`, even on `guard: n/a`. A small client-side race on the base tip remains; only a qualifying CI guard closes it.
- A guarded PR in a repo that requires a merge queue without a qualifying `merge_group` guard is an Ask. Enter a merge queue normally only when the PR is still `guard: n/a` at the Merge gate.

## 4. What needs the user

Criteria already in a bound spec on the base, at run start, or at the initial PR head are accepted; criteria written during this run are not frozen yet. `specs/COURSE.md` at run start is not auto-accepted. Ask before any unrequested change to or drop of an accepted `.criterion` (an agent-written amendment is a record, not approval), deleting an accepted bound spec, any `governed_course_changes` entry, or any `protected_path_hits` entry, including linked `Status: Accepted` ADRs. Entries tagged `upstream_base` came from the base, not this PR; `rebase_recommended: true` means rebase. Milestone `Spec`/`Status` and Area Map updates are exempt.

Only after explicit approval, or when the user's request already names that protected file, record exactly that item and nothing broader: `spec_guard.py approve --guard-prefix <p> --invocation-id <id>` with `--delete-spec <path>`, `--amend-criterion <spec>:<ac-id> --from-text <old> --to-text <new>`, `--delete-criterion <spec>:<ac-id> --from-text <old>`, or `--allow-path <file> --from-entry <mode:oid|absent> --to-entry <mode:oid|absent>`, each with `--reason <text>`. A later rewrite or mode change needs a new approval.

## 5. Spec sync

Before editing a bound spec, copy it to a temp snapshot. Refresh its evidence after the last behavior change or rebase; while proof is pending, set the affected task and its phase to `[]` and prefix the evidence with `Stale:`. Validate with `validate_plan.py <spec> --previous <snapshot> --strict`, then delete the snapshot.
