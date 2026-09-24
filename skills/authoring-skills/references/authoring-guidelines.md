# Skill authoring guidelines

Condensed from Anthropic's skill authoring best practices. Every rule below is a constraint, a number, a pattern, or a stated opinion. Read only the section the decision at hand needs.

## Contents

- Frontmatter constraints
- Naming
- Descriptions
- Degrees of freedom
- Progressive disclosure
- Workflows and feedback loops
- Content rules
- Scripts
- The subtraction test
- Eval-driven development

## Frontmatter constraints

| Field | Rule |
| --- | --- |
| `name` | 1–64 chars, lowercase letters, digits, single hyphens. No XML tags. Cannot contain "anthropic" or "claude". Must equal the directory name. |
| `description` | 1–1024 chars, non-empty, no XML tags. States what the skill does and when to use it. |
| body | Under 500 lines. Split into bundled files before approaching the limit. |

A file whose first line is not `---` has no frontmatter and never loads.

## Naming

Prefer gerund form: `processing-pdfs`, `analyzing-spreadsheets`, `writing-documentation`. Noun phrases (`pdf-processing`) and imperatives (`process-pdfs`) are acceptable. Keep one pattern across a collection.

Avoid vague (`helper`, `utils`, `tools`), generic (`documents`, `data`, `files`), and reserved-word names.

## Descriptions

The description is the only part of a skill in context on every session, so it alone decides whether the skill fires. It is chosen from among potentially a hundred others.

- Third person, always. The description is injected into the system prompt, and a change of point of view breaks discovery.
- Both halves: what the skill does, then when to use it, with the key terms a user actually types.

Good:

```yaml
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```

Avoid:

```yaml
description: I can help you process Excel files
description: Helps with documents
description: Use when creating new skills
```

The first is first person, the second names no trigger, the third names no capability.

## Degrees of freedom

Match specificity to how fragile the task is.

| Freedom | Shape | Use when |
| --- | --- | --- |
| High | Prose steps and heuristics | Several approaches are valid and context decides |
| Medium | A template or parameterised pseudocode | A preferred pattern exists and some variation is fine |
| Low | One exact command, no parameters | The operation is fragile, order matters, or consistency is critical |

The narrow-bridge test: if there is one safe way across, give exact guardrails. If it is an open field, give direction and trust the model to find the route.

## Progressive disclosure

Three tiers, each paid at a different moment:

1. `name` and `description` — always in context.
2. `SKILL.md` body — loaded when the description matches.
3. Bundled files — loaded only when an instruction points at one, scripts executed without being read.

Rules:

- `SKILL.md` is an overview that points at depth, like a table of contents. It is the only file paid on every trigger.
- Every bundled path carries a stated condition for opening it. Never demand a file be opened before the task is known.
- One level deep. Every reference file links directly from `SKILL.md`. A file that is reached only through another reference gets partially read (`head -100`) and the model works from incomplete information.
- Reference files over 100 lines open with a `## Contents` list of their sections, so a partial read still shows the full scope.
- Organise by domain when a skill has several: one reference per domain, so a sales question never loads the finance schema.
- Name files for their content (`form_validation_rules.md`, not `doc2.md`). Forward slashes only.

Patterns:

- High-level guide with references: quick start in `SKILL.md`, "for X see `FILE.md`" links for the rest.
- Domain-specific organisation: `SKILL.md` is a navigation table, one reference file per domain.
- Conditional details: basic content inline, advanced content behind "for tracked changes, see …".
- Workflows in files: when a route's steps grow past a screen, move them to `workflows/<route>.md` and route from a table in `SKILL.md`.

## Workflows and feedback loops

Complex operations are sequential, numbered steps. For long ones, ship a checklist the model copies into its response and ticks off:

```
- [ ] Step 1: Analyze the form (run analyze_form.py)
- [ ] Step 2: Create field mapping (edit fields.json)
- [ ] Step 3: Validate mapping (run validate_fields.py)
- [ ] Step 4: Fill the form (run fill_form.py)
```

The validator loop is the single most effective pattern: run validator → fix errors → repeat → proceed only when it passes. The validator may be a script (exit code) or a reference document the model checks against (a style guide, a rubric). Make the loop explicit: "If validation fails, fix and run again. Only proceed when it passes."

Conditional workflows guide decision points: "Creating new content? → Creation workflow. Editing? → Editing workflow."

For batch, destructive, or high-stakes operations, use plan → validate plan → execute → verify, with the plan as a structured file a script can check before anything is touched.

## Content rules

- No time-bound facts. "Before August 2025 use the old API" becomes wrong on a date. State the current method; put the old one under an "Old patterns" `<details>` block.
- One term per concept, throughout. Not "API endpoint" here and "URL" there; not "field" here and "box" there.
- One default with an escape hatch, not a menu. "Use pdfplumber. For scanned PDFs needing OCR, use pdf2image with pytesseract" beats a list of five libraries.
- Templates for output shape. Strict: "ALWAYS use this exact structure". Flexible: "a sensible default; adjust to the analysis".
- Input/output example pairs where output quality depends on seeing the style, as in regular prompting.
- Concise is key. The model is already very smart; add only what it does not have. Per paragraph: does this justify its token cost?

Concise (≈50 tokens):

```markdown
### Extract PDF text
Use pdfplumber:
    with pdfplumber.open("file.pdf") as pdf:
        text = pdf.pages[0].extract_text()
```

Verbose (≈150 tokens): "PDF (Portable Document Format) files are a common file format that contains text, images… there are many libraries available… pdfplumber is recommended because…". The model knows what a PDF is.

## Scripts

- Solve, don't defer. A script handles its own error conditions (file missing → create the default; permission denied → use a fallback) rather than failing and leaving the model to guess.
- No voodoo constants. Every configuration value carries a one-line comment saying why it has that value. If the author cannot justify it, the model cannot either.
- Verbose validators. Error messages name the specific problem and the valid alternatives: "Field 'signature_date' not found. Available fields: customer_name, order_total".
- State intent for every script reference. "Run `analyze_form.py` to extract fields" means execute; "See `analyze_form.py` for the extraction algorithm" means read. Execution is preferred: only the output costs tokens.
- Prefer a bundled script to generated code for anything deterministic. It is more reliable, cheaper, and consistent across uses.
- List required packages and verify they are available where the skill will run. Claude API code execution has no network and no package installation.
- MCP tools are always fully qualified: `ServerName:tool_name`. A bare tool name fails when several servers are present.
- When inputs can be rendered as images, render them and let the model look.

## The subtraction test

Run this on every instruction in a draft: **would the model do this unprompted?** If yes, cut it. Anthropic removed most of Claude Code's system prompt for Claude 5-generation models with no measurable loss; a skill is a lightweight, opinion-driven guide, not a rulebook.

| Then → now | What it means for a skill |
| --- | --- |
| Rules → judgment | Keep only rules the model cannot derive from the files: paths, naming contracts, output formats, opinions that are the author's rather than the model's default. Cut anything restating general competence. |
| Examples → interface design | A template, routing table, or skeleton to fill in beats a worked example. Shape teaches; a walked-through trajectory pins the model to one path. |
| Upfront → progressive disclosure | `SKILL.md` is the only file paid on every trigger. Everything else carries a "read it when". |
| Repetition → single source of truth | Each idea lives in exactly one file. Where a workflow and a reference overlap, the reference owns it and the workflow links. |
| Manual memory → auto-memory | Do not build note-keeping procedure into a skill. Durable artifacts a later reader needs (plans, rubrics, evals) are a different mechanism and stay. |
| Simple specs → rich references | Ship the artifact, not prose about it: a template over a described structure, a gradeable rubric over "make sure it is good". |

Cuts that always survive review: "think step by step", "consider edge cases", "be thorough", "where appropriate", commands that only confirm a file exists, `chmod +x` after writing a script, `git add`/`commit` after finishing, mandatory-reading prologues, worked examples that walk one imaginary task end to end.

What survives the test despite looking like a rule: a command whose exit status is observable inside a loop that repeats until it passes; exact paths, filenames, and output formats; an opinion that is the author's. The model has defaults; it does not have the team's.

Over-constrain only where a wrong call is expensive: destructive operations, an external contract, security.

## Eval-driven development

Build evaluations before writing extensive documentation, so the skill solves observed problems rather than imagined ones.

1. Identify gaps: run the model on representative tasks without the skill and note the specific failures.
2. Write three cases that test those gaps, in the case shape of `templates/evals.json`:

```json
{
  "id": "pdf-processing-extract-text",
  "summary": "Extracts every page's text to a file.",
  "setup": "Use a disposable workspace containing test-files/document.pdf.",
  "prompt": "Extract all text from this PDF file and save it to output.txt",
  "expectedBehavior": [
    "Reads the PDF using an appropriate library or command-line tool.",
    "Extracts text from every page.",
    "Saves the text to output.txt in a readable format."
  ],
  "forbiddenBehavior": [
    "Skips pages it cannot parse without saying so.",
    "Writes anywhere other than output.txt."
  ]
}
```

3. Establish the baseline: performance without the skill.
4. Write the minimum instructions that pass the cases.
5. Run the evaluations, compare against the baseline, refine. There is no built-in runner; the cases are the source of truth, run by hand in fresh sessions.

The Claude A / Claude B loop: one instance (A) authors and refines the skill with the human; a fresh instance (B) uses it on real tasks. Observe B and bring specifics back to A: "B forgot to filter test accounts on the regional report; the rule is there but not prominent." A reorganises, B is tested again.

Watch how B navigates: files read in an unexpected order mean the structure is not intuitive; a reference never followed means the link is not prominent; a file read on every run belongs in `SKILL.md`; a file never read is unnecessary or badly signalled.

Test with every model the skill will run on. Haiku needs more guidance, Opus needs less explanation; instructions should work for all of them.
