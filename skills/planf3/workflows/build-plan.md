# Build Plan

Task markers: `[]` idle · `[wip]` in progress · `[x]` complete · `[f]` failed.

1. **Resolve, validate, and snapshot the plan.** Infer the target only when unambiguous; otherwise ask. Run `validate_plan.py` before executing work and stop on structural failures or unresolved build blockers. Preserve a temporary pre-edit snapshot before changing any task states or evidence.
2. **Select the range.** Build all unfinished phases unless the request sets a next-N limit. A limit is a stopping boundary, not permission to skip dependencies.
3. **Absorb context.** Read the full plan, its local figures, metadata, and depth-one back references.
4. **Execute phases in order.** For each selected phase:
   - mark the phase and current task `[wip]`;
   - implement each action as **Implementing a task** below describes, and run the task's verification cases and commands;
   - append actual evidence in each verification's evidence field: command/procedure, exit status where applicable, observed assertions/results, and any retained output path; leave unexecuted checks `Not run` with a reason;
   - compare observed results with expected outcomes, repair failures, and rerun; mark blocked tasks `[f]` with evidence and do not start dependent work;
   - mark a task `[x]` only after all its verification passes; run the phase's integration checks and mark the phase `[x]` only when all tasks and integration checks pass, before advancing to dependent phases;
   - if the plan must change, record what changed and why in Amendments, preserve criterion IDs and coverage, and update affected interfaces, consumers, and verification together. Do not weaken acceptance criteria to fit the implementation; ask before changing required behavior. Read `references/engineering-review.md`, repair and recheck affected gates, and rerun structural validation before continuing. Mark superseded evidence stale, reset affected completion markers, and rerun affected checks before marking them complete again.
5. **Use parallel lanes only when safe.** Tasks must be independent, have exclusive file ownership, and run in isolated workspaces. One integrator is the sole plan writer and validates merged results. Use one lane whenever independence is uncertain.
6. **Run global validation.** For a bounded run, execute every currently applicable global command and identify checks deferred to later phases.
7. **Update plan history.** Append modified timestamp, agent/session identity, relevant commit SHAs, and final task states. Record deviations and their coverage impact; keep the snapshot from step 1 until final validation passes.
8. **Revalidate the plan.** Run `validate_plan.py <plan> --previous <snapshot>`, repair structural failures, and remove the snapshot.
9. **Report.** Summarize each selected phase, commands and observed results, final task states, deviations and affected criteria, deferred work, and `[f]` failures. A structurally valid plan is not proof that acceptance criteria passed.

## Implementing a task

The plan's tasks and acceptance criteria are the request. Skipping a planned action, adding unplanned behavior, or editing outside the task's files or lane is a plan change: record it in Amendments as step 4 requires.

Take the first option that fully works: reuse a helper, component or pattern already in this codebase the way surrounding code does; else the standard library or a platform feature (a house component beats a native widget); else an installed dependency (never add one for a few lines); else the minimum code that works.

- Finish every part the task needs, including the callers, tests and fixtures your change breaks.
- No abstraction, wrapper, type conversion, option, config or "for later" code the plan does not call for. Keep values in the form the platform gives you and the codebase's existing layers, interfaces and conventions. Deletion beats addition.
- The shortest working diff wins once you know everything it must touch; a one-liner that needs decoding is not short. Between options of equal size, take the one correct on edge cases.
- Comment only the why the code cannot show, in one line. A shortcut with a known limit gets `shortcut: <the limit>, <when to upgrade>`.
- Bug fix: grep every caller of the function you touch, then fix the root cause once in the shared code; if that code is outside the task's files or lane, amend the plan first.
- Code you move or merge keeps its error handling and validation.
- The task's verification is the floor, never optional. New non-trivial logic (a branch, loop, parser, money or security) also gets a small test or assert-based self-check.

Never cut validation at trust boundaries, error handling that prevents data loss, security, accessibility, or anything the plan or user requires.
