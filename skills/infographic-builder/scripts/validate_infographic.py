#!/usr/bin/env python3
"""Check infographic delivery structure and flag obvious unresolved content."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

PLACEHOLDER_PATTERNS = (
    re.compile(r"\{\{[^}]+\}\}"),
    re.compile(r"\[(?:audience|single message|decision/action|one or two sentences|exact value|supporting evidence|context or comparison|material limitation|include a table|list source titles)[^\]]*\]", re.I),
)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError(f"not UTF-8: {path}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the structure of an infographic planning or production package."
    )
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("slug")
    parser.add_argument(
        "--production",
        action="store_true",
        help="Require a visual artifact and completed text alternative",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures for quality-gated delivery",
    )
    args = parser.parse_args()

    root = args.output_directory.expanduser().resolve()
    required = {
        "brief": root / f"{args.slug}.brief.md",
        "sources": root / f"{args.slug}.sources.csv",
        "storyboard": root / f"{args.slug}.storyboard.md",
    }
    if args.production:
        required.update(
            {
                "alt": root / f"{args.slug}.alt.md",
                "validation": root / f"{args.slug}.validation.md",
            }
        )

    errors: list[str] = []
    warnings: list[str] = []

    if not root.is_dir():
        errors.append(f"output directory does not exist: {root}")
    for label, path in required.items():
        if not path.is_file():
            errors.append(f"missing {label}: {path.name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty {label}: {path.name}")

    for label in ("brief", "storyboard", "alt"):
        path = required.get(label)
        if not path or not path.is_file():
            continue
        text = read_text(path)
        if any(pattern.search(text) for pattern in PLACEHOLDER_PATTERNS):
            errors.append(f"unresolved template placeholder in {path.name}")
        if re.search(r"\b(?:TODO|TBD|FIXME)\b", text, re.I):
            warnings.append(f"review TODO/TBD marker in {path.name}")

    sources = required["sources"]
    if sources.is_file() and sources.stat().st_size:
        with sources.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            expected = {
                "claim_id",
                "role",
                "claim_text",
                "source_title",
                "publisher",
                "source_url",
                "accessed_at",
                "method_note",
                "status",
            }
            missing_headers = sorted(expected - set(reader.fieldnames or []))
            if missing_headers:
                errors.append("source ledger missing columns: " + ", ".join(missing_headers))
            rows = list(reader)
            if not rows:
                errors.append("source ledger has no claim rows")
            seen: set[str] = set()
            for line, row in enumerate(rows, start=2):
                claim_id = (row.get("claim_id") or "").strip()
                status = (row.get("status") or "").strip()
                if not claim_id:
                    errors.append(f"source ledger row {line} has no claim_id")
                elif claim_id in seen:
                    errors.append(f"duplicate claim_id {claim_id!r} on row {line}")
                seen.add(claim_id)
                if status not in {"verified", "needs-review", "blocked"}:
                    errors.append(f"invalid status {status!r} on row {line}")
                if status == "verified":
                    for field in ("claim_text", "source_title", "publisher", "source_url", "accessed_at"):
                        if not (row.get(field) or "").strip():
                            errors.append(f"verified {claim_id or 'row'} is missing {field}")
                else:
                    warnings.append(f"{claim_id or f'row {line}'} status is {status or 'missing'}")

    if args.production:
        artifact_suffixes = (".svg", ".html", ".png", ".pdf")
        artifacts = [root / f"{args.slug}{suffix}" for suffix in artifact_suffixes]
        if not any(path.is_file() and path.stat().st_size for path in artifacts):
            errors.append(
                "missing production artifact; expected one of "
                + ", ".join(path.name for path in artifacts)
            )
        svg = root / f"{args.slug}.svg"
        if svg.is_file():
            text = read_text(svg)
            for token in ("<svg", "viewBox", "<title", "<desc"):
                if token not in text:
                    errors.append(f"{svg.name} is missing {token}")

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors or (args.strict and warnings):
        qualifier = "; strict mode rejects warnings" if args.strict and warnings else ""
        print(
            f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s){qualifier}",
            file=sys.stderr,
        )
        return 1
    print(f"PASS: structural checks completed with {len(warnings)} warning(s)")
    print("Manual evidence, semantic, design, accessibility, and export review is still required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
