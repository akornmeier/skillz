---
name: mental-model
description: Maintains concise YAML expertise files containing durable architecture decisions, recurring patterns, and unresolved questions. Use when asked to read, update, validate, trim, or consolidate a project mental model.
compatibility: Requires file read and write access. The bundled validator requires Node.js and the yaml package; install the skill-local dependency only with approval if it is unavailable.
metadata:
  category: knowledge-maintenance
---

# Mental Model Maintenance

Maintain durable project knowledge in a designated YAML expertise file. Do not load or update a mental model for unrelated tasks merely because the skill is available.

## Locate the file and limit

Use, in order:

1. The expertise path and `max-lines` value provided by the active agent context.
2. A path and limit supplied by the user.

If neither identifies a target file, ask for the path. Do not search for arbitrary YAML files or create a new mental model by assumption. If no line limit is defined, preserve the current size unless the user asks for consolidation.

## What to retain

Record information likely to help future work:

- architecture and stable data flows;
- project conventions and recurring implementation patterns;
- decisions with concise rationale;
- verified pitfalls and durable operational constraints;
- unresolved technical questions.

Reference source files by path instead of copying them. Exclude conversation logs, raw build output, temporary status, secrets, credentials, personal assessments, and claims that have not been verified. Store information about people or team performance only under an explicit project policy and user request.

Use the existing YAML structure when one exists. Otherwise prefer small, descriptive mappings and lists; do not impose a universal schema.

## Update workflow

1. Read the complete target file immediately before editing.
2. Identify the smallest durable addition, correction, consolidation, or removal.
3. Update stale entries rather than appending contradictions.
4. Preserve unrelated content and comments where practical.
5. Validate the result and enforce the declared line limit:

   ```bash
   node <skill-directory>/scripts/validate-yaml.mjs <expertise-file> --max-lines <limit>
   ```

   Omit `--max-lines` when no limit is defined.
6. If validation or the line check fails, repair the file and rerun the command. Do not finish until it passes.

## Validator dependency

Run the validator preflight before the first edit:

```bash
node <skill-directory>/scripts/validate-yaml.mjs --help
```

If Node.js or the `yaml` package is unavailable, report the missing dependency. With approval, install the isolated skill dependency without modifying the consuming project:

```bash
npm install --prefix <skill-directory> --ignore-scripts
```

Then rerun the validator. Do not silently install dependencies.
