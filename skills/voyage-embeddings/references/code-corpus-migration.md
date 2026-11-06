# The user's `code-corpus` migration

Read only when working on the user's `code-corpus` index migration. The generic parallel-run recipe lives in SKILL.md; this file holds the user's own decision state and specifics.

## Open decision: should we actually migrate code-corpus?

> **Status (noted 2026-05-05):** Skill is built and ready. Migration of the existing `code-corpus` index from `llama-text-embed-v2` → `voyage-code-3` is **deferred — not committed.** Bring this up proactively when the conversation touches code retrieval, `recall` quality, or the `code-corpus` index.
>
> **Update (2026-11):** Voyage's embeddings docs now list `voyage-code-4` as the current code model and move `voyage-code-3` to "Older models". That is the "materially better code model" trigger below; it makes `voyage-code-4` the target if the migration goes ahead, but it does not by itself make the go/no-go call.

The migration recipe is a tool, not a commitment. Before running it, the user (Tony) wants to make a deliberate go/no-go call. Surface this section and walk through the triggers when relevant — don't silently assume the migration is wanted.

**Triggers to migrate:**
- An active code-search workflow with concrete queries that can be A/B tested between the two indexes
- Visible retrieval quality pain on `code-corpus` (e.g. `recall` returning irrelevant code chunks)
- Voyage releases a materially better code model (voyage-code-4, etc.)
- Tony explicitly says "let's migrate"

**Triggers to stay on `llama-text-embed-v2`:**
- `code-corpus` is mostly cold storage (no real query traffic)
- One-vendor simplicity (Pinecone integrated, MCP-queryable) is worth more than the quality lift
- No bandwidth to maintain a client-side embedding pipeline

**When asked "should I migrate?" with no trigger fired**, the honest answer is "not yet — here's what would change that." Don't pitch the migration just because the recipe exists.

## Specifics for this index

- Current index: `code-corpus`, integrated `llama-text-embed-v2`.
- Planned new index: `code-corpus-voyage` (standard, AWS `us-east-1`, dim=1024, metric=cosine).
- Namespaces: one per repo (e.g. `pono`), following the convention in `~/.claude/memory-config.json`. Re-ingest each with the same namespace name.
- Cutover: after the side-by-side query comparison favors Voyage and the user approves, update `~/.claude/memory-config.json` so `code_index` points to `code-corpus-voyage` and `embedding_model` names the Voyage model used at ingest.
- Keep the old `code-corpus` index after cutover. Deleting it needs the user's separate, explicit authorization, and only once nothing else reads from it.
- Chunking: the bundled script is one record per file; for this corpus you'll typically want function-level chunks.
