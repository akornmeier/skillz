#!/usr/bin/env python3
"""Validate the structural and offline-package contracts of a Plan F3 HTML file."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

REQUIRED_SECTIONS = {
    "purpose",
    "problem",
    "solution",
    "files",
    "phases",
    "validation",
    "notes",
    "amendments",
}
REQUIRED_METADATA = {
    "created",
    "modified",
    "commits",
    "agent name",
    "session id",
    "back refs",
    "forward refs",
}
REQUIRED_CSS_VARS = {
    "--bg",
    "--paper-2",
    "--ink",
    "--muted",
    "--soft",
    "--rule",
    "--accent",
    "--accent-tint",
}
RESOURCE_ATTRIBUTES = {"src", "srcset", "poster", "data"}
FORBIDDEN_TAGS = {"script", "iframe", "object", "embed"}


@dataclass(order=True)
class Diagnostic:
    line: int
    column: int
    code: str
    message: str


@dataclass
class Figure:
    line: int
    column: int
    has_svg: bool = False
    svg_title: str = ""
    svg_desc: str = ""
    image_src: str = ""
    image_alt: str | None = None
    caption: str = ""


class PlanParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.diagnostics: list[Diagnostic] = []
        self.ids: dict[str, tuple[int, int]] = {}
        self.sections: set[str] = set()
        self.style_count = 0
        self.style_parts: list[str] = []
        self.in_style = False
        self.title_parts: list[str] = []
        self.in_title = False
        self.in_meta = False
        self.meta_depth = 0
        self.meta_key: list[str] | None = None
        self.meta_pending_key = ""
        self.meta_value: list[str] | None = None
        self.metadata: dict[str, str] = {}
        self.figures: list[Figure] = []
        self.figure_stack: list[Figure] = []
        self.capture_svg_title: list[str] | None = None
        self.capture_svg_desc: list[str] | None = None
        self.capture_caption: list[str] | None = None
        self.resources: list[tuple[str, int, int]] = []

    def add(self, code: str, message: str) -> None:
        line, column = self.getpos()
        self.diagnostics.append(Diagnostic(line, column + 1, code, message))

    @staticmethod
    def attrs_dict(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {key.lower(): value or "" for key, value in attrs}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        values = self.attrs_dict(attrs)
        line, column = self.getpos()

        element_id = values.get("id")
        if element_id:
            if element_id in self.ids:
                first_line, _ = self.ids[element_id]
                self.add("PF3_DUPLICATE_ID", f"duplicate id {element_id!r}; first seen on line {first_line}")
            else:
                self.ids[element_id] = (line, column + 1)
            if tag == "section":
                self.sections.add(element_id)

        if tag in FORBIDDEN_TAGS:
            self.add("PF3_FORBIDDEN_TAG", f"forbidden <{tag}> element")
        if tag == "link" and values.get("rel", "").lower() == "stylesheet":
            self.add("PF3_EXTERNAL_STYLE", "external stylesheet links are forbidden")
        if tag == "style":
            self.style_count += 1
            self.in_style = True
        if tag == "title":
            self.in_title = True

        classes = set(values.get("class", "").split())
        if tag == "details" and "meta" in classes:
            self.in_meta = True
            self.meta_depth = 1
        elif self.in_meta:
            self.meta_depth += 1
        if self.in_meta and tag == "dt":
            self.meta_key = []
        if self.in_meta and tag == "dd":
            self.meta_value = []

        if tag == "figure":
            figure = Figure(line=line, column=column + 1)
            self.figures.append(figure)
            self.figure_stack.append(figure)
        elif self.figure_stack:
            figure = self.figure_stack[-1]
            if tag == "svg":
                figure.has_svg = True
            elif tag == "title" and figure.has_svg:
                self.capture_svg_title = []
            elif tag == "desc" and figure.has_svg:
                self.capture_svg_desc = []
            elif tag == "img":
                figure.image_src = values.get("src", "").strip()
                figure.image_alt = values.get("alt")
            elif tag == "figcaption":
                self.capture_caption = []

        for attribute in RESOURCE_ATTRIBUTES:
            raw = values.get(attribute, "").strip()
            if not raw:
                continue
            candidates = [raw]
            if attribute == "srcset":
                candidates = [part.strip().split()[0] for part in raw.split(",") if part.strip()]
            for candidate in candidates:
                self.resources.append((candidate, line, column + 1))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "style":
            self.in_style = False
        if tag == "title":
            self.in_title = False
        if self.in_meta and tag == "dt" and self.meta_key is not None:
            self.meta_pending_key = normalize_text("".join(self.meta_key))
            self.meta_key = None
        if self.in_meta and tag == "dd" and self.meta_value is not None:
            key = self.meta_pending_key
            value = normalize_text("".join(self.meta_value))
            if key:
                if key in self.metadata:
                    self.add("PF3_METADATA_DUPLICATE", f"duplicate metadata row {key!r}")
                self.metadata[key] = value
            self.meta_pending_key = ""
            self.meta_value = None
        if tag == "details" and self.in_meta and self.meta_depth == 1:
            self.in_meta = False
            self.meta_depth = 0
        elif self.in_meta:
            self.meta_depth -= 1

        if self.figure_stack:
            figure = self.figure_stack[-1]
            if tag == "title" and self.capture_svg_title is not None:
                figure.svg_title = normalize_text("".join(self.capture_svg_title))
                self.capture_svg_title = None
            elif tag == "desc" and self.capture_svg_desc is not None:
                figure.svg_desc = normalize_text("".join(self.capture_svg_desc))
                self.capture_svg_desc = None
            elif tag == "figcaption" and self.capture_caption is not None:
                figure.caption = normalize_text("".join(self.capture_caption))
                self.capture_caption = None
            elif tag == "figure":
                self.figure_stack.pop()

    def handle_data(self, data: str) -> None:
        if self.in_style:
            self.style_parts.append(data)
        if self.in_title:
            self.title_parts.append(data)
        if self.meta_key is not None:
            self.meta_key.append(data)
        if self.meta_value is not None:
            self.meta_value.append(data)
        if self.capture_svg_title is not None:
            self.capture_svg_title.append(data)
        if self.capture_svg_desc is not None:
            self.capture_svg_desc.append(data)
        if self.capture_caption is not None:
            self.capture_caption.append(data)


def normalize_text(value: str) -> str:
    return " ".join(value.split()).strip()


def line_column(source: str, offset: int) -> tuple[int, int]:
    line = source.count("\n", 0, offset) + 1
    previous_newline = source.rfind("\n", 0, offset)
    column = offset + 1 if previous_newline < 0 else offset - previous_newline
    return line, column


def is_remote(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme.lower() in {"http", "https", "//"} or value.startswith("//")


def valid_iso(value: str) -> bool:
    candidate = value.strip()
    if not candidate or any(separator in candidate for separator in [",", ";"]):
        return False
    try:
        datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def compare_previous(current: PlanParser, previous: PlanParser, diagnostics: list[Diagnostic]) -> None:
    old_created = previous.metadata.get("created", "")
    new_created = current.metadata.get("created", "")
    if old_created and old_created != new_created:
        diagnostics.append(Diagnostic(1, 1, "PF3_CREATED_CHANGED", "created metadata must not change"))

    for key in REQUIRED_METADATA - {"created"}:
        old = previous.metadata.get(key, "")
        new = current.metadata.get(key, "")
        if old and old not in new:
            diagnostics.append(
                Diagnostic(1, 1, "PF3_METADATA_NOT_APPEND_ONLY", f"metadata row {key!r} lost prior content")
            )


def validate(path: Path, source: str, previous_path: Path | None) -> list[Diagnostic]:
    parser = PlanParser()
    parser.feed(source)
    parser.close()
    diagnostics = list(parser.diagnostics)

    for match in re.finditer(r"\{\{[\s\S]*?\}\}", source):
        line, column = line_column(source, match.start())
        token = normalize_text(match.group(0))[:80]
        diagnostics.append(Diagnostic(line, column, "PF3_PLACEHOLDER", f"unresolved placeholder {token}"))
    for match in re.finditer(r"<!--\s*repeat(?:\s*:.*?)?\s*-->", source, re.I | re.S):
        line, column = line_column(source, match.start())
        diagnostics.append(Diagnostic(line, column, "PF3_REPEAT_MARKER", "unresolved repeat marker"))

    missing_sections = sorted(REQUIRED_SECTIONS - parser.sections)
    for section in missing_sections:
        diagnostics.append(Diagnostic(1, 1, "PF3_SECTION_MISSING", f"missing required section id {section!r}"))
    if parser.style_count != 1:
        diagnostics.append(Diagnostic(1, 1, "PF3_STYLE_COUNT", f"expected exactly one <style> block; found {parser.style_count}"))
    if not normalize_text("".join(parser.title_parts)):
        diagnostics.append(Diagnostic(1, 1, "PF3_TITLE_EMPTY", "document <title> is empty"))

    css = "\n".join(parser.style_parts)
    for variable in sorted(REQUIRED_CSS_VARS):
        if not re.search(rf"{re.escape(variable)}\s*:", css):
            diagnostics.append(Diagnostic(1, 1, "PF3_CSS_VAR_MISSING", f"missing required CSS property {variable}"))
    for match in re.finditer(r"@import\b|url\(\s*['\"]?https?://", css, re.I):
        line, column = line_column(source, source.find(css) + match.start())
        diagnostics.append(Diagnostic(line, column, "PF3_REMOTE_CSS", "remote CSS resources are forbidden"))

    for resource, line, column in parser.resources:
        value = unquote(resource.strip())
        if is_remote(value):
            diagnostics.append(Diagnostic(line, column, "PF3_REMOTE_RESOURCE", f"remote resource is forbidden: {resource}"))

    missing_metadata = sorted(REQUIRED_METADATA - parser.metadata.keys())
    for key in missing_metadata:
        diagnostics.append(Diagnostic(1, 1, "PF3_METADATA_MISSING", f"missing metadata row {key!r}"))
    for key in sorted(REQUIRED_METADATA & parser.metadata.keys()):
        if not parser.metadata[key]:
            diagnostics.append(Diagnostic(1, 1, "PF3_METADATA_EMPTY", f"metadata row {key!r} is empty"))
    created = parser.metadata.get("created", "")
    if created and not valid_iso(created):
        diagnostics.append(Diagnostic(1, 1, "PF3_CREATED_INVALID", "created metadata must contain one ISO timestamp"))

    plan_root = path.parent.resolve()
    for figure in parser.figures:
        has_image = bool(figure.image_src)
        if not figure.has_svg and not has_image:
            diagnostics.append(Diagnostic(figure.line, figure.column, "PF3_FIGURE_EMPTY", "figure has no inline SVG or image"))
        if figure.has_svg:
            if not figure.svg_title:
                diagnostics.append(Diagnostic(figure.line, figure.column, "PF3_SVG_TITLE", "inline SVG has no non-empty <title>"))
            if not figure.svg_desc:
                diagnostics.append(Diagnostic(figure.line, figure.column, "PF3_SVG_DESC", "inline SVG has no non-empty <desc>"))
        if has_image:
            if figure.image_alt is None or not figure.image_alt.strip():
                diagnostics.append(Diagnostic(figure.line, figure.column, "PF3_IMAGE_ALT", "image has no non-empty alt text"))
            if not is_remote(figure.image_src) and not figure.image_src.startswith("data:"):
                candidate = (path.parent / unquote(figure.image_src)).resolve()
                try:
                    candidate.relative_to(plan_root)
                except ValueError:
                    diagnostics.append(Diagnostic(figure.line, figure.column, "PF3_IMAGE_ESCAPE", f"image path escapes plan directory: {figure.image_src}"))
                else:
                    if not candidate.is_file() or candidate.stat().st_size == 0:
                        diagnostics.append(Diagnostic(figure.line, figure.column, "PF3_IMAGE_MISSING", f"local image is missing or empty: {figure.image_src}"))
        if not figure.caption:
            diagnostics.append(Diagnostic(figure.line, figure.column, "PF3_FIGCAPTION", "figure has no non-empty figcaption"))

    if previous_path is not None:
        try:
            previous_source = previous_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ValueError(f"unable to read previous plan: {exc}") from exc
        previous = PlanParser()
        previous.feed(previous_source)
        previous.close()
        compare_previous(parser, previous, diagnostics)

    return sorted(diagnostics)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--previous", type=Path, help="Previous artifact for append-only checks")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()

    path = args.plan.expanduser().resolve()
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        print(f"VALIDATION ERROR: unable to read plan: {exc}", file=sys.stderr)
        return 2

    try:
        diagnostics = validate(path, source, args.previous.expanduser().resolve() if args.previous else None)
    except ValueError as exc:
        print(f"VALIDATION ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json_output:
        print(json.dumps({"ok": not diagnostics, "plan": str(path), "diagnostics": [asdict(item) for item in diagnostics]}, indent=2))
    else:
        for item in diagnostics:
            print(f"{item.code} {path}:{item.line}:{item.column} {item.message}", file=sys.stderr)
        if not diagnostics:
            print(f"VALID: {path}")

    return 1 if diagnostics else 0


if __name__ == "__main__":
    raise SystemExit(main())
