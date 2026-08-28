# Build Plan

Task markers: `[]` idle · `[wip]` in progress · `[x]` complete · `[f]` failed.

1. **Resolve and validate the plan.** Infer the target only when unambiguous; otherwise ask. Run `validate_plan.py` before executing work and stop on structural failures.
2. **Select the range.** Build all unfinished phases unless the request sets a next-N limit. A limit is a stopping boundary, not permission to skip dependencies.
3. **Absorb context.** Read the full plan, its local figures, metadata, and depth-one back references.
4. **Execute phases in order.** For each selected phase:
   - mark the phase and current task `[wip]`;
   - implement each action;
   - run the phase's testing commands;
   - repair failures and rerun until they pass or mark the blocked task `[f]` with evidence;
   - mark successful tasks `[x]` before starting the next phase.
5. **Use parallel lanes only when safe.** Tasks must be independent, have exclusive file ownership, and run in isolated workspaces. One integrator is the sole plan writer and validates merged results. Use one lane whenever independence is uncertain.
6. **Run global validation.** For a bounded run, execute every currently applicable global command and identify checks deferred to later phases.
7. **Update plan history.** Append modified timestamp, agent/session identity, relevant commit SHAs, and final task states. Preserve a pre-update snapshot.
8. **Revalidate the plan.** Run `validate_plan.py <plan> --previous <snapshot>`, repair structural failures, and remove the snapshot.
9. **Report.** Summarize each selected phase, commands run, final task states, deferred work, and `[f]` failures.
