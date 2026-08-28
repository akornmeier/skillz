---
name: babysit-pr
description: Monitors GitHub pull requests through CI and automated review. Use when the user asks to watch, monitor, or babysit a PR, investigate failed checks, or respond to review-bot comments.
compatibility: Requires access to the pull request, its source repository, and authenticated GitHub tooling or equivalent review and CI APIs.
metadata:
  category: pull-request-automation
---

# Babysit PR

Monitor the latest PR revision until required checks and review bots are green. Verify automated findings; do not accept or reject them from the comment alone.

## Monitoring loop

1. Record the PR URL, base branch, latest head commit, required checks, and unresolved review threads.
2. Use the active environment's monitoring capability when available; otherwise poll without posting filler comments.
3. Consider only checks and comments that apply to the latest head commit. Re-evaluate after every push.
4. For each failure or finding:
   - inspect the relevant source and logs;
   - distinguish a real defect from an outdated result, false positive, or infrastructure failure;
   - fix defects within the PR's original scope and run the relevant local checks;
   - reply with a concise source-based reason when dismissing a finding.
5. Push approved repairs, record the new head commit, and repeat the loop.
6. Stop when required checks and review bots are green on the latest commit. Report that the PR is ready unless the user explicitly requested a merge.

Follow repository policy for rebases. If changes to the base branch require a rebase or an overlapping PR makes this PR obsolete, report the condition before destructive or externally visible action. Never close or merge without authorization.

When responding on Tony's behalf, use:

```md
[MODEL-SLUG] RESPONDING ON BEHALF OF TONY
-----

[actual reply]
```

Include screenshots or videos when the active environment supports artifact attachment. Otherwise report verified local paths or URLs without exposing sensitive content.

Do not let feedback expand the PR beyond the user's original goal.
