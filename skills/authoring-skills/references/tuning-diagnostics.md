# Tuning diagnostics

Use observed evidence to test an edit hypothesis. Static review can propose a repair; it cannot invent an observation or prove that a new description reliably triggers.

## Contents

- The loop
- Discovery and controlled comparisons
- Trigger tuning
- Capturing a run
- Evidence and records
- Navigation signals
- Symptom to edit

## The loop

1. Select review-only, targeted, or comprehensive scope. Preserve the original revision/manifest outside active discovery trees before editing; review-only makes no snapshots or writes.
2. Define representative prompts, fixture requirements, and observable outputs/side effects. New skills need no-skill baselines; improvements need old/new baselines. Include subjective quality criteria for human review.
3. With separate approval and safe preflight, observe a fresh executor that does not see the editing conversation. Do not give it failure diagnoses or hidden grading answers. Missing approval/controls means no launch and unqualified behavior.
4. Map primary evidence to a hypothesis: missing information, misleading routing, tool/config failure, bad output interface, or genuine description overlap. If evidence suggests no justified edit, report it rather than inventing one.
5. Repair the relevant cause, rerun static/focused tests, freeze the candidate revision, and retest approved prompts under identical controls. Stronger modals are appropriate for costly omissions, not a universal fix.
6. Compare task quality and available runtime costs, not navigation aesthetics alone. Keep remaining failures and blocked cells visible; add useful new scenarios without contaminating held-out data or silently increasing budget.

## Discovery and controlled comparisons

**Discovery** evaluates normal metadata-based selection. **Execution** evaluates instructions after confirmed delivery; `/skill:name`, a Skill-tool load, or injected content may bypass discovery. A successful read alone also does not establish invocation intent. Inspect actual client semantics: Pi's `--skill` registers a resource and does not by itself prove forced body injection. Do not include explicit-invocation runs in automatic-trigger rates.

Freeze the baseline and candidate with full manifests, not just matching names or SKILL.md bytes. Record exact editing and loaded roots. A same-name different manifest invalidates target evidence; a full matching copy may qualify identity but still needs recorded controls and historical snapshots.

Pair runs with identical prompt, fixture, model/provider/thinking, competing metadata, tools, permissions, containment, sampling controls where supported, timeout, and nested-run allowance. Change only skill presence (new skill) or revision (improvement). Missing/mismatched controls invalidate comparative claims. Do not rename copies to resolve collisions: that changes the experiment. Isolate discovery or mark blocked.

## Trigger tuning

Use realistic positives and negative near-misses, paraphrases, and adjacent skills. Start meaningful tuning with roughly twenty mixed queries and three repetitions, not as a tax on every repair. For this skill, keep a separate frozen discovery corpus with 12 training (6/6), 8 validation (4/4), and 6 fresh (3/3) positive/negative queries. The corpus is not schema-1 execution cases; the router identifies its file for the evaluator, not for exposing held-out details to the optimizer.

Only training failures inform edits. Generalize intent rather than paste exact failed phrases into descriptions. Validation selects among frozen versions; keep its raw prompts/results out of the editing context. Fresh queries confirm the selected version once, untouched; exposure requires new fresh prompts for another confirmation. The evaluator may hold the corpus, while the optimizer receives training details only.

Report true-positive selections over positive attempts and false-positive selections over negative attempts separately, by exact configuration and repetition count. Blocked/unknown samples stay out of pass numerators and visible in coverage denominators. Single samples are coverage evidence; small samples do not justify confidence/reliability claims. Obtain a new approved budget before repetitions or additional candidates.

## Capturing a run

Preflight **before any model call**:

- Record exact provider/model/thinking per selected profile, installed harness version, skill/fixture revisions and digests, prompt/corpus version, competing skill set, and intended automatic/explicit invocation.
- Approve aggregate spend/time, timeout per child, maximum top-level launches, and maximum nested launches. Default nested budget is zero. Approved meta-evals may reach depth two, never unbounded recursion; count inner calls in the aggregate budget and use identical allowances in paired runs.
- Demonstrate fresh context, disposable files, isolated skill discovery, and external containment separately. Restrict unapproved filesystem, shell, network, MCP, publishing, production, and installation effects outside the prompt. No bypass-permissions recommendation; flags or a copied workspace are not a universal security sandbox.
- Keep fixtures/snapshots outside active recursive skill roots, with no writable links to global installs. The runner rejects all fixture symlinks, including contained ones; unsafe output locations receive no writes, including error sidecars.

Example restricted preflight, **only after approval**, with `<base>` resolved from this skill's absolute directory:

```bash
python3 <base>/scripts/run_fresh_session.py <workdir> "<prompt>" --out <run.jsonl> \
  --harness pi --model <provider/model> --effort <thinking> --trace <skill-dir> \
  --invocation-mode automatic --allow-live --qualification --timeout <seconds> \
  --max-depth 1 --run-budget 1
```

The current runner has **no verified discovery/containment adapter** and blocks `--qualification` and either required guarantee. Do not remove restriction flags to manufacture a qualification pass. Its ordinary approved capture mode is explicitly unisolated, not a release workaround. `--in-place` is mutating and invalid for qualification. Installing an adapter or changing containment needs separate scope/approval.

Runner depth/count sentinels coordinate cooperating processes, not hostile children or arbitrary external model APIs. Approved depth two uses a shared launch ledger; a child cannot raise the inherited cap. Verify external containment too. Python/POSIX process controls are prerequisites, not cross-platform sandbox promises. Every harness exit, including success, stops remaining members of its owned process group while preserving parent exit status. Detached/escaped descendants still require external containment.

Exit 0 means **completed capture**, not assertions passed; 1 means harness/capture/trace failure; 2 means blocked preflight/startup; 3 means timed out. Preserve partial evidence. Pi recovery is judged from the latest completed response, closed automatic retries, and a subsequent non-aborted settlement. Intermediate errors may recover; exhausted/incomplete retries and unrecovered errors cannot become completed captures. A missing model, denied read, timeout, unavailable metric, or blocked preflight cannot become an observed pass.

## Evidence and records

Capture primary transcript, stderr, output artifacts/diff, and available session log. Runner writes `<run.jsonl>.summary.json` (schema 1 capture metadata), `.trace.json` when tracing succeeds, optional `.session.jsonl` for Claude, and a shared launch-budget sidecar. The summary records outcome/childExit/reason, requested and available observed model configuration, invocation intent, exact target manifest, workspace/depth/budget, and limitations. Never persist credential/config values merely to reproduce a run.

Run `python3 <base>/scripts/trace_skill_use.py <skill-dir> <transcript> --json` on saved evidence. Trace correlates tool IDs/results, distinguishes reads/writes/edits/executes/loads, and records requested ranges and outcomes. `fired=true` proves observed delivery of matching target content or a confirmed load, not automatic discovery or task quality. `false` requires sufficient supported evidence; malformed/incomplete/opaque evidence can be `null`. Mechanisms include read, skill-tool, injected, none, unknown. Malformed or unsupported event types retain uncertainty instead of being discarded as negative evidence. Capture inspection and standalone trace share Pi activity boundaries: later work/retry records require a fresh settlement; metadata-only records do not. A previously confirmed delivery remains confirmed with an incompleteness warning when later work is unfinished. Text mentions and codemode source are not execution proof; consume actual nested events only when visible.

Negative evidence uses supported non-loading semantics, not a permissive fallback. Every shell command remains unknown, including metadata-looking commands: their options or wrappers can read content. Supported filename/count-only search can remain negative; content/unsupported search modes remain unknown. Script-run records identify only supported literal program operands, not every file argument; they do not prove non-loading. Explicit malformed status values remain unknown, never coerced to success/failure.

Runner retains raw `streamTrace` and optional `sessionTrace`. Effective `trace` and its sidecar use confirmed matching delivery when either source proves it, with `evidenceSource` and `evidencePath` identifying the selected source. Steps/counts belong to that source, not a merged timeline. Identity conflicts or a target revision change in either source fail capture before selection. Explicit-injection fallback changes only effective evidence, not the raw reports. Unreadable target manifests fail analysis; unreadable candidate identities remain unknown, never partial matches.

A partial read is not automatically insufficient. Successful delivery does not by itself prove the needed section was read or understood; assess outputs and information requirements. A matching manifest reflects files at analysis time, so preserve revision snapshots before allowing edits. Supplemental session evidence may reveal loads absent from streams; absent explicit-load evidence is unknown, not a negative discovery result.

The capture summary is **not** a behavioral run record. Follow `<repo>/evals/README.md`; save one schema-conforming execution record per case/profile at `<repo>/evals/runs/<case-id>/<profile>.json`. Use existing `evidence`, assertion evidence, `notes`, and `toolConfiguration` to link unique baseline/candidate artifacts, invocation mode, harness version, controls, approvals, and budgets. Preserve historical evidence rather than relabeling it for a new revision. Do not add fields to the shared schema.

Grade every expected/forbidden behavior from primary evidence. Use `pass`, `fail`, or `blocked` for run-record assertions; missing evidence is blocked. A negative discovery non-trigger is separate from with-skill execution outcomes. Omit unavailable numeric metrics and state `unavailable` in notes, never zero. Human-review subjective outputs; optional blind paired comparison must itself be approved if it uses models. Keep discovery positive/negative counts separate from execution passes.

## Navigation signals

| Signal | Investigate | Possible response |
| --- | --- | --- |
| Unexpected read order | Was required information missing before its decision? | Improve routing/order only if the task evidence shows a problem. |
| Condition held but needed reference not delivered | Was the reference essential and clearly signaled? | Put its section link at the dependent step. |
| Shared reference read on every route | Is it useful shared context, or just a small common fragment? | Keep shared ownership when justified; inline only the routinely needed fragment if that helps. |
| Resource never read | Did the sample exercise its condition? | Expand coverage or improve routing; do not delete dormant conditional resources by default. |
| offset/limit, head, sed, or selective sections | Did the delivered ranges cover essential information? | Accept sufficient section reads; add Contents/direct routing when essential content was missed. |

## Symptom to edit

These are hypotheses, not a mandatory one-symptom/one-edit lookup. Validate the cause first. Dim. refers to stable rubric IDs.

| Symptom | Check before editing | Repair hypothesis | Dim. |
| --- | --- | --- | --- |
| Never fires | Metadata availability, client settings, collisions, invocation mode, realistic positives | Clarify capability/intent boundaries using training evidence, not exact-phrase insertion. | 1 |
| Fires on near-misses | Competing skills and false-positive counts | Narrow scope/boundaries without sacrificing true positives. | 1, 7 |
| Rule present but ignored | Was the relevant information delivered before the decision? | Move the gotcha or clarify the step; strengthen modal only for costly mistakes. | 3, 14 |
| Partial/unexpected reads | Essential information and task success, not read-window shape | Improve navigation only when missing information affected behavior. | 2, 6 |
| Shared or unread file | Shared value and conditional coverage | Keep, split, or re-signal based on evidence; no automatic inline/delete rule. | 2, 5, 6 |
| Strong model succeeds, fast model fails | Missing interface/step vs model/tool limitation | Add useful guidance and retest relevant profiles under equal controls. | 9, 14 |
| Options cause inconsistent output | Legitimate variability vs ambiguity | Prefer one default with documented escape conditions where useful. | 9 |
| Validation skipped | Was it required, executable, and within scope? | Make a fragile operation's validation/repair loop explicit. | 3 |
| Batch/destructive errors | Approval, plan, dry-run, external containment | Validate a structured plan before mutation; never bypass a denied operation. | 3, 11 |
| Script/tool failure | Interface, versioned dependencies, actual tool names, exits | Improve safe errors/helper tests; inspect source when debugging/security-reviewing. | 11 |
| Output quality varies | Objective assertions and human comparison | Add a verifiable template or useful input/output example. | 9 |
| Retest unchanged | Exact loaded path/manifest, baseline controls | Resolve discovery collisions/isolation; do not rename or claim the wrong copy passed. | 14 |
