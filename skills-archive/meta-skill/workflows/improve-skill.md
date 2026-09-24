# Improve Skill

1. Locate the Target - Resolve the skill directory from the prompt. If none is named, list the skills on disk and confirm which one before touching anything.
2. Grade - Read its `SKILL.md` and list every bundled file with its line count, then read `references/skill-review-rubric.md` and record a verdict per dimension. Read it — the dimensions and their pass conditions are the file's job, not something to grade from memory. This is the first move on every improve request, narrow ones included: "it never triggers" is one dimension failing, and the grade is what tells you whether it is the only one.
3. Subtract - Apply the subtraction test in `references/context-engineering-claude5.md` instruction by instruction. Cut what Claude would do unprompted; keep exact paths, formats, and opinions that are yours.
4. Redistribute - What survives but is not needed on every route moves behind a *read it when* row: output shapes to `templates/`, depth to `references/`, per-route steps to `workflows/`. State each idea in exactly one file.
5. Report - Per-dimension verdicts before and after, what was cut, what moved and where, forced line count before and after, and any dimension still failing with the reason it was left.
