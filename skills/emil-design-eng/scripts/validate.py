#!/usr/bin/env python3
"""Validate the consolidated Emil package, aliases, links, lock state, and eval definitions."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

PACKAGE = Path(__file__).resolve().parents[1]
SKILLS = PACKAGE.parent
REPO = SKILLS.parent
ALIASES = {
    "animation-vocabulary": "name",
    "apple-design": "apple",
    "find-animation-opportunities": "opportunities",
    "prototype": "prototype",
    "review-animations": "review",
    "improve-animations": "improve",
}
LEAVES = {
    "references/animation-plan-template.md",
    "references/animation-vocabulary.md",
    "references/apple-design.md",
    "references/design-engineering-catalog.md",
    "references/maintenance.md",
    "references/motion-principles.md",
    "references/motion-standards.md",
    "references/provenance.md",
    "workflows/apply-motion.md",
    "workflows/find-opportunities.md",
    "workflows/improve-motion.md",
    "workflows/prototype.md",
    "workflows/review-motion.md",
}
PACKAGE_FILES = LEAVES | {
    "SKILL.md",
    "evals/evals.json",
    "scripts/validate.py",
}
EXPECTED_PROFILES = [
    "fast/economical",
    "balanced/default",
    "highest-reasoning",
]
REQUIRED_MODES = {
    "name",
    "apply",
    "review",
    "opportunities",
    "improve",
    "apple",
    "prototype ui",
    "prototype logic",
    "none",
    "alias",
}
REQUIRED_RECORD_FIELDS = {
    "provider",
    "model_id",
    "thinking_level",
    "pi_version",
    "loaded_files",
    "input_tokens",
    "output_tokens",
    "tool_calls",
    "routing_outcome",
    "assertion_results",
    "unauthorized_mutations",
    "visual_checks_run",
}


def frontmatter(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError(f"missing frontmatter: {path}")
    return text.split("\n---\n", 1)[0][4:]


def scalar(fm: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+)$", fm)
    if not match:
        return None
    return match.group(1).strip().strip('"\'')


def links(path: Path) -> list[str]:
    return re.findall(r"\[[^\]]+\]\(([^)]+)\)", path.read_text(encoding="utf-8"))


def slug(text: str) -> str:
    value = re.sub(r"<[^>]+>", "", text.strip().lower())
    value = re.sub(r"[^\w\- ]", "", value, flags=re.UNICODE)
    return re.sub(r"[ ]+", "-", value)


def anchors(path: Path) -> set[str]:
    found: set[str] = set()
    counts: dict[str, int] = {}
    for heading in re.findall(r"(?m)^#{1,6}\s+(.+?)\s*$", path.read_text(encoding="utf-8")):
        base = slug(heading)
        number = counts.get(base, 0)
        found.add(base if number == 0 else f"{base}-{number}")
        counts[base] = number + 1
    return found


def add(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre-remove-aliases", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []

    actual_files = {
        str(path.relative_to(PACKAGE))
        for path in PACKAGE.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
    if actual_files != PACKAGE_FILES:
        add(errors, f"package inventory mismatch; missing={sorted(PACKAGE_FILES - actual_files)}, extra={sorted(actual_files - PACKAGE_FILES)}")
    generated = [path for path in PACKAGE.rglob("*") if path.name == "__pycache__" or path.suffix in {".pyc", ".pyo"}]
    if generated:
        add(errors, f"generated cache files in package: {[str(path.relative_to(REPO)) for path in generated]}")

    root = PACKAGE / "SKILL.md"
    try:
        fm = frontmatter(root)
        if scalar(fm, "name") != "emil-design-eng":
            add(errors, "umbrella name must be emil-design-eng")
        description = scalar(fm, "description") or ""
        if not 1 <= len(description) <= 1024:
            add(errors, "umbrella description must contain 1-1024 characters")
        if scalar(fm, "disable-model-invocation") == "true":
            add(errors, "umbrella must remain automatically discoverable")
    except (OSError, ValueError) as error:
        add(errors, str(error))

    root_targets = {
        target.split("#", 1)[0]
        for target in links(root)
        if target.startswith(("references/", "workflows/"))
    }
    if LEAVES - root_targets:
        add(errors, f"SKILL.md does not directly link leaves: {sorted(LEAVES - root_targets)}")
    for target in root_targets:
        if len(Path(target).parts) != 2:
            add(errors, f"leaf link is deeper than one level: {target}")

    for path in PACKAGE.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if path != root and len(text.splitlines()) > 100 and not re.search(r"(?mi)^## Contents\s*$", text):
            add(errors, f"long leaf lacks Contents section: {path.relative_to(REPO)}")
        for link in links(path):
            if "://" in link or link.startswith("mailto:"):
                continue
            file_part, separator, anchor = link.partition("#")
            target_path = path if not file_part else (path.parent / unquote(file_part)).resolve()
            if not target_path.is_file():
                add(errors, f"broken link: {path.relative_to(REPO)} -> {link}")
                continue
            if separator and unquote(anchor) not in anchors(target_path):
                add(errors, f"broken anchor: {path.relative_to(REPO)} -> {link}")

    automatic_family: list[str] = []
    for name in ["emil-design-eng", *ALIASES]:
        path = SKILLS / name / "SKILL.md"
        try:
            fm = frontmatter(path)
            if scalar(fm, "name") != name:
                add(errors, f"skill name mismatch: {name}")
            description = scalar(fm, "description") or ""
            if not 1 <= len(description) <= 1024:
                add(errors, f"invalid description: {name}")
            hidden = scalar(fm, "disable-model-invocation") == "true"
            if not hidden:
                automatic_family.append(name)
            if name in ALIASES:
                mode = ALIASES[name]
                if not hidden:
                    add(errors, f"alias remains automatically discoverable: {name}")
                if not re.search(r"(?m)^  alias-for: emil-design-eng$", fm):
                    add(errors, f"alias-for metadata missing: {name}")
                if not re.search(rf"(?m)^  mode: {re.escape(mode)}$", fm):
                    add(errors, f"alias mode mismatch: {name}")
                body = path.read_text(encoding="utf-8")
                if "../emil-design-eng/SKILL.md" not in body or "final `User: <arguments>` block" not in body:
                    add(errors, f"alias forwarding contract missing: {name}")
                alias_files = [item for item in path.parent.rglob("*") if item.is_file()]
                if alias_files != [path]:
                    add(errors, f"alias contains unexpected files: {name}")
        except (OSError, ValueError) as error:
            add(errors, str(error))
    if automatic_family != ["emil-design-eng"]:
        add(errors, f"automatic family skills must be only emil-design-eng; got {automatic_family}")

    try:
        lock = json.loads((REPO / ".skill-lock.json").read_text(encoding="utf-8"))
        collisions = sorted(set(lock.get("skills", {})) & ({"emil-design-eng"} | set(ALIASES)))
        if collisions:
            add(errors, f"consolidated packages remain installer-managed: {collisions}")
    except (OSError, json.JSONDecodeError) as error:
        add(errors, f"invalid .skill-lock.json: {error}")

    try:
        definitions = json.loads((PACKAGE / "evals/evals.json").read_text(encoding="utf-8"))
        if definitions.get("profiles") != EXPECTED_PROFILES:
            add(errors, f"eval profiles must be {EXPECTED_PROFILES}")
        if set(definitions.get("record", [])) != REQUIRED_RECORD_FIELDS:
            add(errors, "eval record fields do not match the reproducibility contract")
        cases = definitions.get("cases", [])
        if len(cases) < 20:
            add(errors, "at least 20 umbrella eval cases are required")
        ids = [case.get("id") for case in cases]
        if len(ids) != len(set(ids)) or any(not item for item in ids):
            add(errors, "eval IDs must be non-empty and unique")
        modes = {case.get("mode") for case in cases}
        if REQUIRED_MODES - modes:
            add(errors, f"eval modes missing: {sorted(REQUIRED_MODES - modes)}")
        for case in cases:
            assertions = case.get("assertions")
            if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
                add(errors, f"eval prompt missing: {case.get('id')}")
            if not isinstance(assertions, list) or len(assertions) < 2 or not all(isinstance(item, str) and item.strip() for item in assertions):
                add(errors, f"eval needs at least two non-empty assertions: {case.get('id')}")
    except (OSError, json.JSONDecodeError) as error:
        cases = []
        add(errors, f"invalid eval definitions: {error}")

    if args.pre_remove_aliases:
        for skill in SKILLS.iterdir():
            if not skill.is_dir() or skill.name in ALIASES:
                continue
            for path in skill.rglob("*.md"):
                if path in {PACKAGE / "references/maintenance.md", PACKAGE / "references/provenance.md"}:
                    continue
                text = path.read_text(encoding="utf-8")
                for old in ALIASES:
                    if re.search(rf"/skill:{re.escape(old)}\b", text):
                        add(errors, f"active old command reference: {path.relative_to(REPO)} -> {old}")

    if errors:
        print("Consolidation validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Consolidation validation passed: 1 umbrella, {len(ALIASES)} explicit aliases, {len(cases)} eval cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
