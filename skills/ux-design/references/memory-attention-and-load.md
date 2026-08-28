# Memory, attention, and load

Use these principles when an interface asks users to hold, compare, scan, or recall information. Cognitive capacity varies with expertise, stress, disability, interruption, language, and environment; do not design to a mythical average user.

## Chunking

**Principle.** Grouping individual information units into meaningful structures can make content easier to scan, understand, and remember.

**Use when:** presenting long forms, dense settings, identifiers, instructions, navigation, or multi-part content.

**Design moves:** group by user goal; give each group a descriptive heading; use consistent formatting and manageable progressive disclosure; preserve the whole context while revealing detail.

**Failure modes:** arbitrary chunks based only on visual symmetry; too many nested groups; splitting a task across screens so users lose comparison context.

**Validate:** scan tests, findability tasks, comprehension questions, and return-to-task testing after interruption.

Source: https://lawsofux.com/chunking/

## Cognitive Load

**Principle.** Understanding and operating an interface consumes limited mental resources. Some effort is inherent to the task; avoid effort introduced by presentation, memory demands, ambiguity, or unnecessary decisions.

**Use when:** users hesitate, repeatedly reread, miss details, abandon, make sequence errors, or describe a flow as overwhelming.

**Design moves:** remove irrelevant content; externalize state and constraints; use plain language; keep controls near affected content; disclose advanced detail when needed; provide safe defaults and examples without removing agency.

**Failure modes:** equating fewer pixels with lower load; hiding essential comparison data; moving complexity to help documentation, support staff, or later steps; measuring only completion time.

**Validate:** error patterns, pauses, backtracking, help usage, subjective effort collected after tasks, and performance under realistic interruption.

Source: https://lawsofux.com/cognitive-load/

## Miller’s Law

**Principle.** Immediate-memory capacity is limited, but “seven plus or minus two” is a historical finding—not a universal count for navigation, steps, or options.

**Use when:** a task requires retaining unfamiliar items or sequences without external support.

**Design moves:** reduce recall demands, create meaningful chunks, keep instructions and references visible, and let users recognize rather than reproduce information.

**Failure modes:** enforcing seven menu items; confusing perception with memory; ignoring expertise and context; deleting useful choices solely to hit a number.

**Validate:** test the actual task with representative users and interruptions; measure omissions, order errors, and repeated lookups.

Source: https://lawsofux.com/millers-law/

## Serial Position Effect

**Principle.** In a sequence, early and late items can be recalled more reliably than middle items, although task relevance and presentation often matter more.

**Use when:** ordering navigation, onboarding steps, instructions, lists, or summaries.

**Design moves:** place high-priority information at natural entry or completion points; repeat truly critical guidance at the moment of use; use hierarchy rather than order alone.

**Failure modes:** assuming left/right placement works identically across writing directions and responsive layouts; burying routine but necessary actions; manipulating memory to privilege a sponsored choice.

**Validate:** recall and findability after a delay, across screen sizes, reading directions, and keyboard traversal order.

Source: https://lawsofux.com/serial-position-effect/

## Working Memory

**Principle.** People can temporarily hold and manipulate only a small amount of new information, and that information decays or is displaced easily.

**Use when:** users compare plans, transfer codes, configure across steps, calculate mentally, or resume interrupted work.

**Design moves:** carry prior selections forward; show summaries and comparison tables; preserve entered values; expose constraints beside controls; support copy/paste and review; save progress where appropriate.

**Failure modes:** asking users to memorize values from another screen; clearing data after validation errors; replacing labels with unfamiliar icons; hiding previous choices during review.

**Validate:** complete tasks after a realistic interruption; test comparison accuracy, resumption, error recovery, and whether users reopen earlier screens.

Source: https://lawsofux.com/working-memory/

## Combined checks

- What must the user remember, and can the system display or preserve it instead?
- Is grouping based on the user’s task and vocabulary?
- Is intrinsic domain complexity distinguished from avoidable interface complexity?
- Can users compare alternatives without serially opening and memorizing them?
- Does the design survive interruption, validation failure, refresh, and back navigation?
