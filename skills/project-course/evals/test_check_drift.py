"""Unit tests for check_drift.py using temporary repositories; standard library only."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_drift.py"
SPEC = importlib.util.spec_from_file_location("check_drift", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
check_drift = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_drift
SPEC.loader.exec_module(check_drift)


def status(mark: str | None) -> str:
    return "" if mark is None else f'<code class="status">[{mark}]</code> '


def plan(tasks=("",), back: str = "None", forward: str = "None", files: str = "src/app.py",
         amendments: str = "", drop: str | None = None) -> str:
    """Compact modern plan; tasks lists each task's h4 status ('', 'wip', 'x', 'f', or None for unmarked)."""
    task_html, task_links, verify_links = [], [], []
    for index, mark in enumerate(tasks, 1):
        evidence = "Ran it; exit 0." if mark == "x" else "Not run."
        task_html.append(
            f'<div class="task" id="task-{index}"><h4>{status(mark)}Task {index}</h4>'
            f'<div class="verification" id="verify-{index}"><dl>'
            f'<dt>Cases</dt><dd class="cases">Case {index}.</dd>'
            f'<dt>Command</dt><dd class="command">make test</dd>'
            f'<dt>Expected</dt><dd class="expected">Exit 0.</dd>'
            f'<dt>Evidence</dt><dd class="evidence">{evidence}</dd></dl></div></div>')
        task_links.append(f'<a href="#task-{index}">T{index}</a>')
        verify_links.append(f'<a href="#verify-{index}">V{index}</a>')
    source = f"""<!doctype html><html lang="en"><head><title>Fixture</title>
<style>:root {{ --bg: #000; --paper-2: #000; --ink: #fff; --muted: #fff;
--soft: #fff; --rule: #fff; --accent: #fff; --accent-tint: #000; }}</style>
</head><body><details class="meta"><summary>Metadata</summary><dl>
<dt>created</dt><dd>2026-01-01T00:00:00Z</dd><dt>modified</dt><dd>None</dd>
<dt>commits</dt><dd>None</dd><dt>agent name</dt><dd>Fixture</dd>
<dt>session id</dt><dd>Fixture</dd><dt>back refs</dt><dd>{back}</dd>
<dt>forward refs</dt><dd>{forward}</dd></dl></details>
<section id="purpose">Purpose.</section><section id="problem">Problem.</section>
<section id="solution">Solution.</section>
<section id="acceptance"><ul><li class="criterion" id="ac-main">It works.</li></ul></section>
<section id="coverage"><table><tbody><tr><td><a href="#ac-main">AC</a></td>
<td>{' '.join(task_links)}</td><td>{' '.join(verify_links)}</td></tr></tbody></table></section>
<section id="files"><ul><li><span class="tag existing">existing</span> <code>{files}</code></li></ul></section>
<section id="phases"><div class="phase"><h3>Phase 1</h3>{''.join(task_html)}</div></section>
<section id="validation">make test</section><section id="notes">None.</section>
<section id="amendments">{amendments}</section></body></html>"""
    if drop:
        source = source.replace(f'id="{drop}"', f'id="removed-{drop}"')
    return source


LEGACY = """<!doctype html><html><head><title>Old plan</title><style>body {}</style></head>
<body><h1>Old plan</h1><section id="summary"><p>Do the thing.</p></section>
<ol><li>Step one</li><li>Step two</li></ol></body></html>"""

COURSE = """# Course

## North Star
Keep fixtures honest.

## Milestones
| Milestone | Status | Spec | Notes |
|---|---|---|---|
{milestones}

## Area & Verification Map
| Area | Paths | Verification | Invariants |
|---|---|---|---|
{areas}

## Decision Log
| ID | Date | Status | Decision | ADR |
|---|---|---|---|---|
{decisions}

## Proposals
{proposals}
"""


def amendment(summary: str, body: str) -> str:
    return f"<details><summary>{summary}</summary><p>{body}</p></details>"


class Repo:
    def __init__(self, directory: str) -> None:
        self.root = Path(directory)
        (self.root / "src").mkdir()
        (self.root / "src" / "app.py").write_text("", encoding="utf-8")
        (self.root / "specs").mkdir()

    def spec(self, name: str, source: str) -> None:
        (self.root / "specs" / name).write_text(source, encoding="utf-8")

    def course(self, milestones: str = "| M1 | Active | specs/active.html | — |",
               areas: str = "| Core | `src/` | `make test` | — |",
               decisions: str = "| D-001 | 2026-01-01 | Accepted | Use src | — |",
               proposals: str = "None yet.") -> None:
        text = COURSE.format(milestones=milestones, areas=areas, decisions=decisions, proposals=proposals)
        (self.root / "specs" / "COURSE.md").write_text(text, encoding="utf-8")


class CheckDriftTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Repo(self.tmp.name)

    def run_check(self) -> tuple[int, dict]:
        return check_drift.run(self.repo.root)

    @staticmethod
    def codes(result: dict, bucket: str) -> list[str]:
        return [item["code"] for item in result["certain"][bucket]]

    def classification(self, result: dict, name: str) -> str:
        return next(plan["classification"] for plan in result["summary"]["plans"] if plan["file"] == f"specs/{name}")

    def test_healthy_repo_with_course_and_active_plan(self) -> None:
        self.repo.spec("active.html", plan())
        self.repo.course()
        code, result = self.run_check()
        self.assertEqual(code, 0)
        self.assertTrue(result["ok"])
        self.assertEqual(result["course_file"], "specs/COURSE.md")
        self.assertEqual(result["certain"], {"failures": [], "warnings": [], "skipped": []})

    def test_repo_without_course(self) -> None:
        self.repo.spec("active.html", plan())
        code, result = self.run_check()
        self.assertEqual(code, 0)
        self.assertIsNone(result["course_file"])
        self.assertNotIn("unlinked-active-spec", self.codes(result, "warnings"))

    def test_repo_without_specs_directory(self) -> None:
        shutil.rmtree(self.repo.root / "specs")
        self.assertEqual(self.run_check()[0], 0)

    def test_legacy_plan_skipped_with_warning(self) -> None:
        self.repo.spec("legacy.html", LEGACY)
        code, result = self.run_check()
        self.assertEqual(code, 0)
        self.assertEqual(self.codes(result, "warnings"), ["legacy-format"])
        self.assertEqual(result["certain"]["skipped"][0]["classification"], "legacy")

    def test_modern_plan_missing_only_coverage_fails(self) -> None:
        self.repo.spec("broken.html", plan(drop="coverage"))
        code, result = self.run_check()
        self.assertEqual(code, 1)
        self.assertEqual(self.classification(result, "broken.html"), "active")
        self.assertIn("PF3_SECTION_MISSING", self.codes(result, "failures"))
        self.assertEqual(result["certain"]["skipped"], [])

    def test_completed_plan_with_moved_files_passes(self) -> None:
        self.repo.spec("done.html", plan(tasks=("x", "x"), files="src/moved_away.py",
                                         back="old/history.md"))
        self.repo.spec("active.html", plan())
        self.repo.course()
        code, result = self.run_check()
        self.assertEqual(code, 0)
        self.assertEqual(self.classification(result, "done.html"), "completed")
        self.assertEqual(result["certain"]["warnings"], [])

    def test_completed_plan_missing_coverage_fails(self) -> None:
        self.repo.spec("done.html", plan(tasks=("x",), drop="coverage"))
        code, result = self.run_check()
        self.assertEqual(code, 1)
        self.assertEqual(self.classification(result, "done.html"), "completed")
        self.assertIn("PF3_SECTION_MISSING", self.codes(result, "failures"))

    def test_retired_plan_via_appended_forward_refs(self) -> None:
        self.repo.spec("old.html", plan(forward="None; Retired: replaced by the new flow",
                                        files="src/gone.py", drop="coverage"))
        self.repo.course()
        self.repo.spec("active.html", plan())
        code, result = self.run_check()
        self.assertEqual(code, 0)
        self.assertEqual(self.classification(result, "old.html"), "retired")
        self.assertIn("retired-plan", self.codes(result, "warnings"))
        self.assertIn("PF3_SECTION_MISSING", self.codes(result, "warnings"))
        self.assertNotIn("unlinked-active-spec", self.codes(result, "warnings"))

    def test_retired_plan_shaped_like_file_pr_haiku(self) -> None:
        forward = ('PR https://example.test/skillz/pull/5; repair evidence /tmp/repair.log; '
                   'superseded by skills/file-pr/SKILL.md "Bug review" (branch refactor/file-pr-simple-review)')
        self.repo.spec("file-pr-haiku-local-review.html", plan(tasks=("x",) * 7 + ("f",), forward=forward,
                                                               back="missing/pilot.html"))
        self.repo.course()
        self.repo.spec("active.html", plan())
        code, result = self.run_check()
        self.assertEqual(code, 0)
        self.assertEqual(self.classification(result, "file-pr-haiku-local-review.html"), "retired")
        self.assertEqual(self.codes(result, "failures"), [])
        self.assertNotIn("unlinked-active-spec", self.codes(result, "warnings"))
        self.assertNotIn("ref-path-missing", self.codes(result, "warnings"))

    def test_amendments_mentioning_retirement_stay_active(self) -> None:
        entries = (
            amendment("2026-10-27: Superseded test fixture", "Replaced the fixture."),
            amendment("2026-10-28", "Retired the ac-old-flow criterion."),
            amendment("Retired: ac-old-flow", "The criterion no longer applies, so it is retired."),
        )
        for entry in entries:
            with self.subTest(entry=entry):
                self.repo.spec("active.html", plan(amendments=entry))
                code, result = self.run_check()
                self.assertEqual(code, 0)
                self.assertEqual(self.classification(result, "active.html"), "active")

    def test_forward_refs_without_standalone_retirement_segment_stay_active(self) -> None:
        for forward in ("PR #4, retired: later maybe", "Superseded by", "notes; not superseded by anything"):
            with self.subTest(forward=forward):
                self.repo.spec("active.html", plan(forward=forward))
                self.assertEqual(self.classification(self.run_check()[1], "active.html"), "active")

    def test_failed_task_keeps_plan_active(self) -> None:
        self.repo.spec("active.html", plan(tasks=("x", "x", "f")))
        code, result = self.run_check()
        self.assertEqual(code, 0)
        self.assertEqual(self.classification(result, "active.html"), "active")

    def test_unmarked_or_wip_task_keeps_plan_active(self) -> None:
        for tasks in (("x", None), ("x", "wip")):
            with self.subTest(tasks=tasks):
                self.repo.spec("active.html", plan(tasks=tasks))
                self.assertEqual(self.classification(self.run_check()[1], "active.html"), "active")

    def test_unstarted_plan_with_missing_existing_file_fails(self) -> None:
        self.repo.spec("active.html", plan(files="src/missing.py"))
        code, result = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("PF3_EXISTING_FILE_MISSING", self.codes(result, "failures"))

    def test_in_progress_plan_with_missing_existing_file_warns(self) -> None:
        self.repo.spec("active.html", plan(tasks=("wip", ""), files="src/missing.py"))
        code, result = self.run_check()
        self.assertEqual(code, 0)
        self.assertIn("PF3_EXISTING_FILE_MISSING", self.codes(result, "warnings"))

    def test_milestone_multi_spec_missing_path_fails(self) -> None:
        self.repo.spec("active.html", plan())
        self.repo.course(milestones="| M1 | Active | specs/active.html, specs/missing.html | — |")
        code, result = self.run_check()
        self.assertEqual(code, 1)
        self.assertEqual(self.codes(result, "failures"), ["milestone-spec-missing"])
        self.assertIn("specs/missing.html", result["certain"]["failures"][0]["message"])

    def test_milestone_done_with_unfinished_or_failed_tasks_warns(self) -> None:
        for tasks in (("x", "f"), ("x", ""), ("x", "wip"), ("x", None)):
            with self.subTest(tasks=tasks):
                self.repo.spec("active.html", plan(tasks=tasks))
                self.repo.course(milestones="| M1 | Done | specs/active.html | — |")
                code, result = self.run_check()
                self.assertEqual(code, 0)
                self.assertIn("milestone-done-mismatch", self.codes(result, "warnings"))

    def test_milestone_active_with_all_tasks_done_warns(self) -> None:
        self.repo.spec("done.html", plan(tasks=("x", "x")))
        self.repo.course(milestones="| M1 | Active | specs/done.html | — |")
        code, result = self.run_check()
        self.assertEqual(code, 0)
        self.assertIn("milestone-open-mismatch", self.codes(result, "warnings"))

    def test_milestone_unknown_status_warns(self) -> None:
        self.repo.spec("active.html", plan())
        self.repo.course(milestones="| M1 | Someday | specs/active.html | — |")
        code, result = self.run_check()
        self.assertEqual(code, 0)
        self.assertIn("milestone-status-unknown", self.codes(result, "warnings"))

    def test_area_map_missing_path_fails(self) -> None:
        self.repo.spec("active.html", plan())
        self.repo.course(areas="| Core | `src/`, `lib/missing.py` | `make test` | — |")
        code, result = self.run_check()
        self.assertEqual(code, 1)
        self.assertEqual(self.codes(result, "failures"), ["area-path-missing"])

    def test_area_map_ignores_verification_column_and_external_paths(self) -> None:
        self.repo.spec("active.html", plan())
        areas = ("| Core | `src/app.py` C:/temp/a.py ~/notes/x.md /etc/hosts.txt https://x.test/a.md "
                 "| `pytest --cov=lib/ tests/missing_test.py` | Keep docs/missing.md intact |")
        self.repo.course(areas=areas)
        code, result = self.run_check()
        self.assertEqual(code, 0)
        self.assertEqual(result["certain"]["failures"], [])

    def test_duplicate_decision_id_fails(self) -> None:
        self.repo.spec("active.html", plan())
        self.repo.course(decisions="| D-001 | 2026-01-01 | Accepted | One | — |\n"
                                   "| D-001 | 2026-01-02 | Accepted | Two | — |")
        code, result = self.run_check()
        self.assertEqual(code, 1)
        self.assertEqual(self.codes(result, "failures"), ["decision-id-duplicate"])

    def test_broken_superseded_by_fails(self) -> None:
        self.repo.spec("active.html", plan())
        self.repo.course(decisions="| D-001 | 2026-01-01 | Superseded by D-009 | One | — |")
        code, result = self.run_check()
        self.assertEqual(code, 1)
        self.assertEqual(self.codes(result, "failures"), ["decision-superseded-missing"])

    def test_valid_superseded_by_passes(self) -> None:
        self.repo.spec("active.html", plan())
        self.repo.course(decisions="| D-001 | 2026-01-01 | Superseded by D-002 | One | — |\n"
                                   "| D-002 | 2026-01-02 | Accepted | Two | — |")
        self.assertEqual(self.run_check()[0], 0)

    def test_broken_adr_link_fails(self) -> None:
        self.repo.spec("active.html", plan())
        self.repo.course(decisions="| D-001 | 2026-01-01 | Accepted | One | [ADR](docs/adr/0001-one.md) |")
        code, result = self.run_check()
        self.assertEqual(code, 1)
        self.assertEqual(self.codes(result, "failures"), ["decision-link-missing"])
        (self.repo.root / "docs" / "adr").mkdir(parents=True)
        (self.repo.root / "docs" / "adr" / "0001-one.md").write_text("Status: Accepted\n", encoding="utf-8")
        self.assertEqual(self.run_check()[0], 0)

    def test_prose_back_refs_warn_without_failing(self) -> None:
        back = r"https://example.test/docs; README.md; /file-pr; C:\temp\a.txt; None; missing/file.md"
        self.repo.spec("active.html", plan(back=back))
        code, result = self.run_check()
        self.assertEqual(code, 0)
        missing = [item for item in result["certain"]["warnings"] if item["code"] == "ref-path-missing"]
        self.assertEqual(len(missing), 1)
        self.assertIn("missing/file.md", missing[0]["message"])

    def test_forward_ref_paths_resolve_from_repo_root_or_spec_dir(self) -> None:
        (self.repo.root / "specs" / "notes").mkdir()
        (self.repo.root / "specs" / "notes" / "a.md").write_text("", encoding="utf-8")
        self.repo.spec("active.html", plan(forward="src/app.py; notes/a.md"))
        self.assertNotIn("ref-path-missing", self.codes(self.run_check()[1], "warnings"))

    def test_unlinked_active_spec_warns(self) -> None:
        self.repo.spec("active.html", plan())
        self.repo.spec("other.html", plan())
        self.repo.course()
        code, result = self.run_check()
        self.assertEqual(code, 0)
        unlinked = [item["file"] for item in result["certain"]["warnings"] if item["code"] == "unlinked-active-spec"]
        self.assertEqual(unlinked, ["specs/other.html"])

    def test_pending_proposal_warns(self) -> None:
        self.repo.spec("active.html", plan())
        self.repo.course(proposals="> PROPOSED: add a release milestone")
        code, result = self.run_check()
        self.assertEqual(code, 0)
        self.assertIn("pending-proposal", self.codes(result, "warnings"))

    def test_unsupported_protected_boundary_warns(self) -> None:
        self.repo.spec("active.html", plan())
        self.repo.course()
        course = self.repo.root / "specs" / "COURSE.md"
        course.write_text(course.read_text(encoding="utf-8")
                          + "\n## Protected Boundaries\n- `~/secrets/` and `infra/`\n", encoding="utf-8")
        code, result = self.run_check()
        self.assertEqual(code, 0)
        self.assertIn("boundary-unsupported", self.codes(result, "warnings"))


class CliTests(unittest.TestCase):
    def cli(self, *args: str, script: Path = SCRIPT) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, check=False)

    def test_help(self) -> None:
        result = self.cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--repo-root", result.stdout)

    def test_invalid_arguments_exit_2(self) -> None:
        self.assertEqual(self.cli("--bogus").returncode, 2)

    def test_missing_repo_root_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self.cli("--repo-root", str(Path(directory) / "nope"))
            self.assertEqual(result.returncode, 2)
            self.assertIn("repo root", result.stderr)

    def test_json_and_text_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Repo(directory)
            repo.spec("broken.html", plan(drop="coverage"))
            result = self.cli("--repo-root", directory, "--json")
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertEqual(set(payload), {"ok", "course_file", "certain", "summary"})
            self.assertEqual(set(payload["certain"]), {"failures", "warnings", "skipped"})
            finding = payload["certain"]["failures"][0]
            self.assertTrue({"code", "file", "message"} <= set(finding))
            text = self.cli("--repo-root", directory)
            self.assertEqual(text.returncode, 1)
            self.assertIn("FAIL: ", text.stdout.splitlines()[-1])

    def test_missing_sibling_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "skills" / "project-course" / "scripts" / "check_drift.py"
            script.parent.mkdir(parents=True)
            shutil.copy(SCRIPT, script)
            result = self.cli("--repo-root", directory, script=script)
            self.assertEqual(result.returncode, 2)
            self.assertIn("missing sibling", result.stderr)


if __name__ == "__main__":
    unittest.main()
