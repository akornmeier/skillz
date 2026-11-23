#!/usr/bin/env python3
"""Report Certain drift between specs/COURSE.md, specs/*.html plans, and the repository.

Checks only deterministic facts: COURSE.md Milestone specs, Area Map paths, and Decision Log links
exist; Milestone statuses agree with linked task markers; each plan validates under the sibling
validate_plan.py contract for its class (legacy, retired, completed, or active). Exit 0 when there are
no Certain failures (warnings allowed), 1 on any Certain failure, 2 on bad input. Read-only and
standard library only; it runs no git or shell commands.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SIBLINGS = Path(__file__).resolve().parents[2] / "planf3" / "scripts"
COURSE_PATH = Path("specs") / "COURSE.md"
MILESTONE_STATUSES = ("planned", "active", "done", "dropped")
RETIRED_SEGMENT = re.compile(r"^\s*(?:retired\s*:|superseded\s+by(?:\s*:|\s+\S))", re.I)


class InputError(Exception):
    """Bad input: missing sibling script, unreadable root, or unreadable COURSE.md."""


def load_siblings(directory: Path = SIBLINGS):
    """Import validate_plan.py and course_parser.py from the planf3 scripts directory."""
    missing = [name for name in ("validate_plan.py", "course_parser.py") if not (directory / name).is_file()]
    if missing:
        raise InputError(f"missing sibling script(s) {', '.join(missing)} in {directory}; "
                         "install the planf3 skill next to project-course")
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
    import course_parser  # noqa: E402
    import validate_plan  # noqa: E402
    return validate_plan, course_parser


class Report:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.failures: list[dict] = []
        self.warnings: list[dict] = []
        self.skipped: list[dict] = []
        self.plans: list[dict] = []

    def rel(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return str(path)

    @staticmethod
    def finding(code: str, file: str, message: str, line: int | None = None) -> dict:
        item = {"code": code, "file": file, "message": message}
        if line is not None:
            item["line"] = line
        return item

    def fail(self, code: str, file: str, message: str, line: int | None = None) -> None:
        self.failures.append(self.finding(code, file, message, line))

    def warn(self, code: str, file: str, message: str, line: int | None = None) -> None:
        self.warnings.append(self.finding(code, file, message, line))


def resolve(token: str, root: Path, doc_dir: Path) -> Path | None:
    """Resolve a path token against the repo root first, then the containing document's directory."""
    for base in (root, doc_dir):
        candidate = base / token
        if candidate.exists():
            return candidate.resolve()
    return None


def parse_plan(validate_plan, source: str):
    parser = validate_plan.PlanParser()
    parser.feed(source)
    parser.close()
    return parser


def task_statuses(validate_plan, parser) -> list[str]:
    return [validate_plan.task_status(parser, element) for element in parser.elements if "task" in element.classes]


def classify(validate_plan, parser) -> str:
    """Return 'legacy', 'retired', 'completed', or 'active' for a parsed plan."""
    has_sections = "acceptance" in parser.ids or "coverage" in parser.ids
    has_markers = any({"criterion", "task"} & element.classes for element in parser.elements)
    if not has_sections and not has_markers:
        return "legacy"
    segments = parser.metadata.get("forward refs", "").split(";")
    if any(RETIRED_SEGMENT.match(segment.strip()) for segment in segments):
        return "retired"
    statuses = task_statuses(validate_plan, parser)
    if statuses and all(status == "x" for status in statuses):
        return "completed"
    return "active"


def check_course(report: Report, course, course_file: Path, validate_plan, plan_cache: dict) -> set[Path]:
    """Run the COURSE.md Certain checks and return the resolved spec paths Milestones link to."""
    root, doc_dir, name = report.root, course_file.parent, report.rel(course_file)
    linked: set[Path] = set()

    for row in course.milestones:
        status = row["status"].strip()
        if status.lower() not in MILESTONE_STATUSES:
            report.warn("milestone-status-unknown", name,
                        f"milestone {row['milestone']!r} has status {status!r}; use Planned, Active, Done, or Dropped",
                        row["line"])
        spec_statuses = []
        for spec in row["specs"]:
            path = resolve(spec, root, doc_dir)
            if path is None:
                report.fail("milestone-spec-missing", name,
                            f"milestone {row['milestone']!r} links spec {spec!r}, which does not exist", row["line"])
                continue
            linked.add(path)
            if path.suffix.lower() == ".html" and path.is_file():
                parser = plan_cache.get(path)
                if parser is None:
                    try:
                        parser = parse_plan(validate_plan, path.read_text(encoding="utf-8"))
                    except (OSError, UnicodeError):
                        continue
                    plan_cache[path] = parser
                spec_statuses.append((spec, task_statuses(validate_plan, parser)))
        lowered = status.lower()
        if lowered == "done":
            open_specs = [spec for spec, statuses in spec_statuses if any(s != "x" for s in statuses)]
            if open_specs:
                report.warn("milestone-done-mismatch", name,
                            f"milestone {row['milestone']!r} is Done but {', '.join(open_specs)} has tasks not marked [x]",
                            row["line"])
        elif lowered in ("planned", "active"):
            if spec_statuses and all(statuses and all(s == "x" for s in statuses) for _, statuses in spec_statuses):
                report.warn("milestone-open-mismatch", name,
                            f"milestone {row['milestone']!r} is {status} but every linked task is marked [x]",
                            row["line"])

    for row in course.area_map:
        for token in row["paths"]:
            if resolve(token, root, doc_dir) is None:
                report.fail("area-path-missing", name,
                            f"area {row['area']!r} lists path {token!r}, which does not exist", row["line"])

    seen: dict[str, int] = {}
    for row in course.decisions:
        identifier = row["id"]
        if identifier in seen:
            report.fail("decision-id-duplicate", name,
                        f"decision {identifier!r} repeats the ID first used on line {seen[identifier]}", row["line"])
        elif identifier:
            seen[identifier] = row["line"]
    for row in course.decisions:
        target = row["superseded_by"]
        if target and target not in seen:
            report.fail("decision-superseded-missing", name,
                        f"decision {row['id']!r} is superseded by {target!r}, which is not in the Decision Log",
                        row["line"])
        for token in row["adr_paths"]:
            if resolve(token, root, doc_dir) is None:
                report.fail("decision-link-missing", name,
                            f"decision {row['id']!r} links {token!r}, which does not exist", row["line"])

    for proposal in course.proposals:
        report.warn("pending-proposal", name, f"pending proposal in {proposal['section']}: {proposal['text']}",
                    proposal["line"])
    for entry in course.unsupported_boundaries:
        report.warn("boundary-unsupported", name,
                    f"protected boundary {entry['span']!r} cannot be enforced ({entry['reason']})", entry.get("line"))
    return linked


def check_plans(report: Report, validate_plan, course_parser, course_present: bool, linked: set[Path],
                plan_cache: dict) -> None:
    specs = report.root / "specs"
    if not specs.is_dir():
        return
    for path in sorted(specs.glob("*.html")):
        path = path.resolve()
        name = report.rel(path)
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            report.fail("spec-unreadable", name, f"cannot read plan: {exc}")
            continue
        parser = plan_cache.get(path) or parse_plan(validate_plan, source)
        kind = classify(validate_plan, parser)
        entry = {"file": name, "classification": kind, "errors": 0, "warnings": 0}
        report.plans.append(entry)

        if kind == "legacy":
            reason = "pre-engineering plan: no #acceptance, #coverage, .criterion, or .task"
            report.skipped.append({"file": name, "classification": kind, "reason": reason})
            report.warn("legacy-format", name, f"skipped {reason}")
            continue

        repo_root = report.root if kind == "active" else None
        diagnostics = validate_plan.validate(path, source, None, repo_root)
        if kind == "retired":
            report.skipped.append({"file": name, "classification": kind,
                                   "reason": "forward refs mark the plan retired or superseded"})
            report.warn("retired-plan", name, "skipped strict checks: forward refs mark the plan retired or superseded")
            for item in diagnostics:
                report.warn(item.code, name, f"(retired plan, {item.severity}) {item.message}", item.line)
                entry["warnings"] += 1
            continue

        for item in diagnostics:
            if item.severity == "error":
                report.fail(item.code, name, item.message, item.line)
                entry["errors"] += 1
            else:
                report.warn(item.code, name, item.message, item.line)
                entry["warnings"] += 1
        if kind != "active":
            continue

        for key in ("back refs", "forward refs"):
            for token in course_parser.path_tokens(parser.metadata.get(key, "")):
                if resolve(token, report.root, path.parent) is None:
                    report.warn("ref-path-missing", name, f"{key} names {token!r}, which does not exist")
                    entry["warnings"] += 1
        if course_present and path not in linked:
            report.warn("unlinked-active-spec", name, f"active plan is not linked from any {COURSE_PATH.as_posix()} Milestone")
            entry["warnings"] += 1


def run(root: Path, siblings: Path = SIBLINGS) -> tuple[int, dict]:
    """Audit the repository at root and return (exit code, JSON-ready result)."""
    validate_plan, course_parser = load_siblings(siblings)
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise InputError(f"repo root is not a readable directory: {root}")
    report = Report(root)
    plan_cache: dict = {}
    course_file = root / COURSE_PATH
    linked: set[Path] = set()
    course_present = course_file.is_file()
    if course_present:
        try:
            text = course_file.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise InputError(f"cannot read {course_file}: {exc}") from exc
        course = course_parser.parse_course(text, repo_root=root)
        linked = check_course(report, course, course_file, validate_plan, plan_cache)
    check_plans(report, validate_plan, course_parser, course_present, linked, plan_cache)

    counts: dict[str, int] = {}
    for plan in report.plans:
        counts[plan["classification"]] = counts.get(plan["classification"], 0) + 1
    result = {
        "ok": not report.failures,
        "course_file": COURSE_PATH.as_posix() if course_present else None,
        "certain": {"failures": report.failures, "warnings": report.warnings, "skipped": report.skipped},
        "summary": {"failures": len(report.failures), "warnings": len(report.warnings),
                    "skipped": len(report.skipped), "plan_counts": counts, "plans": report.plans},
    }
    return (1 if report.failures else 0), result


def render_text(result: dict) -> str:
    lines = []
    for title, key in (("FAILURES", "failures"), ("WARNINGS", "warnings")):
        items = result["certain"][key]
        if items:
            lines.append(f"{title} ({len(items)}):")
            for item in items:
                where = f"{item['file']}:{item['line']}" if item.get("line") else item["file"]
                lines.append(f"  {item['code']} {where}: {item['message']}")
    if result["certain"]["skipped"]:
        lines.append(f"SKIPPED ({len(result['certain']['skipped'])}):")
        for item in result["certain"]["skipped"]:
            lines.append(f"  {item['file']} [{item['classification']}]: {item['reason']}")
    summary = result["summary"]
    plans = ", ".join(f"{count} {kind}" for kind, count in sorted(summary["plan_counts"].items())) or "no plans"
    verdict = "PASS" if result["ok"] else "FAIL"
    lines.append(f"{verdict}: {summary['failures']} failure(s), {summary['warnings']} warning(s), "
                 f"{summary['skipped']} skipped; plans: {plans}; course: {result['course_file'] or 'none'}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-root", type=Path, default=Path("."),
                        help="repository to audit (default: current directory); reads <root>/specs/COURSE.md")
    parser.add_argument("--json", action="store_true", dest="json_output", help="print the JSON result")
    args = parser.parse_args(argv)
    try:
        code, result = run(args.repo_root)
    except InputError as exc:
        print(f"check_drift: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2) if args.json_output else render_text(result))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
