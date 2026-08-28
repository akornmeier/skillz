# Optional Higgsfield workflow

Higgsfield is an optional paid external service. Use it only after the user explicitly requests or approves it. Local SVG/HTML remains the default.

CLI capabilities and flags can change. Inspect the installed CLI's help instead of guessing syntax.

## Contents

- [Approval gate](#approval-gate)
- [Inspect safely](#inspect-safely)
- [Estimate before spending](#estimate-before-spending)
- [Generate only the approved layer](#generate-only-the-approved-layer)
- [Recommended infographic pattern](#recommended-infographic-pattern)
- [Failure handling](#failure-handling)

## Approval gate

Before any upload or generation, confirm:

- the user wants Higgsfield for this artifact;
- supplied data/assets are allowed to leave the local environment;
- no secrets, personal data, unreleased results, or restricted assets are included;
- the intended use, model/workflow, estimated credits, and output rights are acceptable;
- a local fallback exists.

Authentication and listing commands do not create an artifact, but login still changes local credential state. Do not run login without user approval.

## Inspect safely

```bash
higgsfield version
higgsfield --help
higgsfield model list --image --json
higgsfield workflow list --json
higgsfield model get <job_type> --json
higgsfield workflow get <workflow_name> --json
```

Use `model get` or `workflow get` to discover accepted parameters. Never assume a model identifier or parameter set from an old example.

If authentication is needed and approved:

```bash
higgsfield auth login
higgsfield account status
```

Never print, log, or include `higgsfield auth token` output in deliverables.

## Estimate before spending

After selecting a current image model and constructing only accepted parameters:

```bash
higgsfield generate cost <job_type> --prompt "<prompt>" [model-specific flags]
```

For a workflow:

```bash
higgsfield generate cost workflow <workflow_name> [workflow-specific flags]
```

Show the estimate and obtain approval before creating a paid job unless the user already gave a clear spending instruction.

## Generate only the approved layer

Generic CLI shape:

```bash
higgsfield generate create <job_type> \
  --prompt "<approved prompt>" \
  [model-specific flags] \
  --wait --json
```

Local media paths passed to media flags may be auto-uploaded. Treat any such path as an external disclosure.

Capture:

- CLI version;
- model/workflow identifier;
- full prompt and accepted parameters;
- estimated and actual credits if available;
- job ID and output URL/path;
- input asset provenance and approval;
- generation date and review notes.

Do not assume an output URL is permanent. Save the approved asset locally and retain generation metadata according to the project's policy.

## Recommended infographic pattern

Use Higgsfield for a **non-data-bearing layer**:

1. Create a wireframe with reserved illustration bounds.
2. Generate only the illustration/background, preferably without text.
3. Inspect for unwanted text, symbols, logos, bias, anatomical errors, and misleading implications.
4. Crop/mask the accepted asset without changing data geometry.
5. Overlay verified headline, labels, charts, annotations, and citations deterministically.
6. Preserve a no-generated-asset fallback.

One-shot infographic generation is suitable for concept exploration, not an evidence-grade source of truth. If the user insists on it for final output, manually compare every visible fact and recreate incorrect or illegible information in an editable layer.

## Failure handling

If the CLI is absent, unauthenticated, out of credits, or the service fails:

- do not install, log in, switch models, or retry paid jobs silently;
- report the exact failure without exposing credentials;
- continue with the local SVG/HTML or prompt-only fallback;
- mark Higgsfield validation as not run.
