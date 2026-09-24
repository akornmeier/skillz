# Context engineering for Claude 5-generation models

Source: [The new rules of context engineering for Claude 5 generation models](https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models) — applies to Claude 5-generation models (Opus 5, Fable 5, Sonnet 5), for which Anthropic removed over 80% of Claude Code's system prompt with no measurable loss on coding evals.

The argument is subtraction. Below is what that subtraction looks like inside a `SKILL.md`.

## The six pairs

| Then → now | What changed | What it means for your SKILL.md |
| --- | --- | --- |
| Rules → judgment | Old prompts fenced the model in ("never write multi-paragraph docstrings"); new ones state intent ("write code that reads like the surrounding code"). | Keep only rules that cannot be derived from the files themselves: paths, naming contracts, output formats, opinions that are yours rather than the model's default. Cut anything restating general engineering competence. |
| Examples → interface design | Examples narrow the exploration space; an expressive interface hints at correct use without one. | Replace worked examples with a template, a routing table, or a skeleton to fill in. Shape teaches; a walked-through trajectory pins the model to one path. |
| Upfront → progressive disclosure | The model loads what it needs when it needs it, so frontloaded context is paid on every trigger whether used or not. | `SKILL.md` is the only file loaded on every trigger. Everything else carries a *read it when* condition. Never write "read these files first". |
| Repetition → single source of truth | Instructions duplicated across system prompt and tool definitions forced the model to reconcile versions of one idea. | State each idea in exactly one file. Where a workflow and a reference overlap, the reference owns the idea and the workflow links to it. |
| Manual memory → auto-memory | Hand-maintained CLAUDE.md memory is giving way to memory the model captures itself. | Don't build note-keeping procedure into a skill. Durable artifacts a human or a later agent reads off disk — plans, rubrics, evals — are a different mechanism and stay. |
| Simple specs → rich references | Markdown prose is the weakest reference format; HTML mockups, code, test suites, and rubrics carry more per token. | Ship the artifact, not a description of it: a `templates/` file over a described structure, a gradeable rubric over "make sure it's good". |

## Where context belongs

- **System prompt** — product-level context defining the environment and purpose. You don't write it.
- **CLAUDE.md** — a lightweight description of what the repo is, weighted toward gotchas rather than patterns Claude can read off the code. When a section grows procedural, it wants to be a skill.
- **Skill** — a lightweight, opinion-driven guide that lets Claude pull information when it needs it. It encodes team-specific opinions, knowledge, and practice. It is not a rulebook: over-constrain only where a wrong call is expensive (destructive operations, an external contract, security). Long skills split across files rather than growing.
- **References** — depth for the task at hand, pulled in by link or `@` mention. Prefer the artifact over prose about the artifact: an HTML mockup of a design beats a description of it.

## The subtraction test

Run this on your own draft, instruction by instruction: **would Claude 5 do this unprompted?** If yes, cut it.

Cuts this repo has already found and made:

- `ultrathink` / "think hard" / "think step by step" directives.
- "Consider edge cases and error handling", "include code examples where appropriate", "be thorough".
- Shell commands that confirm a file exists or that YAML parses (`ls -la`, `head -10`).
- `chmod +x` after writing a script; `git add` / `commit` / `push` after finishing work.
- Worked examples that walk one imaginary task end to end.
- "Required reading" prologues that load documentation before the task is known.

What survives the test, despite looking like a rule:

- A command whose exit status is observable, inside a loop that repeats until it passes. Validator loops are endorsed; "double-check your work" is not.
- Exact paths, filenames, and output formats.
- An opinion that is yours. The model has defaults; it does not have your team's.

## Verification

Rubrics let Claude verify taste in a domain — what a good API design looks like — and can be handed to verifier agents spun up for the purpose. That is why gradeable criteria live in `skill-review-rubric.md` rather than as an inline "test the skill" step.

`claude doctor` rightsizes skills and CLAUDE.md files automatically; run it after a rewrite.
