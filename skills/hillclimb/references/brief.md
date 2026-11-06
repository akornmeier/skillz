# Council briefs

Fill the `<...>` fields from the frame. Send the same text to every member; in later rounds only the "Your previous scores" and "Your open blockers" lines differ. Keep the context, goal, rubric, target and scope lines identical in every round so scores stay comparable.

## Round 1

```text
You are one member of a three-member review council. Review only: do not edit, commit, push, comment on GitHub, or start subagents.

Context: <repo path>, branch <branch>, commit <sha>, PR <url or "none">. <One line on what the target is and who or what uses it.>

Goal: <the user's goal in one sentence>. Score each item 1-10 on:
- <rubric dimension>: <what a high score means>
- <...>
<Items that are deliberately unusual, and the intent to judge them against.>

Target: <enumerated items, or the command that lists them>.

Scope limits (the lead enforces these, so do not spend findings on them):
- <out-of-scope item>
- Recommend the smallest edit that gets an item to <bar>/10. Prefer deleting or tightening over adding. Do not propose features.

Useful commands: <checks>.

Reply in exactly this format:

OVERALL: <lowest item score>/10 — satisfied: yes|no (yes only if every item is >= <bar>)

| Item | Score | What keeps it below <bar> |
One row per item.

BLOCKERS
B1 <item> <file>:<line> — <problem>. Fix: <smallest concrete edit>
(only issues that keep an item below the bar; keep your ids stable across rounds)

NITS (optional, max 5, one line each)
```

## Later rounds

Delegates start each round without history, so repeat the full round-1 brief (with the new commit in its context line), then add:

```text
ROUND <n>. Fixes since your last review are in <commit range>. Re-score every item. Check whether your open blockers are resolved and review the changed files. Raise a new blocker only for a regression in changed code or a real defect you missed that keeps an item below the bar; do not move the bar. Carry forward scores for unchanged items unless you find such a defect.

Your previous scores: <this member's per-item scores from the last round>.

Your open blockers: <ids with one-line summaries, or "none">.

Ledger (all members' findings, merged):
fixed:
- <member> <id>, <item>: <what changed>
declined:
- <member> <id>, <item>: <reason>

Reply in the round-1 format, adding this line after the table:
RESOLVED: <ids> / STILL OPEN: <ids and why>
```
