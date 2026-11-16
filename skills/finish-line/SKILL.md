---
name: finish-line
description: Checks whether a ticket is really finished, whether it is a planf3 spec in specs/, a GitHub issue, or a task defined earlier in the conversation. It verifies every requirement against the code with evidence, finishes small and fully specified gaps, and closes the ticket once nothing is left. GitHub issues close only after the user approves. Use when the user asks whether a ticket, issue, spec, or task is done, what is left on it, or to wrap it up or close it out. Not for building a plan from scratch (planf3) or for shipping a PR (full-send, half-send).
---

# Finish Line

Take one ticket to closed. Build its full requirement list, prove each item against the code, finish the small gaps, and close it once every item has evidence. Output: a verdict table, plus the closed ticket or the exact list of what remains.

## Contracts

- **A claim is not evidence.** A ticked checkbox, a `[x]` marker, a PR that says "fixes #N", a handoff note, and your memory of doing the work are all claims. Evidence is one of three things: a `file:line` on the ref the ticket ships from, a command run in this session with its exit status and observed output, or a reproduced behavior. Never claim a manual, visual, or production check you did not perform.
- **Check where the ticket ships.** For a GitHub issue, fetch and check the default branch. Work that exists only on an unmerged branch is open. For a spec or a task in context, check the current working tree.
- **Finish only small, fully specified gaps:** a missing test, a doc line, a missed sibling occurrence, a failing lint, or an unrecorded verification. If a gap needs a design or product decision, changes required behavior, or would add a whole new feature, mark it open and ask. Never weaken a requirement to fit the code.
- **Stay inside the ticket.** List out-of-scope ideas as follow-ups. Do not build them, and do not file new issues without approval.
- **Closing a GitHub issue needs approval in this conversation for this issue.** Show the verdict and the exact closing comment first. Approval given for another ticket does not carry over. Never merge to land a fix without authorization.

## Steps

1. **Resolve the ticket.** Take the spec path, the issue number or URL, or the task from context. Infer it only when exactly one candidate fits, such as an issue number in the branch name or a single spec for this work. Otherwise ask.
2. **Build the requirement list.** Number each item and keep its source reference.

   | Source | Read | Requirements |
   | --- | --- | --- |
   | planf3 spec | Run `python3 ../planf3/scripts/validate_plan.py <spec>` (path relative to this skill) first, then read the whole spec | Every acceptance criterion (`ac-*`), every task action and its verification, phase Testing Strategy checks, global Validation Commands, and any scope changes in Amendments |
   | GitHub issue | `gh issue view <n> --comments --json title,body,state,comments,closedByPullRequestsReferences` and the diffs of the linked PRs | Body checklists and acceptance criteria. Repro steps, which must no longer reproduce. Later comments from the author or maintainers that add, drop, or change scope. Linked PRs, which must be merged. |
   | Task in context | The user's request and every later correction in this conversation | Each asked-for outcome, plus the user's standing definition of done, such as passing tests, lint, or a build |

3. **Verify each item.** Prefer running a check over reading code: the spec's verification commands, the issue's repro steps, and the project's tests, lint, and build. Grep for sibling occurrences of the change. Mark each item **Done**, **Open**, or **Unverifiable**. Unverifiable never counts as done: ask the user to confirm it or supply the evidence.
4. **Finish the small gaps.** For a spec, follow [planf3's Build Plan workflow](../planf3/workflows/build-plan.md) for task markers, evidence, Amendments, and the snapshot and `validate_plan.py --previous` loop. Re-verify every fixed item and mark it **Finished now**.
5. **Report.** Show the verdict table, then close the ticket the way its source requires:

   | # | Requirement (source) | Status | Evidence |
   | --- | --- | --- | --- |

   - **planf3 spec:** It is finished when every task and check is `[x]` with recorded evidence, the history is appended, and the validator passes with `--previous`. If the spec links a GitHub issue, offer to close that issue too, using the issue rules below.
   - **GitHub issue:** If you changed code, the issue closes only after that change lands on the default branch. Offer `half-send` to land it, with `Closes #<n>` in the PR body. Once every item is Done and landed, show the closing comment, formatted per `leaving-pr-comments`, that lists each item with its evidence. Run `gh issue close <n> --reason completed --comment "<comment>"` only after the user approves. If items remain open, leave the issue open, and post the remaining list as a comment only with approval.
   - **Task in context:** Say it is done, or list exactly what remains and what decision each open item needs.
