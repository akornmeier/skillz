#!/usr/bin/env python3
"""Check Plan F3 structure and references, not semantic correctness or executed evidence.

Errors fail by default. Warnings flag completion markers without current evidence and, with
--repo-root, listed existing files missing from disk; --strict fails on warnings too. With
--previous, metadata, prior amendments, and acceptance criteria are checked for silent rewrites.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

REQUIRED_SECTIONS = {
    "purpose",
    "problem",
    "solution",
    "acceptance",
    "coverage",
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
# HTML void elements never own descendants in the contract tree.
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


@dataclass(order=True)
class Diagnostic:
    line: int
    column: int
    code: str
    message: str
    severity: str = "error"


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


@dataclass(eq=False)
class Element:
    tag: str
    attrs: dict[str, str]
    line: int
    column: int
    parent: Element | None
    text_parts: list[str] = field(default_factory=list)
    nested_list_at: int | None = None  # len(text_parts) when the first nested ul/ol opened

    @property
    def classes(self) -> set[str]:
        return set(self.attrs.get("class", "").split())

    @property
    def text(self) -> str:
        return normalize_text("".join(self.text_parts))

    def within(self, ancestor: Element | None) -> bool:
        parent = self.parent
        while parent is not None:
            if parent is ancestor:
                return True
            parent = parent.parent
        return False


class PlanParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.diagnostics: list[Diagnostic] = []
        self.ids: dict[str, tuple[int, int]] = {}
        self.sections: set[str] = set()
        self.elements: list[Element] = []
        self.element_stack: list[Element] = []
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

    def close_implied_elements(self, tag: str) -> None:
        """Close optional list/table siblings without crossing a nested container."""
        if tag in {"dt", "dd"}:
            siblings, boundaries = {"dt", "dd"}, {"dl", "table", "td", "th", "html"}
        elif tag == "li":
            siblings, boundaries = {"li"}, {"ul", "ol", "menu", "table", "html"}
        elif tag in {"td", "th"}:
            siblings, boundaries = {"td", "th"}, {"tr", "table", "html"}
        elif tag == "tr":
            siblings, boundaries = {"tr"}, {"table", "html"}
        elif tag in {"thead", "tbody", "tfoot"}:
            siblings, boundaries = {"thead", "tbody", "tfoot"}, {"table", "html"}
        else:
            return
        for element in reversed(self.element_stack):
            if element.tag in siblings:
                self.handle_endtag(element.tag)
                break
            if element.tag in boundaries:
                break

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        self.close_implied_elements(tag)
        values = self.attrs_dict(attrs)
        line, column = self.getpos()
        if tag in {"ul", "ol"}:
            for ancestor in self.element_stack:
                if ancestor.nested_list_at is None:
                    ancestor.nested_list_at = len(ancestor.text_parts)
        element = Element(tag, values, line, column + 1, self.element_stack[-1] if self.element_stack else None)
        self.elements.append(element)
        if tag not in VOID_TAGS:
            self.element_stack.append(element)

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
        elif self.in_meta and tag not in VOID_TAGS:
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
        for index in range(len(self.element_stack) - 1, -1, -1):
            if self.element_stack[index].tag == tag:
                # Finalize captures for omitted child end tags before closing their parent.
                while len(self.element_stack) > index + 1:
                    self.handle_endtag(self.element_stack[-1].tag)
                self.element_stack.pop()
                break
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
        elif self.in_meta and tag not in VOID_TAGS:
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
        for element in self.element_stack:
            element.text_parts.append(data)
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


STATUS_TOKEN = re.compile(r"\[(|wip|x|f)\]", re.I)
CRITERION_ID = re.compile(r"(?<![\w-])ac-[^\s,;]+")
UNPROVEN_EVIDENCE = ("not run", "stale:", "deferred:")


def own_status(parser: PlanParser, element: Element | None) -> str:
    """Return the element's own status ('', 'wip', 'x', 'f'), or 'unmarked', ignoring nested list items."""
    if element is None:
        return "unmarked"
    for candidate in parser.elements:
        if candidate.tag == "code" and "status" in candidate.classes and candidate.within(element):
            if element.tag == "li" and nearest(candidate, {"li"}) is not element:
                continue
            match = STATUS_TOKEN.fullmatch(candidate.text)
            if match:
                return match.group(1).lower()
            break
    own = element.text_parts[:element.nested_list_at] if element.tag == "li" else element.text_parts
    match = STATUS_TOKEN.match(normalize_text("".join(own)))
    return match.group(1).lower() if match else "unmarked"


def nearest(element: Element, tags: set[str]) -> Element | None:
    parent = element.parent
    while parent is not None and parent.tag not in tags:
        parent = parent.parent
    return parent


def first_descendant(parser: PlanParser, ancestor: Element, tag: str) -> Element | None:
    return next((element for element in parser.elements if element.tag == tag and element.within(ancestor)), None)


def task_status(parser: PlanParser, task: Element) -> str:
    return own_status(parser, first_descendant(parser, task, "h4"))


def validate_engineering_contract(parser: PlanParser) -> list[Diagnostic]:
    """Check declared coverage and verification shape without judging their meaning."""
    diagnostics: list[Diagnostic] = []
    elements = parser.elements
    by_id = {element.attrs["id"]: element for element in elements if element.attrs.get("id")}
    criteria = [element for element in elements if "criterion" in element.classes]
    tasks = [element for element in elements if "task" in element.classes]
    verifications = [element for element in elements if "verification" in element.classes]

    def report(element: Element, code: str, message: str, severity: str = "error") -> None:
        diagnostics.append(Diagnostic(element.line, element.column, code, message, severity))

    for kind, definitions, prefix, section in (
        ("criterion", criteria, "ac-", "acceptance"),
        ("task", tasks, "task-", "phases"),
        ("verification", verifications, "verify-", "phases"),
    ):
        for element in definitions:
            identifier = element.attrs.get("id", "")
            if not identifier.startswith(prefix) or len(identifier) == len(prefix) or re.search(r"\s", identifier):
                report(element, "PF3_CONTRACT_ID", f"{kind} needs a unique id beginning with {prefix!r}")
            if not element.within(by_id.get(section)):
                report(element, "PF3_CONTRACT_LOCATION", f"{kind} {identifier!r} must be inside section {section!r}")
            if not element.text:
                report(element, "PF3_CONTRACT_EMPTY", f"{kind} {identifier!r} has no content")

    if not criteria:
        diagnostics.append(Diagnostic(1, 1, "PF3_CRITERIA_MISSING", "add at least one .criterion with an ac-* id inside acceptance"))
    if not tasks:
        diagnostics.append(Diagnostic(1, 1, "PF3_TASKS_MISSING", "add at least one .task with a task-* id inside phases"))

    owners = {verification: next((task for task in reversed(tasks) if verification.within(task)), None)
              for verification in verifications}
    for verification, owner in owners.items():
        if owner is None:
            report(verification, "PF3_VERIFICATION_OWNER", "verification must be nested inside its owning .task")
        done = owner is not None and task_status(parser, owner) == "x"
        for name in ("cases", "command", "expected", "evidence"):
            fields = [element for element in elements
                      if element.tag == "dd" and name in element.classes and element.within(verification)]
            label = verification.attrs.get("id", "")
            if name == "evidence" and done and len(fields) == 1 and (
                    not fields[0].text or fields[0].text.lower().startswith(UNPROVEN_EVIDENCE)):
                # Warning, not error, so repair workflows can still run on hand-ticked tasks.
                report(verification, "PF3_DONE_WITHOUT_EVIDENCE",
                       f"task marked [x] but verification {label!r} has no current evidence", "warning")
            elif len(fields) != 1 or not fields[0].text:
                report(verification, "PF3_VERIFICATION_FIELD",
                       f"verification {label!r} needs exactly one non-empty dd.{name}")
    for task in tasks:
        if task not in owners.values():
            report(task, "PF3_TASK_VERIFICATION", f"task {task.attrs.get('id', '')!r} needs its own .verification block")

    links = [element for element in elements if element.tag == "a" and element.attrs.get("href", "").startswith("#")]
    for link in links:
        target = unquote(link.attrs["href"][1:])
        if target and target not in by_id:
            report(link, "PF3_REFERENCE_MISSING", f"fragment target {target!r} does not exist; repair the href or define its id")

    coverage = by_id.get("coverage")
    bodies = [element for element in elements if element.tag == "tbody" and element.within(coverage)]
    rows = [element for element in elements if element.tag == "tr" and any(element.within(body) for body in bodies)]
    if not rows:
        diagnostics.append(Diagnostic(1, 1, "PF3_COVERAGE_MISSING", "coverage needs a table tbody with criterion/task/verification links in each row"))
    mapped_criteria: set[Element] = set()
    mapped_tasks: set[Element] = set()
    for row in rows:
        targets = {by_id.get(unquote(link.attrs["href"][1:])) for link in links if link.within(row)}
        row_criteria = targets.intersection(criteria)
        row_tasks = targets.intersection(tasks)
        row_verifications = targets.intersection(verifications)
        if len(row_criteria) != 1 or not row_tasks or not row_verifications:
            report(row, "PF3_COVERAGE_ROW", "coverage row needs links to exactly one criterion, at least one task, and at least one verification")
        for verification in row_verifications:
            if owners[verification] not in row_tasks:
                report(row, "PF3_COVERAGE_OWNER", f"verification {verification.attrs.get('id', '')!r} belongs to a task not linked in this row")
        mapped_criteria.update(row_criteria)
        mapped_tasks.update(row_tasks)
    for criterion in criteria:
        if criterion not in mapped_criteria:
            report(criterion, "PF3_CRITERION_UNCOVERED", f"criterion {criterion.attrs.get('id', '')!r} needs a coverage row")
    for task in tasks:
        if task not in mapped_tasks:
            report(task, "PF3_TASK_UNCOVERED", f"task {task.attrs.get('id', '')!r} needs a coverage link to the criterion it serves")

    for phase in (element for element in elements if "phase" in element.classes):
        if own_status(parser, first_descendant(parser, phase, "h3")) != "x":
            continue
        unfinished = [task for task in tasks if task.within(phase) and task_status(parser, task) != "x"]
        unfinished += [item for item in elements if item.tag == "li" and item.within(phase)
                       and item.parent is not None and item.parent.tag == "ul"
                       and "checklist" in item.parent.classes and own_status(parser, item) != "x"]
        if unfinished:
            report(phase, "PF3_PHASE_PREMATURE_DONE",
                   f"phase marked [x] with {len(unfinished)} task(s) or checklist item(s) not marked [x]", "warning")
    return diagnostics


def check_existing_files(parser: PlanParser, repo_root: Path) -> list[Diagnostic]:
    """Check the first path span of each existing-file row; missing files only warn once a build has started."""
    diagnostics: list[Diagnostic] = []
    elements = parser.elements
    files = next((element for element in elements if element.attrs.get("id") == "files"), None)
    if files is None:
        return diagnostics
    started = any(task_status(parser, task) in {"wip", "x", "f"}
                  for task in elements if "task" in task.classes)
    severity = "warning" if started else "error"
    root = repo_root.resolve()
    for row in elements:
        if row.tag != "li" or not row.within(files):
            continue
        if not any(span.tag == "span" and {"tag", "existing"} <= span.classes and span.within(row) for span in elements):
            continue
        code = first_descendant(parser, row, "code")
        token = code.text if code is not None else ""
        if not token or is_remote(token) or any(marker in token for marker in ("*", "<", ">", "{", "...")):
            continue
        candidate = (root / token).resolve()
        try:
            candidate.relative_to(root)
            escaped = False
        except ValueError:
            escaped = True
        if escaped or not candidate.exists():
            reason = "escapes the repository root" if escaped else "does not exist"
            diagnostics.append(Diagnostic(row.line, row.column, "PF3_EXISTING_FILE_MISSING",
                                          f"existing file {token!r} {reason}", severity))
    return diagnostics


def criteria_text(parser: PlanParser) -> dict[str, str]:
    return {element.attrs.get("id", ""): element.text for element in parser.elements if "criterion" in element.classes}


def amendment_entries(parser: PlanParser) -> list[tuple[str, str, str]]:
    """Return (full text, header, body) per amendment in order; header/body keep word breaks across tags."""
    section = next((element for element in parser.elements
                    if element.tag == "section" and element.attrs.get("id") == "amendments"), None)
    if section is None:
        return []
    entries = []
    for details in (element for element in parser.elements if element.tag == "details" and element.within(section)):
        summary = first_descendant(parser, details, "summary")
        spaced = normalize_text(" ".join(details.text_parts))
        header = normalize_text(" ".join(summary.text_parts)) if summary is not None else ""
        body = spaced[len(header):] if header and spaced.startswith(header) else spaced
        entries.append((details.text, header, body))
    return entries


def compare_previous(current: PlanParser, previous: PlanParser, diagnostics: list[Diagnostic]) -> None:
    old_amendments = amendment_entries(previous)
    new_amendments = amendment_entries(current)
    if [entry[0] for entry in new_amendments[:len(old_amendments)]] != [entry[0] for entry in old_amendments]:
        diagnostics.append(Diagnostic(1, 1, "PF3_AMENDMENT_REWRITTEN",
                                      "prior amendments must stay unchanged and in order; append new entries at the bottom"))
    appended = new_amendments[len(old_amendments):]
    new_criteria = criteria_text(current)
    for identifier, old_text in criteria_text(previous).items():
        if new_criteria.get(identifier) == old_text:
            continue
        token = re.compile(rf"(?<![\w-]){re.escape(identifier)}(?![\w-])")
        if not any((token.search(header) or token.search(body)) and re.search(r"[A-Za-z0-9]", CRITERION_ID.sub("", body))
                   for _, header, body in appended):
            change = "removed" if identifier not in new_criteria else "changed"
            diagnostics.append(Diagnostic(1, 1, "PF3_AC_MUTATED",
                                          f"criterion {identifier!r} {change} without a newly appended amendment naming it with a rationale"))

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


def validate(path: Path, source: str, previous_path: Path | None, repo_root: Path | None = None) -> list[Diagnostic]:
    parser = PlanParser()
    parser.feed(source)
    parser.close()
    diagnostics = list(parser.diagnostics)
    diagnostics.extend(validate_engineering_contract(parser))

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

    if repo_root is not None:
        diagnostics.extend(check_existing_files(parser, repo_root))

    return sorted(diagnostics)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--previous", type=Path, help="Previous artifact for append-only checks")
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--repo-root", type=Path, help="Check that files tagged existing are present under this root")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings as well as errors")
    args = parser.parse_args()

    path = args.plan.expanduser().resolve()
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        print(f"VALIDATION ERROR: unable to read plan: {exc}", file=sys.stderr)
        return 2

    repo_root = args.repo_root.expanduser().resolve() if args.repo_root else None
    if repo_root is not None and not repo_root.is_dir():
        print(f"VALIDATION ERROR: repo root is not a directory: {repo_root}", file=sys.stderr)
        return 2
    try:
        diagnostics = validate(path, source, args.previous.expanduser().resolve() if args.previous else None, repo_root)
    except ValueError as exc:
        print(f"VALIDATION ERROR: {exc}", file=sys.stderr)
        return 2

    warnings = sum(item.severity == "warning" for item in diagnostics)
    failed = any(item.severity == "error" for item in diagnostics) or (args.strict and bool(diagnostics))
    exit_code = 1 if failed else 0
    if args.json_output:
        print(json.dumps({"ok": exit_code == 0, "plan": str(path), "diagnostics": [asdict(item) for item in diagnostics]}, indent=2))
    else:
        for item in diagnostics:
            print(f"{item.code} {path}:{item.line}:{item.column} {item.severity}: {item.message}", file=sys.stderr)
        if exit_code == 0:
            suffix = f" ({warnings} warning{'s' if warnings != 1 else ''})" if warnings else ""
            print(f"STRUCTURALLY VALID{suffix}: {path} (semantic review and execution evidence still require human/agent checks)")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
