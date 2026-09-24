---
name: karpathy-guidelines
description: Applies cautious, scope-controlled coding practices that surface assumptions, favor simple solutions, make surgical changes, and verify outcomes. Use when implementing, reviewing, debugging, or refactoring code where ambiguous requirements, hidden scope, or unnecessary complexity are risks.
license: MIT
compatibility: Has no runtime dependencies. Project instructions, required adjacent changes, and explicit user requirements take precedence over its caution defaults.
metadata:
  category: coding-practice
---

# Karpathy guidelines

Apply these guidelines in proportion to task risk. Trivial, unambiguous edits need no ceremony. Caution must not block required adjacent changes.

## Before coding

- Read the relevant code and project instructions.
- Surface assumptions that affect behavior, scope, or compatibility.
- Ask only when unresolved ambiguity could materially change the result.
- If several approaches are valid, choose the simplest one that fits existing conventions and briefly note the tradeoff.
- Define observable success before editing.

For a multi-step task, use a short plan:

```text
1. [change] -> verify: [check]
2. [change] -> verify: [check]
```

## Keep the solution simple

- Implement only requested behavior.
- Avoid speculative options, abstractions, and configuration.
- Reuse established project patterns.
- Add error handling for realistic boundaries, not impossible scenarios.
- If the implementation is much larger than the behavior warrants, simplify it.

## Make surgical changes

Every changed line should support the request or keep the repository valid.

- Do not reformat, rename, or refactor unrelated code.
- Match local style even when another style is preferable.
- Remove imports, variables, or helpers made obsolete by this change.
- Do not remove pre-existing dead code unless requested.
- Mention unrelated findings without silently fixing them.

Adjacent edits are justified when the requested change would otherwise leave broken tests, types, call sites, generated artifacts, documentation contracts, or migrations. Keep those edits minimal and explain the dependency.

## Verify in a loop

1. Run the smallest check that can disprove the change.
2. Fix failures caused by the change.
3. Repeat until that check passes.
4. Run the relevant broader test, lint, type, or build checks when available.
5. Review the final diff for unrelated edits and verify each success criterion.
6. Report what was and was not verified; never claim checks that were not run.
