---
name: hillclimb
description: Frames an improvement goal as a council-scored hill climb (target items, scoring unit, pass bar, scope limits, a three-provider council) and runs fix-and-rescore rounds until every member scores every item at or above the bar. Use when the user says "hillclimb" or "hill climb", or asks to keep improving something until a review council agrees it reaches a target score.
---

# Hillclimb

Turn a broad "make it better" request into a fixed frame, then climb: the council scores every item, you fix what holds up, and the council scores again until every member clears the bar. This skill owns the frame, the roster and the round briefs. Follow [council](../council/SKILL.md) for delegation mechanics, round counting, the PR results table, and its satisfaction and deadlock rules.

## 1. Frame the goal

Fill each field from the request. Use the default when the request is silent.

- **Target:** the exact items to score, enumerated (for example every `skills/*/` that is not gitignored, the files in a PR, the pages of a doc set). A council cannot score "everything".
- **Unit:** one score per target item. A member's overall score is their lowest item score.
- **Bar:** every member scores every item at least 9/10.
- **Rubric:** 3–5 dimensions the score covers. Take them from the request or the repo's own review guide; otherwise use correctness, effectiveness for its intended use, economy, and safety. Name items that are deliberately unusual so members judge them against their intent.
- **Out of scope:** no new features, no restructuring beyond what fixing errors requires, nothing outside the target, no paid or model-run checks the user has not approved. Add the user's own limits.
- **Checks:** the commands that must pass after every round (tests, linters, validators).
- **Delivery:** a branch and PR named from the user's words when they ask for a PR; otherwise commits on a branch, reported at the end.

Ask only when the target cannot be enumerated or the request conflicts with a default, and propose the default in the question.

## 2. Set the council

- Use the members the user names. Otherwise take one member each from Claude (latest Opus), OpenAI (latest GPT Sol) and Muse (its latest flagship), at the reasoning effort council specifies.
- Resolve exact model IDs at run time, with `orchestrator_capabilities` in T3 Code or the harness's model list elsewhere; never reuse IDs from memory. When a provider lists several current lines, take its top tier and say which.
- Council's rule applies before round 1: report an unavailable member or fewer than three reachable providers and stop; never substitute.
- Record each member's provider, model ID and effort in the frame. Keep the roster fixed for the whole climb; a replaced member starts a new column in the results table.

## 3. Prepare round 1

Fix known issues and run the checks first. Show the frame, with the roster and checks, in a few lines before sending round 1. When delivering a PR, create the branch, commit, and open the PR with `file-pr` before round 1, so every member reviews the same commit. If there is nothing to commit yet, review the current commit and open the PR once the first fixes are committed; if the council finds nothing to fix, report that and open no PR. Build the brief from [references/brief.md](references/brief.md) and send it complete and unchanged to all members in parallel; delegates get no conversation history.

## 4. Run rounds

1. Wait for every member before editing the target. They read the same checkout.
2. Merge findings by item. Verify each against the source before acting on it or repeating it in the ledger or report; a reviewer's claim or severity is not proof.
3. Fix verified blockers with the smallest edit. Decline the rest (out of scope, unverified, nits, features) with a one-line reason each. Give large independent fixes to subagents that each own separate files.
4. Run the checks, commit the round, and push when delivering a PR.
5. Send every member, satisfied or not, the next-round brief: the same frame plus the ledger.

Stop when council's satisfaction rule holds. Also stop and ask the user when no member's lowest score rises from one round to the next, showing what keeps each low. After all members are satisfied, apply a member's suggested correction only if it is a pure fix of an error, and disclose it rather than starting another round.

## 5. Report

Put council's results table in the PR description, noting that each cell is that member's lowest item score. Report rounds, the main changes, declined findings with reasons as follow-ups, the checks run, and anything left unverified.
