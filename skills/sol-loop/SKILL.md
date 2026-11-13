---
name: sol-loop
description: Reviews a change with GPT Sol and a cross-check model from another provider in a bounded fix-and-re-review loop before or after filing a PR. Use when the user says "sol loop".
---

# sol-loop

This is a workflow for making your code changes more correct before (or
sometimes after) filing a pull request. tl;dr - use OpenAI's GPT Sol, plus one
cross-check model from another provider, to review your code in a loop.

Make the most minimal possible changes to appease the reviewers. Be careful
of scope creep and don't be scared to push back.

## Budget

- Default: 3 rounds total. Round 1 is full. Later rounds check only
  changed code and open findings.
- Extend to 5 only for security, permissions, auth, data loss, or
  state/concurrency, while a blocker or should stays open with evidence. Or when
  the user asks.
- Stop early if a round returns only nits. Declined nits and comment,
  doc, or format-only fixes need no new round.
- Two reviewers: Sol and one cross-check (see 2). A round runs one or both.
  Neither may start subagents or reviewers.
- Keep a ledger: id, reviewer, severity, outcome, usage if returned. Never
  guess it.

## 1. Scope

Run `git status --short`. Do not stash, discard, or include unrelated
changes. Limit review to the change paths if they separate cleanly.
Otherwise stop and ask.

Find the base after `git fetch origin`:

- PR: `gh pr view <n> --json baseRefName,headRefOid`. Check out the branch
  only if clean. Confirm `HEAD` is the PR head, or ahead only by this
  change. Base: `git merge-base HEAD origin/<baseRefName>`.
- Local: `git merge-base HEAD origin/<default-branch>`. No remote: a base
  the user names, or `HEAD` for uncommitted changes only.

The change is base to working tree in those paths, with untracked files.
Use one diff command all rounds. State intent and out-of-scope in 1-2
sentences. Run covering checks. Do not send code this change breaks. Note
missing or pre-failing checks in the brief.

## 2. Start the reviewers

In T3, call `orchestrator_capabilities`. Pick the latest Sol unless the user
named a version. Do not hardcode an ID. Record provider, model, and effort
only if exposed. Use `delegate_task` for each reviewer every round
(`role: "review"`, `mode: "async"`). Save each `taskId`. New
`clientRequestId` per call. `childThreadId` is storage, not the next target.
Do not use `t3_thread_send`, `create_threads`, or `t3_thread_launch` for
review.

If T3 tools are not listed, try one direct capability call. Outside T3, use
a native Sol subagent and keep its ID. In Claude Code, use a custom subagent
only if it is set up to run Sol. If no route runs Sol, report the blocker. Do
not substitute a model. Run the cross-check alone only when a calling skill
such as `full-send` says to; then every rule below applies without Sol.

Cross-check: the latest flagship from a provider other than OpenAI, unless
the user named one. Prefer a provider other than the one whose model wrote
the change (for example Meta Muse when Claude wrote it). If only the
writer's provider is reachable, use its flagship in a fresh context. Resolve
and record it like Sol. Outside T3, use a native subagent (in Claude Code,
`Agent` with a Claude model). If no route runs a cross-check, or it fails
twice, continue with Sol alone and say so in the report.

Start both at once with the same round 1 brief. Ids are `S1`, `S2`... for
Sol and `X1`, `X2`... for the cross-check. Never show one reviewer the
other's findings.

Do not edit scoped files while review runs. Wait for every notice. Do not
poll or start a third reviewer. Timeout, error, or no reply is not
approval. On failure, cancel, verify stop, restart that reviewer with only
its own ledger entries.

Round 1 brief (T3 children get no history; `<P>` is `S` or `X`):

```
Review only. Do not edit, commit, push, comment on PRs, or start subagents.
Repo: <abs path> Base: <sha> Intent: <intent> Out of scope: <scope> Checks: <results>
See: git diff <base> [-- <paths>]; git status --short (read untracked).
Read surrounding code. Find bugs, broken callers, mismatch with intent.
Skip style unless it hides a bug. Hold to the smallest change. Flag code,
tests, or guards the intent does not need. Other paths, rare cases, small
perf, extra compat: nits, unless they risk security, data loss, or corrupted state.
blocker = intended case wrong. should = real bug callers will hit, in intent. nit = rest.
Reply:
VERDICT: APPROVE or CHANGES
<P>1 [blocker|should|nit] <file>:<line> <claim>. Fix: <suggestion> (stable ids <P>1, <P>2...)
```

## 3. Answer findings

Check each finding and severity yourself. Another path, rare case, or
small cost is a nit, whatever label it came with, unless it can cause a
security hole, data loss, or corrupted state in the intended change.

- Agree: smallest fix. Prefer delete or narrow over new lock, cache,
  helper, or option. Fix the case that happened. Add one focused test
  that fails without the fix, if intent needs it.
- Disagree: say why, with evidence (file:line, test, output).
- Out of scope or nit: decline in one line. List as follow-up.

Update the ledger. Re-run checks and `git diff --shortstat <base>`. If
review grew the diff, cut first. Do not agree just to end the loop.

## 4. Next round

If budget remains, send a next round to each reviewer, except a dropped
cross-check, that has a blocker or should open, or whose approval does not
cover the current behavior diff. A
behavior fix made for the other reviewer counts. Use a fresh `delegate_task`
in T3, or follow up the saved native ID. Send the round 1 brief, that
reviewer's ledger entries (`fixed:` / `disagree:` / `declined:` + evidence),
the same base diff, and the change since its last round. Tell it: open ids
and changed code only. Mark each old id `resolved` or `still open: <reason>`.

## 5. Stop and ship

Agreed: every reviewer in the loop (Sol if it ran, and the cross-check unless
you dropped it, see 2) gives APPROVE on the current behavior diff, no
blocker or should open, no concern of your own. A dropped cross-check's open
findings stay in the ledger for you to resolve. If no reviewer is left, the
change is unreviewed, not agreed. Stuck: an item stays
disputed after two replies, or budget ends. Show both sides in 2-3 lines
each. The user decides. Budget end is not approval.

Do not push during the loop. Push after agreement only if the user asked
to push, ship, or update the PR. If you push to a PR, add above the closing model
and harness line:

`Reviewed with sol-loop: <N> rounds with <Sol model>, cross-checked by <model>. Both approved`.

With no cross-check, use
`Reviewed with sol-loop: <N> rounds with <model>. Sol verdict: approved`.
With no Sol, use
`Reviewed with sol-loop: <N> rounds with <model>, no Sol route. Cross-check verdict: approved`.
Add `on <effort>` after a model only if verified.

Report: rounds, models, what each reviewer changed, diff size before/after,
fixed and declined findings with reasons, usage if exposed (else say not),
why Sol or the cross-check was skipped if one was, pushed or not.
