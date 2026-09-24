---
name: babysit-pr
description: Monitors GitHub pull requests through CI and automated review. Use when the user asks to watch, monitor, or babysit a PR, investigate failed checks, or respond to review-bot comments.
compatibility: Requires access to the pull request, its source repository, and authenticated GitHub tooling or equivalent review and CI APIs.
metadata:
  category: pull-request-automation
---

# Babysit PR

Finish a scoped PR, not an unlimited bot-improvement loop. Default: **two autonomous repair pushes** per babysit request. "Until green" does not waive this limit. A new head SHA, review, rebase or resumed session does not reset the count.

## Review freeze

- Identify the head SHA, required checks/approvals, expected automated reviews and repair pushes already made.
- **Freeze tracked-file edits and further pushes immediately after every push**, before a review-start event appears. Also freeze when an expected review is requested, queued or running for the current head SHA.
- Use workflow/check-run lifecycle signals keyed to the head SHA, not an earlier head's completed run. Copilot may expose `Running Copilot Code Review`. A streamed comment is not review completion.
- A temporarily missing run is not proof that no review is expected. If no automated review is configured/requested for this PR, no review wait is needed.
- While frozen: inspect source/logs, run non-mutating checks and collect findings. Reproductions needing edits wait or use disposable copies, not the PR branch. No speculative cleanup.
- Recheck head SHA and review state before each edit batch and before pushing. If a review starts mid-batch or the head changes externally, pause and reassess; preserve local edits without resetting or discarding them.
- Bound each expected-review wait to **30 minutes by default**; status changes do not restart it. Escalate missing, failed or stalled reviews: ask whether to keep waiting or proceed without an optional review. Never assume completion or waive required checks/approvals.
- Do not cancel reviews to unlock editing. Only an explicit user decision overrides the optional-review wait; disclose the unfinished review.

## One review batch, one repair push

After the review freeze ends and CI results are available:

1. Collect the complete batch: inline threads, review summaries (including suppressed findings) and CI failures.
2. Revalidate against the current head SHA and original acceptance criteria, not just old citations. Old-head findings may still be real; deduplicate repeats and explain already-addressed ones.
3. Assign a disposition:

   | Finding | Action |
   | --- | --- |
   | Verified in-scope defect eligible for this repair round | Include in the batch |
   | Already addressed or false positive | Explain with evidence; no edit |
   | Optional hardening, wording/style nit or scope expansion | Defer with a concise reason |
   | Infrastructure failure | Report honestly; bounded retry only with a credible transient-failure hypothesis |

4. Apply the escalating bar:
   - **First repair push:** verified defects within the PR's original acceptance criteria.
   - **Second repair push:** repair regressions or demonstrated release blockers, not another sweep of improvements. A blocker means broken acceptance/required CI, incorrect required results, or a concrete security/data-integrity risk. Bot severity alone is not evidence.
   - **After two repair pushes:** no more autonomous edits or repair pushes. If a verified release blocker remains, present evidence and request approval for another scoped batch. Do not dismiss it because it arrived late, or merge past it.
5. If eligible repairs remain, make one scoped batch. Run focused checks and repository-mandated validation once per batch; rerun after failures as needed. Benchmark only when affected or required. Tie verification claims to the revision actually tested.
6. Reply with dispositions and resolve only addressed threads. For a repaired batch, push once, increment the count and return to the review freeze. Otherwise evaluate the finish condition. Use monitoring events when available; otherwise poll without filler comments.

## Finish condition

Report ready when all are true:

- Required checks pass on the current head SHA.
- Required repository approvals are satisfied.
- Verified in-scope release blockers are addressed and remaining findings have explicit dispositions.
- The review freeze has ended through completed expected reviews, confirmed absence of expected reviews, or an explicit user decision about an optional review.

Optional bot wording such as "needs a closer look" is not a release gate. Do not request another review merely to obtain green prose. If ready, finish; if blocked, report the blocker and decision needed instead of continuing silently.

Follow repository policy for rebases. If base changes require a rebase or an overlapping PR makes this PR obsolete, report the condition before destructive or externally visible action. Never close or merge without authorization.

When responding on Tony's behalf, use:

```md
[MODEL-SLUG] RESPONDING ON BEHALF OF TONY
-----

[actual reply]
```

For visual findings, attach verified screenshots/videos when available without exposing sensitive content.
