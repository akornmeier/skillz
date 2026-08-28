#!/usr/bin/env python3
"""Create a deterministic infographic planning package from skill templates."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path


def valid_slug(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise argparse.ArgumentTypeError(
            "slug must contain lowercase letters, digits, and single hyphens"
        )
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold an infographic brief, source ledger, storyboard, alt text, and validation report."
    )
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("slug", type=valid_slug)
    parser.add_argument("--title", help="Human-readable title; defaults to title-cased slug")
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing scaffold files"
    )
    args = parser.parse_args()

    output = args.output_directory.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    assets = Path(__file__).resolve().parent.parent / "assets"
    title = args.title or args.slug.replace("-", " ").title()

    mappings = {
        "brief-template.md": f"{args.slug}.brief.md",
        "source-ledger-template.csv": f"{args.slug}.sources.csv",
        "storyboard-template.md": f"{args.slug}.storyboard.md",
        "alt-template.md": f"{args.slug}.alt.md",
        "validation-template.md": f"{args.slug}.validation.md",
    }

    conflicts = [output / target for target in mappings.values() if (output / target).exists()]
    if conflicts and not args.force:
        print("Refusing to overwrite existing files:", file=sys.stderr)
        for path in conflicts:
            print(f"  {path}", file=sys.stderr)
        print("Use --force only after reviewing those files.", file=sys.stderr)
        return 2

    for source_name, target_name in mappings.items():
        source = assets / source_name
        target = output / target_name
        if source.suffix == ".md":
            target.write_text(
                source.read_text(encoding="utf-8").replace("{{TITLE}}", title),
                encoding="utf-8",
            )
        else:
            shutil.copyfile(source, target)
        print(target)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
