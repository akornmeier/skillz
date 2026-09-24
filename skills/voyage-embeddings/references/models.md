# Voyage AI model reference

Full model catalog with dimensions, context length, and selection guidance. Source: Anthropic platform docs (Voyage AI section).

## Voyage 4 — current generation (recommended for new work)

| Model | Context | Dimensions | When to use |
| --- | --- | --- | --- |
| `voyage-4-large` | 32,000 | 1024 (default), 256, 512, 2048 | Best general-purpose retrieval quality. Pick this when quality matters more than cost. |
| `voyage-4` | 32,000 | 1024 (default), 256, 512, 2048 | Balanced quality/cost. Reasonable default for most workloads. |
| `voyage-4-lite` | 32,000 | 1024 (default), 256, 512, 2048 | Optimized for low latency and cost. Pick this for high-volume or latency-sensitive ingest. |
| `voyage-4-nano` | 32,000 | 1024 (default), 256, 512, 2048 | Open-weight (Apache 2.0) — available on Hugging Face for self-hosting. |

## Domain-specific models

| Model | Context | Dimensions | When to use |
| --- | --- | --- | --- |
| `voyage-code-3` | 32,000 | 1024 (default), 256, 512, 2048 | Code retrieval, programming docs, source files. Beats general models on code search. |
| `voyage-finance-2` | 32,000 | 1024 | Earnings calls, filings, financial analysis. |
| `voyage-law-2` | 16,000 | 1024 | Legal docs, contracts, long-context retrieval. Also strong as a general model. |

## Multimodal

| Model | Context | Dimensions | When to use |
| --- | --- | --- | --- |
| `voyage-multimodal-3.5` | 32,000 | 1024 (default), 256, 512, 2048 | Interleaved text + images + video. First production-grade video embedder from Voyage. |
| `voyage-multimodal-3` | 32,000 | 1024 | Text + content-rich images (PDF screenshots, slides, tables, figures). No video. |

## Previous generation (still supported, prefer v4 for new work)

| Model | Context | Dimensions |
| --- | --- | --- |
| `voyage-3-large` | 32,000 | 1024 (default), 256, 512, 2048 |
| `voyage-3.5` | 32,000 | 1024 (default), 256, 512, 2048 |
| `voyage-3.5-lite` | 32,000 | 1024 (default), 256, 512, 2048 |

## Decision tree

1. **Is the corpus code?** → `voyage-code-3`. The domain advantage is real and well-documented.
2. **Is the corpus finance or legal?** → `voyage-finance-2` or `voyage-law-2`. Both also do well as general models if your corpus is mixed.
3. **Is the corpus mixed text + images + video?** → `voyage-multimodal-3.5`.
4. **Is the corpus mixed text + content-rich images, no video?** → `voyage-multimodal-3` (cheaper than 3.5).
5. **General text, quality > cost?** → `voyage-4-large`.
6. **General text, balanced?** → `voyage-4`.
7. **General text, low latency / high volume?** → `voyage-4-lite`.

## Dimension and quantization knobs

All v4 / v3-line models are **Matryoshka** — you can truncate a 1024-dim vector to 512, 256, etc., and renormalize without re-embedding. This trades retrieval quality for storage. The leading 256 dims are typically ~95% as good as the full 1024 for many tasks.

```python
import voyageai
import numpy as np

vo = voyageai.Client()
embd = vo.embed(["text"], model="voyage-4").embeddings  # 1024-dim by default

short_dim = 256
truncated = np.array(embd)[:, :short_dim]
truncated = truncated / np.linalg.norm(truncated, axis=1, keepdims=True)
```

Or pass `output_dimension=256` to `vo.embed()` directly (cleaner).

### `output_dtype` quantization

Pass `output_dtype` to `vo.embed()`:

| `output_dtype` | Storage per dim | Retrieval impact |
| --- | --- | --- |
| `float` (default) | 4 bytes | None — baseline |
| `int8`, `uint8` | 1 byte (4× saving) | Small but measurable |
| `binary`, `ubinary` | 0.125 bytes (32× saving) | Larger drop, but acceptable for many use cases when paired with reranking |

Pinecone supports `int8` indexes directly. For binary, you'll need to handle the bit-packing yourself — most users should stick to `float` and only quantize when storage is a real bottleneck.

## input_type — the most important parameter

```python
vo.embed(texts, model="voyage-4", input_type="document")  # for upserting
vo.embed(texts, model="voyage-4", input_type="query")     # for searching
```

What happens under the hood: Voyage prepends a fixed prompt to each input.

- `document` → *"Represent the document for retrieval: " + your_text*
- `query` → *"Represent the query for retrieving supporting documents: " + your_text*
- `None` → no prompt, retrieval quality drops

Always specify. Mixing types between ingest and search is the most common silent bug — your top-k results will look "fine" on easy queries and fail on harder ones.

## Pricing (high-level)

Voyage charges per token embedded. Pricing varies by model — `voyage-4-lite` is the cheapest, domain-specific models are mid-tier, `voyage-4-large` and `voyage-multimodal-3.5` are the most expensive. See [Voyage's pricing page](https://docs.voyageai.com/docs/pricing) for current numbers.

For typical ingests:
- A 1M-token corpus costs roughly $0.02–$0.18 depending on model.
- Pinecone storage (1024-dim float, ~4KB/vector) costs $0.33/GB/month at the time of writing — the index storage is usually a smaller line item than the embedding itself.

## Similarity functions

Voyage embeddings are **L2-normalized to unit length**. Consequences:
- Cosine similarity ≡ dot product (use dot, it's faster).
- Cosine and Euclidean produce identical rankings.

For Pinecone indexes embedding Voyage vectors, `metric=cosine` is the safe default.

## SDKs

```bash
pip install -U voyageai
```

```python
import voyageai
vo = voyageai.Client()  # reads VOYAGE_API_KEY from env
result = vo.embed(["Sample"], model="voyage-4", input_type="document")
print(result.embeddings[0])
```

HTTP fallback (when not using the SDK):

```bash
curl https://api.voyageai.com/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $VOYAGE_API_KEY" \
  -d '{
    "input": ["Sample text 1", "Sample text 2"],
    "model": "voyage-4",
    "input_type": "document"
  }'
```

## Useful links

- [Voyage docs](https://docs.voyageai.com/docs/embeddings)
- [Voyage Python package](https://github.com/voyage-ai/voyageai-python)
- [Voyage HTTP API reference](https://docs.voyageai.com/reference/embeddings-api)
- [Anthropic + Pinecone RAG cookbook](https://platform.claude.com/cookbook/third-party-pinecone-rag-using-pinecone)
- [Voyage tokenization guide](https://docs.voyageai.com/docs/tokenization)
- [Voyage AWS Marketplace](https://docs.voyageai.com/docs/aws-marketplace-model-package)
