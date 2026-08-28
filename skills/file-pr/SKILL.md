---
name: file-pr
description: Creates concise GitHub pull requests from the current branch and diff. Use when the user asks to file, open, or create a PR.
compatibility: Requires a Git repository, access to its remote, and authenticated GitHub tooling or equivalent pull-request API access.
metadata:
  category: pull-request-automation
---

# File PR

## Workflow

1. Check whether the current branch already has an open PR. Update or report the existing PR instead of creating a duplicate.
2. Inspect the diff against the intended base branch and confirm it matches the user's goal. Stop on an empty, unrelated, or unexpectedly broad diff.
3. Review recently merged PRs and Git history for repository title and description conventions.
4. Write a concise title that explains why the change matters. PR titles often become commit messages.
5. Open the description with the problem in user-facing terms, then summarize the solution and validation. Do not lead with an implementation inventory.
6. Respect repository policy and the user's request when choosing draft versus ready-for-review status. Default to ready when review automation requires it and no contrary policy applies.
7. Create the PR, then verify its URL, base branch, head branch, title, status, and rendered description.

Prefer a concrete title:

- Weak: `perf(server): negotiate permessage-deflate on the websocket`
- Strong: `perf(server): cut websocket frame size by 70%+ with gzipping`

Do not invent measurements; use a quantified title only when the diff or validation supports it.

If the user also asks for monitoring, continue with `babysit-pr` after the PR is verified.
