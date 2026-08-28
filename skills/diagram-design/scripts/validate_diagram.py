#!/usr/bin/env python3
"""Validate standalone Diagram Design HTML files and bundled assets."""

from __future__ import annotations

import argparse
import math
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree

TYPES = (
    "architecture",
    "er",
    "flowchart",
    "layers",
    "nested",
    "pyramid",
    "quadrant",
    "sequence",
    "state",
    "swimlane",
    "timeline",
    "tree",
    "venn",
)
SVG_NS = "{http://www.w3.org/2000/svg}"
XLINK_HREF = "{http://www.w3.org/1999/xlink}href"
RESOURCE_TAG_ATTRS = {
    "embed": ("src",),
    "iframe": ("src",),
    "image": ("href", "xlink:href"),
    "img": ("src", "srcset"),
    "link": ("href",),
    "object": ("data",),
    "script": ("src",),
    "source": ("src", "srcset"),
    "video": ("src", "poster"),
    "audio": ("src",),
}
PLACEHOLDER_PATTERNS = (
    re.compile(r"\{\{[\s\S]*?\}\}"),
    re.compile(r"\[(?:project name|diagram title|type|date|one-sentence[^\]]*)\]", re.I),
)


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    level: str
    code: str
    message: str


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.doctype = False
        self.html_lang = ""
        self.charset = ""
        self.viewport = ""
        self.title_parts: list[str] = []
        self.h1_parts: list[list[str]] = []
        self.main_count = 0
        self.svg_count = 0
        self.script_count = 0
        self.in_title = False
        self.current_h1: list[str] | None = None
        self.ids: list[str] = []
        self.resources: list[tuple[str, str, str]] = []
        self.style_parts: list[str] = []
        self.in_style = False

    def handle_decl(self, decl: str) -> None:
        if decl.lower().strip() == "doctype html":
            self.doctype = True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "html":
            self.html_lang = values.get("lang", "").strip()
        elif tag == "meta":
            if "charset" in values:
                self.charset = values["charset"].strip()
            if values.get("name", "").lower() == "viewport":
                self.viewport = values.get("content", "").strip()
        elif tag == "title":
            self.in_title = True
        elif tag == "h1":
            self.current_h1 = []
        elif tag == "main":
            self.main_count += 1
        elif tag == "svg":
            self.svg_count += 1
        elif tag == "style":
            self.in_style = True
        elif tag == "script":
            self.script_count += 1

        if values.get("id"):
            self.ids.append(values["id"])
        for attribute in RESOURCE_TAG_ATTRS.get(tag, ()):
            raw = values.get(attribute, "").strip()
            if raw:
                self.resources.append((tag, attribute, raw))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
        elif tag == "h1" and self.current_h1 is not None:
            self.h1_parts.append(self.current_h1)
            self.current_h1 = None
        elif tag == "style":
            self.in_style = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.current_h1 is not None:
            self.current_h1.append(data)
        if self.in_style:
            self.style_parts.append(data)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def normalize(value: str) -> str:
    return " ".join(value.split()).strip()


def is_remote(value: str) -> bool:
    parsed = urlparse(value.strip())
    return parsed.scheme.lower() in {"http", "https"} or value.startswith("//")


def numeric(value: str | None) -> float | None:
    if value is None or not re.fullmatch(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", value.strip()):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def points_bounds(value: str) -> tuple[float, float, float, float] | None:
    numbers = [float(item) for item in re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", value)]
    if len(numbers) < 4 or len(numbers) % 2 or not all(math.isfinite(item) for item in numbers):
        return None
    xs, ys = numbers[0::2], numbers[1::2]
    return min(xs), min(ys), max(xs), max(ys)


def geometry_bounds(element: ElementTree.Element) -> tuple[float, float, float, float] | None:
    name = local_name(element.tag)
    if name == "rect":
        x, y = numeric(element.get("x", "0")), numeric(element.get("y", "0"))
        width, height = numeric(element.get("width")), numeric(element.get("height"))
        if None not in (x, y, width, height) and width >= 0 and height >= 0:
            return x, y, x + width, y + height
    elif name == "circle":
        cx, cy, radius = numeric(element.get("cx", "0")), numeric(element.get("cy", "0")), numeric(element.get("r"))
        if None not in (cx, cy, radius) and radius >= 0:
            return cx - radius, cy - radius, cx + radius, cy + radius
    elif name == "ellipse":
        cx, cy = numeric(element.get("cx", "0")), numeric(element.get("cy", "0"))
        rx, ry = numeric(element.get("rx")), numeric(element.get("ry"))
        if None not in (cx, cy, rx, ry) and rx >= 0 and ry >= 0:
            return cx - rx, cy - ry, cx + rx, cy + ry
    elif name == "line":
        values = [numeric(element.get(key, "0")) for key in ("x1", "y1", "x2", "y2")]
        if all(value is not None for value in values):
            x1, y1, x2, y2 = values
            return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)
    elif name in {"polyline", "polygon"}:
        return points_bounds(element.get("points", ""))
    return None


def outside(bounds: tuple[float, float, float, float], viewbox: tuple[float, float, float, float], epsilon: float = 0.01) -> bool:
    x0, y0, x1, y1 = bounds
    vx, vy, width, height = viewbox
    return x0 < vx - epsilon or y0 < vy - epsilon or x1 > vx + width + epsilon or y1 > vy + height + epsilon


def expected_inventory() -> set[str]:
    names = {"index.html", "template.html", "template-dark.html", "template-full.html", "example-quadrant-consultant.html"}
    for diagram_type in TYPES:
        names.add(f"example-{diagram_type}.html")
        names.add(f"example-{diagram_type}-dark.html")
        names.add(f"example-{diagram_type}-full.html")
    return names


def validate_svg(path: Path, source: str, findings: list[Finding]) -> None:
    matches = list(re.finditer(r"<svg\b[\s\S]*?</svg>", source, re.I))
    if len(matches) != 1:
        findings.append(Finding(str(path), "error", "DD_SVG_COUNT", f"expected exactly one inline SVG; found {len(matches)}"))
        return
    svg_source = matches[0].group(0)
    try:
        root = ElementTree.fromstring(svg_source)
    except ElementTree.ParseError as exc:
        findings.append(Finding(str(path), "error", "DD_SVG_XML", str(exc)))
        return

    raw_viewbox = root.get("viewBox", "").split()
    viewbox: tuple[float, float, float, float] | None = None
    if len(raw_viewbox) == 4:
        try:
            parsed = tuple(float(item) for item in raw_viewbox)
            if all(math.isfinite(item) for item in parsed) and parsed[2] > 0 and parsed[3] > 0:
                viewbox = parsed
        except ValueError:
            pass
    if viewbox is None:
        findings.append(Finding(str(path), "error", "DD_VIEWBOX", "SVG viewBox must contain four finite numbers with positive width and height"))

    if root.get("role") != "img":
        findings.append(Finding(str(path), "error", "DD_SVG_ROLE", "SVG must use role=\"img\""))

    ids: dict[str, ElementTree.Element] = {}
    duplicates: set[str] = set()
    for element in root.iter():
        element_id = element.get("id")
        if element_id:
            if element_id in ids:
                duplicates.add(element_id)
            ids[element_id] = element
    for element_id in sorted(duplicates):
        findings.append(Finding(str(path), "error", "DD_DUPLICATE_ID", f"duplicate SVG id {element_id!r}"))

    title = next((child for child in root if local_name(child.tag) == "title"), None)
    desc = next((child for child in root if local_name(child.tag) == "desc"), None)
    if title is None or not normalize("".join(title.itertext())):
        findings.append(Finding(str(path), "error", "DD_SVG_TITLE", "SVG needs a non-empty direct <title>"))
    if desc is None or not normalize("".join(desc.itertext())):
        findings.append(Finding(str(path), "error", "DD_SVG_DESC", "SVG needs a non-empty direct <desc>"))

    labelled = root.get("aria-labelledby", "").split()
    required_ids = [element.get("id", "") if element is not None else "" for element in (title, desc)]
    if not all(required_ids) or not all(element_id in labelled for element_id in required_ids):
        findings.append(Finding(str(path), "error", "DD_ARIA_LABELLED", "aria-labelledby must reference the SVG title and description IDs"))

    references: set[str] = set(labelled)
    for element in root.iter():
        for key, value in element.attrib.items():
            for match in re.finditer(r"url\(#([^)]+)\)", value):
                references.add(match.group(1))
            if local_name(key) in {"href", "aria-describedby", "aria-labelledby"}:
                for token in value.split():
                    if token.startswith("#"):
                        references.add(token[1:])
                    elif local_name(element.tag) in {"image", "use"} and is_remote(token):
                        findings.append(Finding(str(path), "error", "DD_REMOTE_SVG_RESOURCE", f"remote SVG reference {token!r}"))
    for reference in sorted(references):
        if reference and reference not in ids:
            findings.append(Finding(str(path), "error", "DD_BROKEN_REFERENCE", f"unresolved SVG reference {reference!r}"))

    if viewbox is not None:
        ignored_ancestors = {"defs", "marker", "pattern", "clipPath", "mask", "filter", "symbol"}
        def walk(element: ElementTree.Element, transformed: bool = False, ignored: bool = False) -> None:
            name = local_name(element.tag)
            transformed = transformed or bool(element.get("transform"))
            ignored = ignored or name in ignored_ancestors
            if not transformed and not ignored:
                bounds = geometry_bounds(element)
                if bounds is not None and outside(bounds, viewbox):
                    findings.append(Finding(str(path), "error", "DD_OUT_OF_VIEWBOX", f"<{name}> with bounds {bounds} lies outside viewBox {viewbox}"))
            for child in element:
                walk(child, transformed, ignored)
        walk(root)


def validate_file(path: Path, *, gallery: bool, template: bool) -> list[Finding]:
    findings: list[Finding] = []
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [Finding(str(path), "error", "DD_READ", str(exc))]

    parser = DocumentParser()
    try:
        parser.feed(source)
        parser.close()
    except Exception as exc:
        findings.append(Finding(str(path), "error", "DD_HTML_PARSE", str(exc)))
        return findings

    if not parser.doctype:
        findings.append(Finding(str(path), "error", "DD_DOCTYPE", "missing <!DOCTYPE html>"))
    if not parser.html_lang:
        findings.append(Finding(str(path), "error", "DD_LANG", "missing html lang attribute"))
    if parser.charset.lower().replace("-", "") != "utf8":
        findings.append(Finding(str(path), "error", "DD_CHARSET", "missing UTF-8 charset"))
    if not parser.viewport:
        findings.append(Finding(str(path), "error", "DD_VIEWPORT_META", "missing viewport metadata"))
    if not normalize("".join(parser.title_parts)):
        findings.append(Finding(str(path), "error", "DD_DOCUMENT_TITLE", "document title is empty"))
    if parser.main_count != 1:
        findings.append(Finding(str(path), "error", "DD_MAIN_COUNT", f"expected one <main>; found {parser.main_count}"))
    nonempty_h1 = [parts for parts in parser.h1_parts if normalize("".join(parts))]
    if len(nonempty_h1) != 1:
        findings.append(Finding(str(path), "error", "DD_H1_COUNT", f"expected one non-empty h1; found {len(nonempty_h1)}"))

    duplicates = sorted({element_id for element_id in parser.ids if parser.ids.count(element_id) > 1})
    for element_id in duplicates:
        findings.append(Finding(str(path), "error", "DD_DUPLICATE_HTML_ID", f"duplicate HTML id {element_id!r}"))

    css = "\n".join(parser.style_parts)
    if re.search(r"@import\b", css, re.I):
        findings.append(Finding(str(path), "error", "DD_CSS_IMPORT", "CSS @import is forbidden"))
    for match in re.finditer(r"url\(\s*['\"]?([^)'\"]+)", css, re.I):
        value = match.group(1).strip()
        if not value.startswith("#") and not value.startswith("data:"):
            findings.append(Finding(str(path), "error", "DD_CSS_RESOURCE", f"CSS resource is not embedded: {value!r}"))

    for tag, attribute, raw in parser.resources:
        values = [raw]
        if attribute == "srcset":
            values = [part.strip().split()[0] for part in raw.split(",") if part.strip()]
        for value in values:
            if is_remote(value):
                findings.append(Finding(str(path), "error", "DD_REMOTE_RESOURCE", f"network-loaded {tag} {attribute}={value!r}"))
            elif gallery and tag == "iframe":
                candidate = (path.parent / unquote(value)).resolve()
                try:
                    candidate.relative_to(path.parent.resolve())
                except ValueError:
                    findings.append(Finding(str(path), "error", "DD_GALLERY_ESCAPE", f"gallery path escapes assets: {value!r}"))
                else:
                    if not candidate.is_file():
                        findings.append(Finding(str(path), "error", "DD_GALLERY_MISSING", f"gallery target does not exist: {value!r}"))
            elif not gallery and tag in RESOURCE_TAG_ATTRS:
                findings.append(Finding(str(path), "error", "DD_EXTERNAL_ELEMENT", f"standalone diagrams may not load <{tag}> resources"))

    if not template:
        for pattern in PLACEHOLDER_PATTERNS:
            if pattern.search(source):
                findings.append(Finding(str(path), "error", "DD_PLACEHOLDER", "unresolved template placeholder"))
                break

    if gallery:
        if parser.svg_count != 0:
            findings.append(Finding(str(path), "error", "DD_GALLERY_SVG", "gallery must not contain a diagram SVG"))
        for referenced in sorted(set(re.findall(r"example-[a-z0-9-]+\.html", source))):
            if not (path.parent / referenced).is_file():
                findings.append(Finding(str(path), "error", "DD_GALLERY_MISSING", f"gallery references missing file {referenced!r}"))
    else:
        if parser.script_count:
            findings.append(Finding(str(path), "error", "DD_SCRIPT", "standalone diagrams may not contain scripts"))
        validate_svg(path, source, findings)
        findings.append(Finding(str(path), "manual", "DD_VISUAL_REVIEW", "render and inspect text fit, clipping, overlap, contrast, and reading order"))

    return sorted(set(findings))


def validate_package(directory: Path) -> list[Finding]:
    findings: list[Finding] = []
    actual = {path.name for path in directory.glob("*.html")}
    expected = expected_inventory()
    for name in sorted(expected - actual):
        findings.append(Finding(str(directory), "error", "DD_INVENTORY_MISSING", f"missing bundled asset {name}"))
    for name in sorted(actual - expected):
        findings.append(Finding(str(directory), "error", "DD_INVENTORY_EXTRA", f"unexpected bundled asset {name}"))
    for name in sorted(actual & expected):
        findings.extend(validate_file(directory / name, gallery=name == "index.html", template=name.startswith("template")))
    return sorted(set(findings))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("diagram", nargs="?", type=Path, help="Generated standalone HTML diagram")
    target.add_argument("--package", type=Path, help="Bundled assets directory")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--template", action="store_true", help="Allow declared template placeholders")
    args = parser.parse_args()

    if args.package:
        directory = args.package.expanduser().resolve()
        if not directory.is_dir():
            print(f"VALIDATION ERROR: package directory does not exist: {directory}", file=sys.stderr)
            return 2
        findings = validate_package(directory)
    else:
        path = args.diagram.expanduser().resolve()
        if not path.is_file():
            print(f"VALIDATION ERROR: diagram does not exist: {path}", file=sys.stderr)
            return 2
        findings = validate_file(path, gallery=False, template=args.template)

    for finding in findings:
        stream = sys.stderr if finding.level in {"error", "warning"} else sys.stdout
        print(f"{finding.level.upper()} {finding.code} {finding.path}: {finding.message}", file=stream)

    errors = sum(finding.level == "error" for finding in findings)
    warnings = sum(finding.level == "warning" for finding in findings)
    manual = sum(finding.level == "manual" for finding in findings)
    if errors or (args.strict and warnings):
        print(f"FAIL: {errors} error(s), {warnings} warning(s), {manual} manual check(s)", file=sys.stderr)
        return 1
    print(f"PASS: {errors} error(s), {warnings} warning(s), {manual} manual check(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
