#!/usr/bin/env python3
"""Embed a query with Voyage AI and search a standard Pinecone index.

Usage:
    query.py \\
        --index code-corpus-voyage \\
        --namespace pono \\
        --model voyage-code-3 \\
        --query "how does the retry handler work" \\
        [--top-k 10]

Env vars: VOYAGE_API_KEY, PINECONE_API_KEY (both in ~/.claude/settings.local.json)

Notes:
    - Uses input_type="query" — the right side of the document/query asymmetry
      that Voyage embeddings depend on. Mismatched input_type silently degrades
      retrieval quality.
    - --model must match the model used at upsert time. Mixing models across
      ingest and query produces nonsense scores even when both succeed.
    - For integrated Pinecone indexes (e.g. llama-text-embed-v2), use the
      pinecone-query skill (MCP) instead — this script is for standard indexes
      with client-side embedding only.
"""

import argparse
import os
import sys

try:
    import voyageai
    from pinecone import Pinecone
except ImportError:
    sys.exit("missing deps — run: pip install voyageai pinecone")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--index", required=True, help="Pinecone standard index name")
    p.add_argument("--namespace", required=True, help="Namespace within the index")
    p.add_argument("--model", required=True, help="Voyage model — must match the model used at upsert time")
    p.add_argument("--query", required=True, help="The search text")
    p.add_argument("--top-k", type=int, default=10, help="Number of results to return (default 10)")
    args = p.parse_args()

    if not os.environ.get("VOYAGE_API_KEY"):
        sys.exit("VOYAGE_API_KEY not set — check ~/.claude/settings.local.json env block")
    if not os.environ.get("PINECONE_API_KEY"):
        sys.exit("PINECONE_API_KEY not set — check ~/.claude/settings.local.json env block")

    vo = voyageai.Client()
    embedding = vo.embed([args.query], model=args.model, input_type="query").embeddings[0]

    pc = Pinecone()
    result = pc.Index(args.index).query(
        vector=embedding,
        namespace=args.namespace,
        top_k=args.top_k,
        include_metadata=True,
    )

    if not result.matches:
        print(f"no results in {args.index}/{args.namespace}")
        return 0

    for i, match in enumerate(result.matches, 1):
        meta = match.metadata or {}
        source = meta.get("source", "")
        text = meta.get("text", "")
        snippet = text[:200].replace("\n", " ") + ("..." if len(text) > 200 else "")
        print(f"{i:2}. [{match.score:.3f}] {source or match.id}")
        if snippet:
            print(f"    {snippet}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
