#!/usr/bin/env python3
"""Parse a project's specs/COURSE.md into milestones, maps, decisions, and accepted constraints.

Single owner of COURSE.md parsing for check_drift.py and spec_guard.py. Only accepted text carries
authority: governed prose is accepted unless marked "Inferred — needs developer review" or inside a
"> PROPOSED" block; Decision Log rows are accepted only with Status: Accepted. Standard library only.
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

INFERRED = re.compile(r"inferred\s*[—–-]+\s*needs developer review", re.I)
HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$")
FENCE = re.compile(r"^\s*(```|~~~)")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
CODE_SPAN = re.compile(r"`([^`]+)`")
DECISION_ID = re.compile(r"\bD-\d{3,}\b")
SUPERSEDED = re.compile(r"superseded\s+by\s+(D-\d{3,})", re.I)
ACCEPTED = re.compile(r"^\s*(?:status\s*:\s*)?accepted\b", re.I)
VERIFIED = re.compile(r"^\s*verified\s*:\s*(\d{4}-\d{2}-\d{2})(?:\s*\(\s*([^)\s]+)\s*\))?", re.I | re.M)
PATH_EXTENSION = re.compile(r"\.(?=[A-Za-z0-9]{0,4}[A-Za-z])[A-Za-z0-9]{1,5}$")
EXTERNAL = re.compile(r"^(?:/|~|[A-Za-z]:)")
URL = re.compile(r"^[a-z][a-z0-9+.-]*:", re.I)
EMPTY_CELLS = {"", "—", "–", "-", "none", "tbd", "n/a"}

SECTIONS = (
    ("north_star", ("north star",)),
    ("milestones", ("milestone",)),
    ("non_goals", ("non-goal", "non goal", "nongoal")),
    ("protected_boundaries", ("protected",)),
    ("precedence", ("precedence",)),
    ("area_map", ("area",)),
    ("decision_log", ("decision",)),
    ("proposals", ("proposal",)),
    ("glossary", ("glossary",)),
)
GOVERNED = ("north_star", "precedence", "protected_boundaries", "non_goals")


@dataclass
class Course:
    milestones: list = field(default_factory=list)
    area_map: list = field(default_factory=list)
    decisions: list = field(default_factory=list)
    proposals: list = field(default_factory=list)
    unsupported_boundaries: list = field(default_factory=list)
    accepted: dict = field(default_factory=dict)
    verified: Optional[dict] = None


def normalize(value: str) -> str:
    return " ".join(value.split()).strip()


def section_key(title: str) -> str | None:
    lowered = title.lower()
    for key, needles in SECTIONS:
        if any(needle in lowered for needle in needles):
            return key
    return None


def split_row(line: str) -> list[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    return [normalize(cell.replace("\\|", "|")) for cell in re.split(r"(?<!\\)\|", body)]


def is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def plain(cell: str) -> str:
    """Strip Markdown emphasis and code ticks from a table cell."""
    return normalize(re.sub(r"[`*_]", "", cell))


def path_tokens(text: str) -> list[str]:
    """Repo-relative path tokens: contain '/', end in '/' or a short extension; skip URLs, patterns, externals."""
    text = MD_LINK.sub(lambda match: f" {match.group(1)} ", text)
    tokens = []
    for raw in re.split(r"[\s`]+", text):
        token = raw.strip("\"'()[]<>{},;:!?")
        token = token.rstrip(".") if not token.endswith("/") else token
        if "/" not in token or URL.match(token) or EXTERNAL.match(token):
            continue
        if any(marker in token for marker in ("*", "<", ">", "{", "...")) or re.fullmatch(r"#\d+", token):
            continue
        if token.endswith("/") or PATH_EXTENSION.search(token):
            tokens.append(token)
    return tokens


def adr_links(text: str) -> list[str]:
    """Decision Log links: Markdown link targets and .md path tokens, never other paths named in prose."""
    links = [path for match in MD_LINK.finditer(text) for path in path_tokens(match.group(1))]
    links += [path for path in path_tokens(MD_LINK.sub(" ", text)) if path.lower().endswith(".md")]
    return list(dict.fromkeys(links))


def match_protected_path(changed_path: str, boundary: str) -> bool:
    """Globs match via fnmatch; 'dir/' matches by prefix; bare entries match the file or its subtree."""
    changed = changed_path.lstrip("/")
    if any(char in boundary for char in "*?["):
        return fnmatch.fnmatchcase(changed, boundary)
    if boundary.endswith("/"):
        return changed == boundary.rstrip("/") or changed.startswith(boundary)
    return changed == boundary or changed.startswith(boundary + "/")


def boundary_spans(text: str) -> tuple[list[str], list[dict]]:
    boundaries, unsupported = [], []
    for match in CODE_SPAN.finditer(text):
        span = match.group(1).strip()
        if URL.match(span) or span.startswith("//"):
            unsupported.append({"span": span, "reason": "url"})
            continue
        if span.startswith("~") or re.match(r"^[A-Za-z]:", span):
            unsupported.append({"span": span, "reason": "external path"})
            continue
        path = span[1:] if span.startswith("/") else span
        if not path or re.search(r"\s", path) or ".." in path.split("/"):
            unsupported.append({"span": span, "reason": "not a repo-relative path"})
            continue
        boundaries.append(path)
    return boundaries, unsupported


def table_rows(lines: list[tuple[int, str]]) -> list[tuple[int, dict]]:
    """Parse the first pipe table in lines into (line number, {header: cell}) rows."""
    rows, header = [], None
    for number, line in lines:
        if not line.lstrip().startswith("|"):
            if header is not None and rows:
                break
            continue
        cells = split_row(line)
        if header is None:
            header = [plain(cell).lower() for cell in cells]
        elif is_separator(cells):
            continue
        else:
            rows.append((number, {header[i] if i < len(header) else f"col{i}": cell for i, cell in enumerate(cells)}))
    return rows


def column(row: dict, *names: str) -> str:
    for key, value in row.items():
        if any(key.startswith(name) for name in names):
            return value
    return ""


def items_and_proposals(lines: list[tuple[int, str]]) -> tuple[list[dict], list[dict]]:
    """Split section lines into list items, paragraphs, and table rows; peel off PROPOSED blockquotes."""
    items, proposals, current, quote = [], [], None, None

    def close() -> None:
        nonlocal current, quote
        if quote is not None:
            text = normalize(" ".join(quote["parts"]))
            if re.match(r"^proposed\b", text, re.I):
                proposals.append({"line": quote["line"], "text": text})
            else:
                items.append({"line": quote["line"], "text": text})
        if current is not None:
            items.append({"line": current["line"], "text": normalize(" ".join(current["parts"]))})
        current, quote = None, None

    in_table = False
    for number, line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--"):
            close()
            in_table = False
            continue
        if stripped.startswith(">"):
            if current is not None:
                close()
            content = stripped.lstrip(">").strip()
            if quote is None:
                quote = {"line": number, "parts": []}
            elif re.match(r"^proposed\b", content, re.I):
                close()
                quote = {"line": number, "parts": []}
            quote["parts"].append(content)
            continue
        if quote is not None:
            close()
        if stripped.startswith("|"):
            close()
            cells = split_row(stripped)
            if not in_table:
                in_table = True  # header row describes columns, not content
                continue
            if not is_separator(cells):
                items.append({"line": number, "text": " | ".join(cells)})
            continue
        in_table = False
        list_match = LIST_ITEM.match(line)
        if list_match:
            close()
            current = {"line": number, "parts": [list_match.group(1)]}
        elif current is None:
            current = {"line": number, "parts": [stripped]}
        else:
            current["parts"].append(stripped)
    close()
    return items, proposals


def adr_status(paths: list[str], reader: Callable[[str], Optional[str]] | None) -> bool:
    if not paths or reader is None:
        return False
    for path in paths:
        text = reader(path)
        if text is None or re.search(r"superseded", text, re.I):
            return False
        if not re.search(r"^\W*status\W*:?\W*accepted\b", text, re.I | re.M):
            return False
    return True


def parse_course(text: str, repo_root: Path | str | None = None,
                 read_file: Callable[[str], Optional[str]] | None = None) -> Course:
    """Parse COURSE.md text. read_file(path) supplies linked-ADR text (for example from a git blob)."""
    if read_file is None and repo_root is not None:
        root = Path(repo_root)

        def read_file(path: str) -> Optional[str]:
            try:
                return (root / path).read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                return None

    sections: dict[str, list[tuple[int, str]]] = {}
    inferred_sections: set[str] = set()
    current, fenced = None, False
    for number, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        heading = HEADING.match(line)
        if heading:
            key = section_key(heading.group(2))
            if key is not None or len(heading.group(1)) <= 2:
                current = key
            if key is not None and INFERRED.search(heading.group(2)):
                inferred_sections.add(key)
            continue
        if current is not None:
            sections.setdefault(current, []).append((number, line))

    course = Course()
    verified = VERIFIED.search(text)
    if verified:
        course.verified = {"date": verified.group(1), "commit": verified.group(2)}

    accepted: dict = {key: [] for key in GOVERNED}
    for key, lines in sections.items():
        items, proposals = items_and_proposals(lines)
        course.proposals.extend(dict(proposal, section=key) for proposal in proposals)
        if key not in GOVERNED:
            continue
        for item in items:
            if key in inferred_sections or INFERRED.search(item["text"]):
                continue
            if key == "protected_boundaries":
                paths, unsupported = boundary_spans(item["text"])
                accepted[key].extend(path for path in paths if path not in accepted[key])
                course.unsupported_boundaries.extend(dict(entry, line=item["line"]) for entry in unsupported)
            else:
                accepted[key].append(item["text"])

    for number, row in table_rows(sections.get("milestones", [])):
        specs = [part for part in (plain(MD_LINK.sub(r"\1", piece)) for piece in column(row, "spec").split(","))
                 if part.lower() not in EMPTY_CELLS]
        course.milestones.append({"line": number, "milestone": column(row, "milestone"),
                                  "status": plain(column(row, "status")), "specs": specs,
                                  "notes": column(row, "note")})

    for number, row in table_rows(sections.get("area_map", [])):
        course.area_map.append({"line": number, "area": column(row, "area"),
                                "paths": path_tokens(column(row, "path")),
                                "verification": column(row, "verification"),
                                "invariants": column(row, "invariant")})

    decisions_inferred = "decision_log" in inferred_sections
    for number, row in table_rows(sections.get("decision_log", [])):
        identifier = DECISION_ID.search(column(row, "id"))
        status = plain(column(row, "status"))
        decision = column(row, "decision")
        superseded = SUPERSEDED.search(status)
        adr_paths = adr_links(" ".join(row.values()))
        inferred = decisions_inferred or any(INFERRED.search(value) for value in row.values())
        if superseded or inferred:
            is_accepted = False
        elif ACCEPTED.match(status):
            is_accepted = True
        else:
            # A row that defers to its ADR is accepted only when the ADR itself says Status: Accepted.
            is_accepted = not status and adr_status(adr_paths, read_file)
        course.decisions.append({"line": number, "id": identifier.group(0) if identifier else column(row, "id"),
                                 "date": column(row, "date"), "status": status, "decision": decision,
                                 "superseded_by": superseded.group(1) if superseded else None,
                                 "adr_paths": adr_paths, "accepted": is_accepted})

    course.accepted = {
        "north_star": " ".join(accepted["north_star"]) or None,
        "precedence": accepted["precedence"],
        "protected_boundaries": accepted["protected_boundaries"],
        "non_goals": accepted["non_goals"],
        "accepted_decisions": [{"id": item["id"], "date": item["date"], "status": item["status"],
                                "decision": normalize(item["decision"]), "adr_paths": item["adr_paths"]}
                               for item in course.decisions if item["accepted"]],
    }
    return course


def protected_paths(course: Course) -> list[str]:
    """Accepted Protected Boundaries plus the ADR files linked from accepted decisions."""
    paths = list(course.accepted.get("protected_boundaries", []))
    for decision in course.accepted.get("accepted_decisions", []):
        paths.extend(path for path in decision["adr_paths"] if path not in paths)
    return paths
