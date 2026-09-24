#!/usr/bin/env python3
"""Embed local text/code with Voyage AI and upsert into a standard Pinecone index.

Usage:
    embed_and_upsert.py \\
        --index code-corpus-voyage \\
        --namespace pono \\
        --model voyage-code-3 \\
        --file path/to/file.py [--file ...]

Env vars: VOYAGE_API_KEY, PINECONE_API_KEY (both already in ~/.claude/settings.local.json)

Notes:
    - Treats one file as one record. Pre-chunk before passing in if you want
      smaller granularity.
    - Stable record IDs (sha256 of text) make re-runs idempotent — same content
      overwrites in place rather than duplicating.
    - input_type defaults to 'document' (right for upserts). Pass --input-type
      query only for ad-hoc test searches.
"""

import argparse
import hashlib
import os
import sys
import time
from pathlib import Path

try:
    import voyageai
    from pinecone import Pinecone
except ImportError:
    sys.exit("missing deps — run: pip install voyageai pinecone")


VOYAGE_BATCH_SIZE = 128   # Voyage's max inputs per /embeddings call
PINECONE_BATCH_SIZE = 100  # Pinecone's recommended upsert batch size


def read_records(files: list[Path]) -> list[dict]:
    """One record per file. Stable ID = first 16 hex chars of sha256(text)."""
    records = []
    for f in files:
        text = f.read_text()
        if not text.strip():
            print(f"skip empty file: {f}", file=sys.stderr)
            continue
        rid = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        records.append({"id": rid, "text": text, "source": str(f)})
    return records


def embed_records(vo: "voyageai.Client", records: list[dict], model: str, input_type: str) -> None:
    """Add a 'values' field (the embedding) to every record, in-place."""
    for i in range(0, len(records), VOYAGE_BATCH_SIZE):
        batch = records[i:i + VOYAGE_BATCH_SIZE]
        result = vo.embed(
            [r["text"] for r in batch],
            model=model,
            input_type=input_type,
        )
        for r, emb in zip(batch, result.embeddings):
            r["values"] = emb
        print(f"embedded {i + len(batch)}/{len(records)}")


def upsert_with_recovery(index, batch: list[dict], namespace: str, max_attempts: int = 4) -> None:
    """Upsert one batch with exponential backoff on transient failures.

    Retries up to max_attempts with 1s, 2s, 4s, 8s sleeps. Catches all
    exceptions rather than narrowing to 429/5xx — Pinecone's exception
    hierarchy varies across SDK versions and distinguishing transient from
    permanent reliably is more trouble than it's worth at this scale.

    Cost of this simplicity: a permanent error (e.g. dim mismatch) burns ~15s
    of retries before surfacing. Acceptable trade-off for ~50k-record ingests.
    For larger jobs, narrow the except clause to PineconeApiException with
    retriable status codes.
    """
    for attempt in range(max_attempts):
        try:
            index.upsert(vectors=batch, namespace=namespace)
            return
        except Exception:
            if attempt == max_attempts - 1:
                raise
            time.sleep(2 ** attempt)


def upsert_records(index, records: list[dict], namespace: str) -> None:
    vectors = [
        {
            "id": r["id"],
            "values": r["values"],
            "metadata": {"text": r["text"], "source": r["source"]},
        }
        for r in records
    ]
    for i in range(0, len(vectors), PINECONE_BATCH_SIZE):
        batch = vectors[i:i + PINECONE_BATCH_SIZE]
        upsert_with_recovery(index, batch, namespace)
        print(f"upserted {i + len(batch)}/{len(vectors)} into {namespace}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--index", required=True, help="Pinecone standard index name")
    p.add_argument("--namespace", required=True, help="Namespace within the index (per-repo by convention)")
    p.add_argument("--model", default="voyage-4", help="Voyage model (e.g. voyage-code-3, voyage-4-large)")
    p.add_argument("--file", type=Path, action="append", default=[], required=True, help="File to embed (repeatable)")
    p.add_argument(
        "--input-type",
        choices=["document", "query"],
        default="document",
        help="'document' for upserts (default), 'query' for ad-hoc test searches",
    )
    args = p.parse_args()

    if not os.environ.get("VOYAGE_API_KEY"):
        sys.exit("VOYAGE_API_KEY not set — check ~/.claude/settings.local.json env block")
    if not os.environ.get("PINECONE_API_KEY"):
        sys.exit("PINECONE_API_KEY not set — check ~/.claude/settings.local.json env block")

    records = read_records(args.file)
    if not records:
        sys.exit("no records to embed (all files empty?)")

    vo = voyageai.Client()
    pc = Pinecone()
    index = pc.Index(args.index)

    t0 = time.time()
    embed_records(vo, records, args.model, args.input_type)
    upsert_records(index, records, args.namespace)
    print(f"done — {len(records)} records in {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
