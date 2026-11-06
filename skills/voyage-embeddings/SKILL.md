---
name: voyage-embeddings
description: Voyage AI embeddings reference and Pinecone integration. Use when the user mentions Voyage or any Voyage model (voyage-code-4, voyage-code-3, voyage-4, voyage-finance-2, voyage-law-2, voyage-multimodal), is embedding with Voyage to upsert into or query a Pinecone index, or is migrating a Pinecone index (e.g., from integrated llama-text-embed-v2) to Voyage. Also use when the user explicitly asks to choose an embedding provider or model for code, finance, legal, or multilingual retrieval.
compatibility: Requires Python 3 with the voyageai and pinecone packages, VOYAGE_API_KEY and PINECONE_API_KEY in the environment, and network access. Voyage embedding calls are paid per token.
---

# Voyage AI embeddings

Voyage AI is the embedding provider Anthropic recommends as a complement to Claude. This skill covers two things:

1. **Reference** — which model to pick, the `input_type` rule, dimensions, quantization
2. **Workflow** — embedding text/code with Voyage and upserting into a **standard** (non-integrated) Pinecone index

`<skill-dir>` below means the directory containing this SKILL.md; run the bundled scripts by that path, not relative to the user's project.

`references/code-corpus-migration.md` — read only when working on the user's code-corpus index migration.

## When this skill applies

- User wants higher retrieval quality than `llama-text-embed-v2` provides — especially for code (`voyage-code-4`), finance (`voyage-finance-2`), or legal (`voyage-law-2`) content
- User is embedding content client-side and pushing vectors to Pinecone
- User is migrating an existing integrated index to a Voyage model
- User asks any "which model" or "what dimensions" question about Voyage

## When this skill does NOT apply

- User wants to query an **integrated** Pinecone index with a built-in embedder — the Pinecone MCP tools handle that directly
- User wants generic OpenAI / Cohere / HuggingFace embeddings — different provider, different SDK

## Approval gates

Confirm with the user before any of these, even when the overall task is clear:

- Paid Voyage embedding of a corpus (state the file/record count and model first)
- Creating a Pinecone index
- Any deletion (index, namespace, or records)

Migrations keep the original index by default. Deleting it needs separate, explicit authorization after cutover.

## Account and key

The `VOYAGE_API_KEY` is set in `~/.claude/settings.local.json` under the `env` block. Claude Code loads it into the shell environment of any tool it spawns, so `voyageai.Client()` and `curl` against `api.voyageai.com` both pick it up automatically — no extra wiring needed.

If the key is missing, the script will exit with a clear message. Direct the user to add it to the same env block (alongside `PINECONE_API_KEY`).

## Model selection — quick reference

| Task | Recommended model | Dimensions | Why |
| --- | --- | --- | --- |
| Code retrieval | `voyage-code-4` | 1024 (default); 256, 512, 2048 | Current code model, built for code retrieval and coding agents; supersedes `voyage-code-3` |
| General-purpose, best quality | `voyage-4-large` | 1024 (default); 256, 512, 2048 | Top general retrieval quality |
| General-purpose, balanced | `voyage-4` | 1024 (default); 256, 512, 2048 | Good quality at lower latency/cost |
| Latency/cost-sensitive | `voyage-4-lite` | 1024 (default); 256, 512, 2048 | Fastest, cheapest of the v4 line |
| Finance text | `voyage-finance-2` | 1024 only | Domain-tuned |
| Legal text | `voyage-law-2` | 1024 only (16K context) | Domain-tuned, also strong general |
| Multimodal (text + images) | `voyage-multimodal-3.5` | 1024 (default); 256, 512, 2048 | Adds video support over -3 |

Models with several listed dimensions accept `output_dimension` (Matryoshka truncation); `voyage-finance-2` and `voyage-law-2` are fixed at 1024. Smaller dimensions save Pinecone storage at some cost in retrieval quality.

For the full table with context lengths, dimension options, and FAQ on dtype/quantization, see `references/models.md`.

## The input_type rule (read this — it's the #1 correctness gotcha)

Ingest with `input_type="document"`; search with `input_type="query"`. Never use the same value on both sides, and never omit it.

Voyage prepends different prompts to your text depending on `input_type`:

- `input_type="document"` → prepends *"Represent the document for retrieval: "*
- `input_type="query"` → prepends *"Represent the query for retrieving supporting documents: "*
- `input_type=None` → no prompt; retrieval quality drops noticeably

`embed_and_upsert.py` defaults to `document` and exposes a `--input-type query` override; `query.py` always uses `query`. If the user is doing something unusual (e.g., embedding queries to upsert as a "query bank" for query expansion), surface the choice explicitly rather than silently defaulting.

The reason this matters: documents and queries are distributionally different (queries are short, fragmentary; documents are long, declarative). Voyage uses the prepended prompt to align both into the same retrieval space. Using the wrong `input_type` on either side → embeddings drift apart in the vector space → retrieval looks fine in tests on "obvious" queries but quietly fails on harder ones.

## Embed-and-upsert workflow

Run `<skill-dir>/scripts/embed_and_upsert.py` to embed local text/code and upsert into a Pinecone **standard** index. It makes paid Voyage calls, so confirm first (see Approval gates).

```bash
python3 <skill-dir>/scripts/embed_and_upsert.py \
  --index <index> \
  --namespace <namespace> \
  --model voyage-code-4 \
  --file path/to/file.py \
  --file path/to/another.py
```

What the script does:
1. Reads each `--file`, treats one file as one record (chunk how you want before passing in)
2. Embeds in batches of up to 128 (Voyage's per-call limit)
3. Generates a stable record ID = `sha256(text)[:16]` so re-running is idempotent
4. Upserts in batches of up to 100 to the named Pinecone index/namespace, retrying each batch with exponential backoff
5. Stores the original text in `metadata.text` so you can read it back from search hits

Read the script before running a real ingest — the chunking is naive (one record per file). For code you'll typically want function-level chunks.

## Querying a Voyage-embedded Pinecone index

The Pinecone MCP server only queries integrated indexes, so it can't search Voyage-backed standard indexes. Run `<skill-dir>/scripts/query.py` instead — it embeds the query with `input_type="query"` and runs a standard Pinecone vector search.

```bash
python3 <skill-dir>/scripts/query.py \
  --index <index> \
  --namespace <namespace> \
  --model voyage-code-4 \
  --query "how does the retry handler work" \
  --top-k 10
```

The `--model` must match the model used at ingest. Mixing models across upsert and query is silent garbage — different embedding spaces produce nonsense scores even when both runs succeed.

For ad-hoc work outside this script, use the Pinecone Python SDK (`pc.Index(name).query(vector=..., namespace=..., top_k=...)`) — never the MCP `search-records` tool.

## Migration recipe: integrated index → Voyage

Migrating an index that uses an integrated model (e.g. `llama-text-embed-v2`) to a Voyage model means moving from integrated to standard, which means client-side embedding from then on.

**Recommended path (parallel run, then swap).** Present these as proposed steps and get approval at each gate:

1. **Gate: index creation.** Create a new standard index `<index>-voyage`, dimension matching the model (1024 by default), metric=cosine.
   ```bash
   pc index create-serverless \
     --name <index>-voyage \
     --dimension 1024 \
     --metric cosine \
     --cloud aws \
     --region us-east-1
   ```
2. **Gate: paid embedding.** Re-ingest each namespace into the new index with `embed_and_upsert.py` (`input_type="document"`), keeping the same namespace names.
3. Side-by-side compare a handful of real queries (the same query against the old index with its integrated model, and against the new one via `query.py`). Eyeball whether the Voyage results are better for *this* corpus.
4. **Gate: cutover.** If Voyage wins and the user approves, repoint whatever config or code reads the index to the new one.
5. Keep the original index. Deleting it is a separate decision that needs explicit authorization once nothing reads from it.

**Why parallel-run instead of in-place:** A dimension/metric mismatch between writes and existing data corrupts an index irrecoverably. Running both in parallel for a few days lets you bail out cheaply if Voyage doesn't actually win on your data — and it keeps existing tools working during the migration.

## Pricing and quantization

Voyage charges per token embedded. For storage-sensitive ingests, models that support it can return quantized embeddings at request time:

```python
result = vo.embed(texts, model="voyage-4", input_type="document", output_dtype="int8")
```

`int8` reduces vector storage 4×; `binary`/`ubinary` reduce 32× at the cost of recall. Most users won't need this — full `float` is the default and matches what Pinecone expects without further configuration. See `references/models.md` for details.

## Troubleshooting

- **`voyageai.error.AuthenticationError`** — `VOYAGE_API_KEY` isn't reaching the script. Confirm it's in the `env` block of `~/.claude/settings.local.json` and restart the Claude Code session so the env reloads.
- **Dimension mismatch on upsert** — the Voyage model's output dimension differs from the Pinecone index's. If the model supports it, pass `output_dimension=N` to `vo.embed()` to match the index; otherwise create a new, correctly-dimensioned index (with approval) and leave the existing one alone.
- **Retrieval quality looks worse than llama-text-embed-v2** — first check `input_type`: ingest must use `document` and search must use `query`. Using the same value on both sides, or `None`, is the most common cause.
- **Rate-limit errors during large ingests** — `upsert_with_recovery()` retries with backoff. If it's still failing, lower `VOYAGE_BATCH_SIZE` from 128 to ~32.

## Reference files

- `references/models.md` — read for the full model table, decision tree for picking a model, quantization details
- `scripts/embed_and_upsert.py` — run to embed + upsert (input_type=document); its docstring explains the retry strategy
- `scripts/query.py` — run to search a Voyage-embedded standard Pinecone index (input_type=query)
