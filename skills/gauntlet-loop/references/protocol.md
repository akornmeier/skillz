# Gauntlet Execution Protocol

Use this only in run mode. The lead owns coordination and integration but may not impersonate independent review.

## Contents

- [1. Establish the run](#1-establish-the-run)
- [2. Inspect primary inputs](#2-inspect-primary-inputs)
- [3. Decompose by judgeable outcomes](#3-decompose-by-judgeable-outcomes)
- [4. Build in isolated contexts](#4-build-in-isolated-contexts)
- [5. Critique from fresh context](#5-critique-from-fresh-context)
- [6. Blind A/B when fair](#6-blind-ab-when-fair)
- [7. Validate findings and repair the largest gap](#7-validate-findings-and-repair-the-largest-gap)
- [8. Integrate and smooth when needed](#8-integrate-and-smooth-when-needed)
- [9. Decide the state](#9-decide-the-state)
- [10. Deliver](#10-deliver)

## 1. Establish the run

Create:

```text
.gauntlet/<goal-slug>/
├── progress.md
├── candidates/
├── critiques/
├── comparisons/
└── evidence/
```

Copy the progress template and record:

- exact goal and constraints;
- inspected reference paths or URLs;
- the one-sentence quality bar and blocking gates;
- harness/delegation capability;
- workspace isolation strategy;
- user, budget, deadline, safety, and blocking stop conditions.

Do not silently commit the run directory or modify `.gitignore`. Follow repository policy.

## 2. Inspect primary inputs

The lead opens every accessible reference, repository instruction, source-of-truth file, relevant existing artifact, and verification command before decomposition. A summary can aid navigation but cannot replace inspection.

If a required reference cannot be accessed, do not pretend it was compared. Either obtain access, substitute a user-approved inspectable bar, or mark the run blocked.

## 3. Decompose by judgeable outcomes

Choose the smallest **useful** pieces that can be improved and judged independently. Do not atomize work just to maximize agent count.

Good boundaries include:

- self-contained visual or behavioral components;
- isolated interfaces with explicit contracts;
- distinct sections or arguments in writing;
- independent functional, visual, accessibility, performance, security, or factuality reviews;
- competing candidates for the same narrow outcome.

Keep tightly coupled work together. Do not let concurrent agents write overlapping files in one workspace.

For every assignment, record owner, fresh-context requirement, workspace, inputs, expected artifact, acceptance evidence, and prohibited scope.

## 4. Build in isolated contexts

Each builder gets:

- original goal and relevant constraints;
- quality bar and primary references;
- owned component/outcome and workspace;
- expected artifact and verification method;
- verified findings from the immediately preceding review when repairing.

A builder does **not** get competing builders' drafts before submitting an independent candidate. It produces the artifact, runs narrow checks, and reports artifact paths plus factual evidence. Builder reasoning and confidence are not acceptance evidence.

When parallel execution is supported, fan out only independent work in a bounded batch. Use separate worktrees, sandboxes, temporary copies, or non-overlapping ownership. Otherwise run sequentially.

## 5. Critique from fresh context

Start a new critic context for each judgment round. Give it:

- original goal, constraints, and quality bar;
- primary reference and candidate artifact locations;
- equivalent inspection conditions;
- relevant verification commands;
- required finding format.

Withhold builder transcript, rationale, self-assessment, model identity, and the lead's preferred answer. A repair critic may receive the defect to retest, but must still inspect the whole affected result for regressions.

The critic must inspect primary evidence and report:

1. verdict: candidate wins, reference wins, tie, neither, or insufficient evidence;
2. criterion-level observations with artifact locations or command output;
3. blocking defects versus material gaps versus optional polish;
4. the single largest meaningful gap;
5. a concrete repair target and how to verify it;
6. confidence and missing evidence.

Unsupported taste is not a defect. A tie or insufficient evidence is not a win.

## 6. Blind A/B when fair

For comparable candidates or candidate-versus-reference judgments:

1. Prepare anonymous A/B packages.
2. Remove author, model, branch, timestamp, chronology, and process identity.
3. Normalize viewport, inputs, fixture data, instructions, and presentation.
4. Preserve the differences that actually matter.
5. Ask a fresh judge for criterion-level results, winner/tie/neither, decisive evidence, confidence, and any required follow-up test.

Do not force blind A/B for complementary pieces or incomparable scope. Use direct objective verification for correctness, security, accessibility, and performance claims that cannot be settled by preference.

## 7. Validate findings and repair the largest gap

The lead checks critic findings against files, rendered output, tests, or measurements. Reject unsupported preferences and record why.

If a material defect remains and a repair has a credible hypothesis:

1. preserve the strongest known candidate;
2. send the verified highest-impact gap to a fresh builder context;
3. make one coherent repair wave;
4. inspect and run affected checks;
5. send the real revised artifact to another fresh critic;
6. update progress.

Do not continue merely because another round is possible. Every round names the defect or uncertainty it intends to reduce.

## 8. Integrate and smooth when needed

After a major parallel wave, the lead selects the strongest verified work rather than merging every suggestion.

Use a fresh smoothing/integration agent only when independently improved pieces conflict or feel inconsistent. Give it the goal, accepted artifacts, constraints, and authority to resolve cross-cutting coherence issues without redesigning or expanding scope. Then use another fresh critic and rerun affected gates.

Smoothing cannot waive correctness or compensate for failed components.

## 9. Decide the state

- **Win:** all blocking gates pass, required evidence exists, and direct comparison finds no material unresolved loss.
- **Continue:** a material gap remains and a targeted pass can credibly reduce it within scope and controls.
- **Blocked:** missing access, unsafe action, unavailable verification, incompatible outputs, or repeated non-improvement prevents a defensible result.
- **Stopped:** the user cancels or an agreed cost, time, or concurrency control is reached.

There is no arbitrary final round, but there is also no dishonest infinite loop. Stop immediately on user cancellation. Preserve partial work and report blocked or stopped rather than relabeling it a win.

## 10. Deliver

Return:

- winning or latest artifact paths;
- why it won, or why the run blocked/stopped;
- quality-gate status;
- comparisons and checks actually performed;
- unavailable checks and unresolved risks;
- progress workbench path;
- whether smoothing ran;
- final state: win, blocked, or stopped.
