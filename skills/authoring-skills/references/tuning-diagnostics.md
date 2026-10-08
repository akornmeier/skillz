# Tuning diagnostics

How to improve a skill from watching a fresh instance use it, rather than from reading it. Every symptom maps to one edit; a symptom with no row below is reported, not fixed.

## Contents

- The loop
- Capturing a run
- Navigation signals
- Symptom to edit
- Report shape

## The loop

Two instances. Claude A edits the skill with the human. Claude B is a fresh session that uses it on real work and never sees the editing conversation.

1. Use the skill through B in a real workflow, not a test scenario: a prompt a user would type, in a workspace shaped like theirs.
2. Observe where B struggles, succeeds, or chooses unexpectedly: a rule it ignores, a file it opens at the wrong moment, a tool it cannot find, an output in the wrong shape.
3. Bring the specific observation back to A together with the current `SKILL.md`: "B forgot to filter test accounts on the regional report; the rule is there but not prominent."
4. Apply the edit: reorganise so the rule sits where it applies, strengthen the modal (must, never, only), or restructure the workflow so the step cannot be skipped.
5. Test again on the same prompt in a new fresh session and compare the two traces.
6. Repeat as new scenarios appear; each one becomes an eval case.

This works because B shows what the text actually causes, not what the author meant it to cause, and A sees both at once.

## Capturing a run

One fresh session per profile in the skill's `requiredProfiles`, under the run contract in `<repo>/evals/README.md`: the skill is discoverable and not force-loaded, the workspace is disposable, side effects are blocked. Save the transcript, then run the trace script against the skill directory:

```bash
claude -p "<prompt>" --output-format stream-json --verbose > run.jsonl
python3 <base>/scripts/trace_skill_use.py <skill-dir> run.jsonl
```

Run that as one plain command: a `cd` or an environment-variable prefix in front of it makes the non-interactive permission check refuse the whole line, so set the working directory in the step before and pass fixture paths in the prompt.

Under Pi, `pi --no-session --mode json -p "<prompt>" > run.jsonl` gives the equivalent event stream and the trace script detects it. A plain `pi -p` transcript also works, through the text fallback, where read order and partiality are approximate.

The trace prints four facts: whether the skill fired and at which step, every bundled file read in order with partial reads marked, the bundled files never opened, and the format it parsed. Judgment supplies the fifth: whether the files read were the right ones for the task.

When no fresh session can be run (no CLI, no budget, no model for the profile), write `observation skipped: <reason>` in the report and grade rubric dimension 14 as failing with that reason. Never infer navigation from reading the skill yourself.

## Navigation signals

| Signal | Means | Edit |
| --- | --- | --- |
| Files read in an unexpected order | The structure is not intuitive; the router does not say what comes first | Name each file at the step that needs it, in the order the steps run |
| A reference never followed although its condition held | The link or its read-it-when condition is not prominent | Move the condition into the step that depends on it; name the section, not just the file |
| The same file read on every run | Its content belongs in `SKILL.md` | Inline the part every route needs; leave the rest behind its condition |
| A file never read across all runs | It is unnecessary, or its condition never matches a real prompt | Delete it, or rewrite its condition in the words of the prompts that should open it |
| A partial read (`head`, `tail`, `sed -n`, `offset`, `limit`) | The file is long or reached through another file, so the instance rationed its read | Add a `## Contents` list, link it directly from `SKILL.md`, or split it by domain |

## Symptom to edit

Dim. is the rubric dimension that fails; the doc pattern behind each edit is named so the fix can be checked against it.

| Symptom | Likely cause | Edit | Dim. |
| --- | --- | --- | --- |
| Never fires on prompts that should trigger it | Description lacks the phrases users type, or is not third person | Add the user's exact phrases to the "Use when" clause, third person throughout (description phrases) | 1 |
| Fires on prompts it should not | Description overlaps a neighbouring skill or names only a vague capability | Add a boundary clause ("Not for …") and sharpen the what-half (boundary clause) | 1 |
| Rule present but ignored | Buried below the step it governs, or phrased as a suggestion | Move it into the step; strengthen the modal to must, never, or only (prominence or stronger modal) | 14 |
| Files read in unexpected order | Router names files but not when | Name each file at its step, in step order (progressive disclosure) | 3 |
| Reference never followed | Read condition not prominent, or stated far from the step | Put the condition inside the step and name the section (prominence) | 3 |
| Same reference read every run | Content every route needs sits behind a condition | Inline that part into `SKILL.md`; keep depth behind the condition (inline) | 2 |
| Bundled file never read | Unnecessary, or its condition never matches a real prompt | Delete it, or re-signal with the prompts' own words (delete or re-signal) | 6 |
| Partial reads | Long or nested file | Add `## Contents`, flatten to one level from `SKILL.md`, or split by domain (flatten or add Contents) | 6 |
| Works on the strongest profile, fails on the fast one | Too little guidance; the strong model infers a step the fast one skips | Write the inferred step out; lower the degree of freedom at that step (more guidance for the fast profile) | 14 |
| Picks inconsistently among listed options | A menu of equivalent choices | One default plus the condition for the alternative (default plus escape hatch) | 9 |
| Skips a validation step | The step is advisory and nothing loops on it | Run validator, fix, rerun, "only proceed when it passes" (validator loop) | 3 |
| Errors in a batch or destructive step | No plan checked before anything is touched | Plan as a structured file, validate it with a script, then execute and verify (plan-validate-execute) | 3 |
| A script fails and the instance improvises | The script defers its error cases to the model | Handle the case in the script; errors name the specific problem and the valid alternatives (solve, don't defer) | 11 |
| "tool not found" on an MCP tool | Bare tool name with several servers present | Fully qualify as `Server:tool` (qualified MCP names) | 11 |
| Output shape varies between runs | No template, or a flexible one where strict was needed | Ship the shape as a template marked "ALWAYS use this exact structure" (strict template) | 9 |
| Output style is off | Style only visible by example | Add input/output pairs showing the style (input/output pairs) | 9 |

## Report shape

One row per observed symptom, placed before the before/after numbers the Improve route already reports:

| Symptom | Evidence | Edit applied | Retest |
| --- | --- | --- | --- |
| Reference never followed: rubric not opened | trace step 7: reads `workflows/improve-skill.md`, never `references/review-rubric.md` | Grade step now says "read `references/review-rubric.md`" before "record a verdict" | Second run opens the rubric at step 4 |

Evidence is a trace line or a transcript excerpt, never a paraphrase. A row whose Retest column is empty means the edit is unproven, and the report says so.
