#!/usr/bin/env python3
"""Validate core structural and accessibility properties of an SVG file."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree

XLINK = "{http://www.w3.org/1999/xlink}href"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg", type=Path)
    args = parser.parse_args()
    path = args.svg.expanduser().resolve()

    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        print(f"SVG_READ: {exc}", file=sys.stderr)
        return 2

    try:
        root = ElementTree.fromstring(source)
    except ElementTree.ParseError as exc:
        print(f"SVG_XML: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    if local_name(root.tag) != "svg":
        errors.append("SVG_ROOT: root element must be <svg>")
    view_box = root.get("viewBox", "").strip()
    if not re.fullmatch(r"-?(?:\d+(?:\.\d+)?|\.\d+)(?:\s+-?(?:\d+(?:\.\d+)?|\.\d+)){3}", view_box):
        errors.append("SVG_VIEWBOX: viewBox must contain four numeric values")

    direct_children = list(root)
    title = next((element for element in direct_children if local_name(element.tag) == "title"), None)
    desc = next((element for element in direct_children if local_name(element.tag) == "desc"), None)
    if title is None or not "".join(title.itertext()).strip():
        errors.append("SVG_TITLE: root must contain a non-empty <title>")
    if desc is None or not "".join(desc.itertext()).strip():
        errors.append("SVG_DESC: root must contain a non-empty <desc>")

    ids: set[str] = set()
    for element in root.iter():
        name = local_name(element.tag)
        if name == "script":
            errors.append("SVG_SCRIPT: scripts are not allowed")
        element_id = element.get("id")
        if element_id:
            if element_id in ids:
                errors.append(f"SVG_DUPLICATE_ID: duplicate id {element_id!r}")
            ids.add(element_id)
        for attribute in ("href", XLINK):
            value = element.get(attribute, "").strip()
            if not value:
                continue
            parsed = urlparse(value)
            if parsed.scheme in {"http", "https"} or value.startswith("//"):
                errors.append(f"SVG_REMOTE_RESOURCE: remote reference {value!r} is not allowed")

    for match in re.finditer(r"url\(#([^)]+)\)", source):
        if match.group(1) not in ids:
            errors.append(f"SVG_BROKEN_REFERENCE: missing id {match.group(1)!r}")

    for error in sorted(set(errors)):
        print(error, file=sys.stderr)
    if errors:
        return 1

    print(f"VALID: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
