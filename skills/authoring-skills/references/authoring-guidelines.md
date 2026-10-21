# Skill authoring guidelines

Authoring recommendations, not universal format laws. Portable fields, named client contracts, sources, and local release policy belong to `references/compatibility.md`. Other guidance below is a house default or heuristic; read enough of the sections needed for the decision.

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
| `name` | Portable: 1–64 characters, lowercase Unicode alphanumerics and single hyphens, matching directory name. ASCII is easiest across clients. |
| `description` | Portable: non-empty string, at most 1,024 characters. Explain capability, intent, and boundaries. |
| optional fields | Portable: license, compatibility, metadata, experimental allowed-tools. See compatibility reference for types and client extensions. |
| body | Recommendation: below 500 lines/about 5,000 instruction tokens; 150 lines is a house router heuristic, not validity. |

Use valid YAML starting at line 1 between `---` delimiters. Client leniency does not establish portable validity. Anthropic reserved-name/XML-tag restrictions and third-person preference are platform guidance, not portable laws.

## Naming

Prefer gerund form: `processing-pdfs`, `analyzing-spreadsheets`, `writing-documentation`. Noun phrases (`pdf-processing`) and imperatives (`process-pdfs`) are acceptable. Keep one pattern across a collection.

Prefer distinctive names over vague (`helper`, `utils`, `tools`) or generic (`documents`, `data`, `files`) ones. Check the selected client's reserved names separately.

## Descriptions

Clients typically advertise name/description/path before loading instructions. Availability, competing skills, explicit invocation, and client settings also affect selection; description alone never proves discovery.

- Prefer third-person capability phrasing for a consistent catalogue; alternate grammatical forms are not format errors.
- State what the skill does and when it applies, using realistic intent language and clear boundaries rather than exhaustive exact phrases.

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
| Low | Validated command/schema with explicit inputs and failure boundaries | The operation is fragile, order matters, or consistency is critical |

The narrow-bridge test: if there is one safe way across, give exact guardrails. If it is an open field, give direction and trust the model to find the route.

## Progressive disclosure

Typical client loading has three costs: advertised metadata, delivered instructions, then needed resources. Explicit invocation and client caching/compaction can change the sequence. Executed script output normally enters context without its source, but debugging/security review may need source reads.

Navigation defaults:

- Keep `SKILL.md` as a useful overview with enough routing for the task. Put non-obvious gotchas before the decisions they govern, not behind a link the agent has no reason to follow.
- State when resources help. A shared prerequisite may legitimately apply to every route; no rule requires each additional file to be conditional in every circumstance.
- Prefer direct links from `SKILL.md` and Contents for long references. Necessary deeper structure is valid with explicit navigation. Offset/limit or section reads are sufficient when they deliver the needed information; their shape alone is not a defect.
- Split domains when that reduces irrelevant context without hiding shared contracts. Confirm coverage before treating an unread resource as unnecessary.
- Use descriptive filenames (`form_validation_rules.md`, not `doc2.md`) and portable forward-slash paths.

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

For quality-critical operations, make the validation/repair loop explicit: run relevant checks, fix real failures, rerun, and proceed only when those checks pass. A script or manual rubric proves only its stated scope; static success does not establish task quality, live behavior, or authorization.

Conditional workflows guide decision points: "Creating new content? → Creation workflow. Editing? → Editing workflow."

Use plan → validate plan → execute → verify when the operation is a batch, destructive, governed by complex validation rules, or high-stakes: the plan is a structured file a script can check before anything is touched.

## Content rules

- Give mutable facts sources, versions/review dates, or runtime verification. Label historical methods; do not treat every date as an error.
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

- Fail safely. Handle expected errors with actionable diagnostics and nonzero exits; never create missing data or work around denied permissions unless that fallback is explicitly safe and authorized. Bound retries and output; scripts must run noninteractively without hidden input prompts.
- No voodoo constants. Every configuration value carries a one-line comment saying why it has that value. If the author cannot justify it, the model cannot either.
- Verbose validators. Error messages name the specific problem and the valid alternatives: "Field 'signature_date' not found. Available fields: customer_name, order_total".
- Document inputs, outputs, exits, dependencies, and side effects. Provide `--help`; keep machine-readable data on stdout, diagnostics on stderr. Use dry-run/idempotency for repeatable mutating work. State execute-versus-inspect intent; normal execution avoids source loading, while debugging/security review may require it.
- Bundle a reusable helper when deterministic/repeated work benefits from tested behavior and an explicit interface. Compare maintenance/dependency cost with saved time and output tokens; not every one-off operation needs another script.
- Declare versioned dependencies and verify the selected environment's network/package permissions. Do not generalize one hosted product's installation limits to every client. Request approval before provisioning; this skill's pinned uv/PyYAML bootstrap and offline command live in the compatibility reference.
- Name MCP tools exactly as exposed by the client, with its full qualification (for example `ServerName:tool_name` or a client-generated namespace). Do not assume a universal spelling.
- Use images or examples when they improve the task's actual quality; avoid unnecessary model calls and artifact generation.

## The subtraction test

Ask what useful information each instruction adds, then test removal against intended outcomes. Do not infer that all profiles share the strongest model's defaults. Without approved behavioral comparisons, a cut may be a reasonable scoped edit, but its quality benefit remains unproven.

| Candidate | Decide by |
| --- | --- |
| Generic ceremony or redundant prose | Whether it changes task results or prevents a real error. Keep exact contracts, costly safety boundaries, and useful rationale. |
| Worked example versus template | Whether the example improves style/edge-case handling or merely duplicates an interface. Keep compact effective examples, especially when removal worsens observed quality. |
| Repeated contract | One owner for detailed truth, with brief synchronized reminders at costly safety boundaries. Repetition is not automatically wrong. |
| Shared reference | Whether shared ownership and section reads deliver needed information efficiently. No blanket inline rule. |
| Dormant resource | Whether its condition was exercised before judging it unnecessary. No automatic deletion based on a small sample. |
| Stronger modal | Whether the error is expensive and the instruction was actually missing/unclear at the decision. Do not escalate every suggestion into MUST/NEVER. |

Use paired old/new comparisons across intended profiles for meaningful subtraction claims. Compare task success and human-reviewed quality alongside runtime time/tokens when available. A smaller static estimate alone is not a better skill, and padding unrelated assets cannot improve its verdict. Keep durable artifacts (plans, rubrics, evals) when they serve later readers.

## Eval-driven development

Define observable cases before extensive instruction expansion. Repository release policy keeps schema 1, at least three execution cases, and all three required profiles; these are not portable format rules. Static definitions do not prove that a skill worked or that cases were authored first.

Separate two questions:

- **Discovery**: was the intended metadata available, did automatic selection choose the right skill, and did negative near-misses avoid it? Explicit invocation bypasses selection. A generic `--skill` flag may register metadata rather than force a body load; check the installed client's semantics.
- **Execution**: after verified delivery, did the task satisfy every expected/forbidden behavior? Use realistic prompts, output/side-effect assertions, and primary evidence. A negative non-trigger sample is not a with-skill execution pass.

For a new skill compare no-skill/with-skill; for an improvement snapshot/digest the original **before editing** and compare old/new. Freeze versions outside active skill trees. Hold prompt, fixture, competing skill set, provider/model/thinking, tools, permissions, containment, and available sampling controls equal. A renamed copy or a differing nested-run allowance contaminates the comparison. Missing controls leave the claim unqualified.

For meaningful description tuning, a scalable starting point is about twenty realistic mixed queries, a fixed stratified train/validation split, three repetitions per query, and untouched fresh confirmation prompts. Include paraphrases, competing skills, and plausible near-misses, not obvious keyword opposites. A narrow wording repair need not pay for that campaign. Obtain model/time/spend and nested-run approval first.

Optimize on **training failures only**. Generalize the capability/intent boundary instead of appending the exact failed phrase. Validation may select among frozen versions, but its prompts/results must not enter edit prompts. Do not mutate held-out queries or recycle exposed fresh prompts as confirmation. Report positive selections/counts and false positives/counts separately, with denominators and repetitions. A one-shot sample is coverage, not reliability or statistical confidence.

Grade objective assertions from transcripts and artifacts, not a summary's success flag. Use human review for subjective quality; optional blind paired comparison reduces version-label bias. Compare task success alongside available time/token/cost data. Keep useful examples, rationale, and reusable helpers when they improve outcomes across intended profiles, even if text grows. Mark missing metrics unavailable, not zero.

Quick iteration runs only affected checks and relevant approved samples. Comprehensive **release qualification** retains every execution case under all three profiles, using exact mappings rather than profile labels alone:

| Profile | Question |
| --- | --- |
| fast/economical | Does the skill provide enough guidance without forcing the model to invent missing steps? |
| balanced/default | Is guidance clear and efficient for ordinary production use? |
| highest-reasoning | Does added context still improve quality rather than over-explain? |

The tuning reference owns capture preflight, diagnosis, primary-evidence interpretation, and mapping sidecars/baselines into existing run records. Missing approval, safe discovery isolation, or required external containment blocks live qualification. Do not infer a security sandbox from a copied workspace or permission flags.
