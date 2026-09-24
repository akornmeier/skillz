---
name: voyage-embeddings
description: Voyage AI embeddings reference and Pinecone integration. Use when the user mentions Voyage or any Voyage model (voyage-code-3, voyage-4, voyage-finance-2, voyage-law-2, voyage-multimodal), is picking an embedding model for code, finance, legal, or multilingual retrieval, or is migrating a Pinecone index from an integrated model (e.g., llama-text-embed-v2) to Voyage. Also use when embedding with Voyage to upsert into or query a standard Pinecone index, or when the user mentions input_type, document vs query embeddings, matryoshka truncation, or int8/binary quantization. Use even when the user doesn't say Voyage — many embedding questions are Voyage questions in disguise.
---

# Voyage AI embeddings

Voyage AI is the embedding provider Anthropic recommends as a complement to Claude. This skill covers two things:

1. **Reference** — which model to pick, the `input_type` rule, dimensions, quantization
2. **Workflow** — embedding text/code with Voyage and upserting into a **standard** (non-integrated) Pinecone index

## When this skill applies

- User wants higher retrieval quality than `llama-text-embed-v2` provides — especially for code (`voyage-code-3`), finance (`voyage-finance-2`), or legal (`voyage-law-2`) content
- User is embedding content client-side and pushing vectors to Pinecone
- User is migrating an existing integrated index to a Voyage model
- User asks any "which model" or "what dimensions" question about Voyage

## When this skill does NOT apply

- User wants to query an **integrated** Pinecone index with a built-in embedder (use the `pinecone-query` skill — that one uses MCP)
- User wants generic OpenAI / Cohere / HuggingFace embeddings — different provider, different SDK

## Open decision: should we actually migrate code-corpus?

> **Status (noted 2026-05-05):** Skill is built and ready. Migration of the existing `code-corpus` index from `llama-text-embed-v2` → `voyage-code-3` is **deferred — not committed.** Bring this up proactively when the conversation touches code retrieval, `recall` quality, or the `code-corpus` index.

The migration recipe further down is a tool, not a commitment. Before running it, the user (Tony) wants to make a deliberate go/no-go call. Surface this section and walk through the triggers when relevant — don't silently assume the migration is wanted.

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

## Account and key

The `VOYAGE_API_KEY` is set in `~/.claude/settings.local.json` under the `env` block. Claude Code loads it into the shell environment of any tool it spawns, so `voyageai.Client()` and `curl` against `api.voyageai.com` both pick it up automatically — no extra wiring needed.

If the key is missing, the script will exit with a clear message. Direct the user to add it to the same env block (alongside `PINECONE_API_KEY`).

## Model selection — quick reference

| Task | Recommended model | Dim | Why |
| --- | --- | --- | --- |
| Code retrieval | `voyage-code-3` | 1024 (default) | Trained on code, beats general models on code search |
| General-purpose, best quality | `voyage-4-large` | 1024 (default) | Top general retrieval quality |
| General-purpose, balanced | `voyage-4` | 1024 (default) | Good quality at lower latency/cost |
| Latency/cost-sensitive | `voyage-4-lite` | 1024 (default) | Fastest, cheapest of the v4 line |
| Finance text | `voyage-finance-2` | 1024 | Domain-tuned |
| Legal text | `voyage-law-2` | 1024 (16K context) | Domain-tuned, also strong general |
| Multimodal (text + images) | `voyage-multimodal-3.5` | 1024 (default) | Adds video support over -3 |

All models support `output_dimension` truncation to 256, 512, 1024, or 2048 (Matryoshka). Truncating costs storage but keeps quality high — use it when Pinecone vector storage matters.

For the full table with context lengths, dimension options, and FAQ on dtype/quantization, see `references/models.md`.

## The input_type rule (read this — it's the #1 correctness gotcha)

Voyage prepends different prompts to your text depending on `input_type`:

- `input_type="document"` → prepends *"Represent the document for retrieval: "*
- `input_type="query"` → prepends *"Represent the query for retrieving supporting documents: "*
- `input_type=None` → no prompt; retrieval quality drops noticeably

**Default behavior in this skill's scripts:**

- Use `document` when **upserting** into Pinecone (the records are documents, even if they came from a search).
- Use `query` when **searching** ad-hoc with a user's question.

The script defaults to `document` and exposes a `--input-type query` override. If the user is doing something unusual (e.g., embedding queries to upsert as a "query bank" for query expansion), surface the choice explicitly rather than silently defaulting.

The reason this matters: documents and queries are distributionally different (queries are short, fragmentary; documents are long, declarative). Voyage uses the prepended prompt to align both into the same retrieval space. Mismatched `input_type` → embeddings drift apart in the vector space → retrieval looks fine in tests on "obvious" queries but quietly fails on harder ones.

## Embed-and-upsert workflow

Use `scripts/embed_and_upsert.py` to embed local text/code and upsert into a Pinecone **standard** index.

```bash
python scripts/embed_and_upsert.py \
  --index code-corpus-voyage \
  --namespace pono \
  --model voyage-code-3 \
  --file path/to/file.py \
  --file path/to/another.py
```

What the script does:
1. Reads each `--file`, treats one file as one record (chunk how you want before passing in)
2. Embeds in batches of up to 128 (Voyage's per-call limit)
3. Generates a stable record ID = `sha256(text)[:16]` so re-running is idempotent
4. Upserts in batches of up to 100 to the named Pinecone index/namespace
5. Stores the original text in `metadata.text` so you can read it back from search hits

Read the script before running for a real ingest — the chunking is naive (one record per file). For the `code-corpus` use case you'll typically want function-level chunks.

## Querying a Voyage-embedded Pinecone index

The Pinecone MCP server only supports integrated indexes, so the existing `pinecone-query` skill won't work against Voyage-backed indexes. Use the bundled `scripts/query.py` — it embeds the query with `input_type="query"` (the right side of the asymmetry) and runs a standard Pinecone vector search.

```bash
python scripts/query.py \
  --index code-corpus-voyage \
  --namespace pono \
  --model voyage-code-3 \
  --query "how does the retry handler work" \
  --top-k 10
```

The `--model` must match the model used at ingest. Mixing models across upsert and query is silent garbage — different embedding spaces produce nonsense scores even when both runs succeed.

For ad-hoc work outside this script, use the Pinecone Python SDK (`pc.Index(name).query(vector=..., namespace=..., top_k=...)`) — never the MCP `search-records` tool.

## Migration recipe: code-corpus → voyage-code-3

The current `code-corpus` index uses `llama-text-embed-v2` as an integrated model. Migrating to `voyage-code-3` means moving from integrated to standard, which means client-side embedding from now on.

**Recommended path (parallel run, then swap):**

1. Create a new standard index `code-corpus-voyage` on AWS `us-east-1`, dim=1024, metric=cosine.
   ```bash
   pc index create-serverless \
     --name code-corpus-voyage \
     --dimension 1024 \
     --metric cosine \
     --cloud aws \
     --region us-east-1
   ```
2. Re-ingest each repo's code into the new index using `scripts/embed_and_upsert.py` with `--model voyage-code-3`. Use the same per-repo namespace convention from `~/.claude/memory-config.json`.
3. Side-by-side compare a handful of real queries (the same query embedded twice — once with `llama-text-embed-v2` against the old index, once with `voyage-code-3` against the new one). Eyeball whether the Voyage results are better for *your* code.
4. If yes: update `~/.claude/memory-config.json` so `code_index` points to `code-corpus-voyage` and `embedding_model` is `voyage-code-3`. Delete the old index when nothing else reads from it.

**Why parallel-run instead of in-place:** A dimension/metric mismatch between writes and existing data corrupts an index irrecoverably. Running both in parallel for a few days lets you bail out cheaply if Voyage doesn't actually win on your data — and it keeps existing tools working during the migration.

## Error handling strategy (for `embed_and_upsert.py`)

The script's `upsert_with_recovery()` function is the single most consequential design decision in this workflow. Three reasonable strategies:

- **(a) Abort on first failure.** Fast feedback, simple. Bad on large jobs — lose progress when one batch hiccups.
- **(b) Retry the whole batch with exponential backoff.** Handles transient errors (rate limits, blips). Good default.
- **(c) Retry individual vectors on batch failure.** Slowest but isolates a single bad record.

Voyage's API rate-limits and Pinecone's serverless upsert can both produce transient 429/503s. (b) is the right default for almost all ingests.

The script ships with strategy (b): exponential backoff (1s, 2s, 4s, 8s) over 4 attempts, catching all exceptions. For jobs larger than ~50k records — where burning 15s on a permanent error becomes a real cost — narrow the except clause to `PineconeApiException` with retriable status codes only.

## Pricing and quantization

Voyage charges per token embedded. For storage-sensitive ingests, embeddings can be quantized at request time:

```python
result = vo.embed(texts, model="voyage-4", input_type="document", output_dtype="int8")
```

`int8` reduces vector storage 4×; `binary`/`ubinary` reduce 32× at the cost of recall. Most users won't need this — full `float` is the default and matches what Pinecone expects without further configuration. See `references/models.md` for details.

## Troubleshooting

- **`voyageai.error.AuthenticationError`** — `VOYAGE_API_KEY` isn't reaching the script. Confirm it's in the `env` block of `~/.claude/settings.local.json` and restart the Claude Code session so the env reloads.
- **Dimension mismatch on upsert** — your Voyage model returned 1024-dim vectors but the Pinecone index was created with a different dimension. Recreate the index with the matching dim, or pass `output_dimension=N` to `vo.embed()` to match.
- **Retrieval quality looks worse than llama-text-embed-v2** — first thing to check: did `input_type` match between embedding and query time? Mixing `document`/`query`/`None` is the most common cause.
- **Rate-limit errors during large ingests** — the recovery strategy in `upsert_with_recovery()` should retry with backoff. If it's still failing, lower `VOYAGE_BATCH_SIZE` from 128 to ~32.

## Reference files

- `references/models.md` — full model table, decision tree for picking a model, quantization details
- `scripts/embed_and_upsert.py` — the one-script embed + upsert pipeline (input_type=document)
- `scripts/query.py` — search a Voyage-embedded standard Pinecone index (input_type=query)
