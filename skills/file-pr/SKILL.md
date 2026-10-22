---
name: file-pr
description: Creates concise GitHub pull requests from the current branch and diff. Use when the user asks to file, open, or create a PR.
compatibility: Requires Git, remote access and authenticated GitHub tooling. New-code review requires Node >=22.19, pnpm 12.9.1, pinned Pi SDK package and explicit OpenRouter key/scope approval; production use additionally requires calibration and rollout signoff.
metadata:
  category: pull-request-automation
---

# File PR

## Workflow

1. Look up an existing PR read-only. Compare its head SHA with the local candidate. If no new code needs uploading, report the existing PR without inference; never create a duplicate.
2. Inspect the diff against the intended base and confirm the user's goal. Stop on an empty, unrelated, or unexpectedly broad diff. Review recent merged PRs, Git history and the PR template for conventions.
3. Before any push or PR write containing new code, follow [local-review.md](workflows/local-review.md). It owns authorized fetch/rebase, focused checks/commits, independent review, parent triage, at most one fix/re-review and immediate receipt verification. Resolve helpers from this skill directory, not the target repository.
4. **Live review is explicit opt-in.** Require private scoped OpenRouter approval and qualified user rollout signoff. Help/dry-run/draft commands never read the key or invoke models. Missing approval/prerequisites, incomplete/stale evidence or remaining P0–P2 findings stop upload. Do not auto-install, substitute models, use harness subscription auth or treat simulations as passed. Only an explicit per-attempt user waiver may bypass review, labeled **bypassed** in PR validation.
5. Write a concise supported title explaining why the change matters. Open the description with the user-facing problem, then solution and actual validation. Do not lead with an implementation inventory. End with the actual model and harness attribution; do not publish private reports/transcripts.
6. Respect repository policy and requested draft status. Default to a real, ready-for-review PR when no contrary policy applies.
7. After current receipt verification (or disclosed explicit waiver), push only authorized changes and create/update the existing PR. Never silently force-push rebased published history. Verify URL, base/head branches and SHA, title, status and rendered description.

Same skill and Node runner support both harnesses: Claude Code `/file-pr`; Pi `/skill:file-pr`. Pi CLI is not required by the runner. Review uses an explicitly approved OpenRouter API key, not either harness's subscription/auth.

Prefer a concrete title:

- Weak: `perf(server): negotiate permessage-deflate on the websocket`
- Strong: `perf(server): cut websocket frame size by 70%+ with gzipping`

Do not invent measurements; use a quantified title only when the diff or validation supports it.

If the user also asks for monitoring, continue with `babysit-pr` after the PR is verified.
