"""Focused mechanical checks for the engineering-plan contract; standard library only."""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_plan.py"
SPEC = importlib.util.spec_from_file_location("validate_plan", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


def plan() -> str:
    """Independent fixture, not generated from the template under test."""
    return """<!doctype html><html lang="en"><head><title>Pagination</title>
<style>:root { --bg: #000; --paper-2: #000; --ink: #fff; --muted: #fff;
--soft: #fff; --rule: #fff; --accent: #fff; --accent-tint: #000; }</style>
</head><body><details class="meta"><summary>Metadata</summary><dl>
<dt>created</dt><dd>2026-01-01T00:00:00Z</dd><dt>modified</dt><dd>None</dd>
<dt>commits</dt><dd>None</dd><dt>agent name</dt><dd>Fixture</dd>
<dt>session id</dt><dd>Fixture</dd><dt>back refs</dt><dd>None</dd>
<dt>forward refs</dt><dd>None</dd></dl></details>
<section id="purpose">Bound result sizes.</section>
<section id="problem">Unbounded results.</section>
<section id="solution">Parse the page-size query.</section>
<section id="acceptance"><ul>
<li class="criterion" id="ac-default">Missing pageSize yields 20.</li>
</ul></section>
<section id="coverage"><table><thead><tr><th>Criterion</th><th>Tasks</th>
<th>Verification</th></tr></thead><tbody><tr>
<td><a href="#ac-default">AC default</a></td>
<td><a href="#task-parser">Parser</a></td>
<td><a href="#verify-parser">Default case</a></td>
</tr></tbody></table></section>
<section id="files">src/pagination.ts</section>
<section id="phases"><div class="phase"><h3>Phase 1</h3>
<div class="task" id="task-parser"><h4>Parse page size</h4>
<ul class="checklist"><li>[] Implement parser.</li></ul>
<div class="verification" id="verify-parser"><dl>
<dt>Cases</dt><dd class="cases">null returns 20.</dd>
<dt>Command</dt><dd class="command"><code>pnpm test -- pagination</code></dd>
<dt>Expected</dt><dd class="expected">Default-value case passes; exit 0.</dd>
<dt>Evidence</dt><dd class="evidence">Not run.</dd>
</dl></div></div></div></section>
<section id="validation">pnpm test</section><section id="notes">No blockers.</section>
<section id="amendments"></section></body></html>"""


class EngineeringContractTests(unittest.TestCase):
    def codes(self, source: str) -> set[str]:
        return {item.code for item in validator.validate(Path("/tmp/plan.html"), source, None)}

    def test_valid_plan_without_optional_interfaces(self) -> None:
        self.assertEqual(self.codes(plan()), set())

    def test_filled_template_matches_the_validator_contract(self) -> None:
        source = (SCRIPT.parents[1] / "templates" / "plan.html").read_text(encoding="utf-8")
        source = re.sub(r'<figure>.*?</figure>', '', source, flags=re.S)
        source = re.sub(r'<!--.*?-->', '', source, flags=re.S)
        values = {"CREATED_ISO": "2026-01-01T00:00:00Z", "CRITERION_KEY": "default",
                  "TASK_KEY": "parser", "VERIFICATION_KEY": "parser"}
        source = re.sub(r'\{\{(.*?)\}\}',
                        lambda match: values.get(match.group(1).split(':', 1)[0].strip(), "Fixture"),
                        source, flags=re.S)
        self.assertEqual(self.codes(source), set())

    def test_missing_engineering_sections(self) -> None:
        for section in ("acceptance", "coverage"):
            with self.subTest(section=section):
                source = plan().replace(f'id="{section}"', f'id="removed-{section}"')
                self.assertIn("PF3_SECTION_MISSING", self.codes(source))

    def test_empty_engineering_sections_cannot_pass(self) -> None:
        source = plan().replace('class="criterion"', '').replace('class="task"', '')
        self.assertTrue({"PF3_CRITERIA_MISSING", "PF3_TASKS_MISSING"} <= self.codes(source))

    def test_missing_or_empty_verification_fields(self) -> None:
        for field in ("cases", "command", "expected", "evidence"):
            for mutation in ("missing", "empty"):
                with self.subTest(field=field, mutation=mutation):
                    source = plan()
                    if mutation == "missing":
                        source = source.replace(f'class="{field}"', '')
                    else:
                        source = re.sub(rf'(<dd class="{field}">).*?(</dd>)', r'\1 \2', source)
                    self.assertIn("PF3_VERIFICATION_FIELD", self.codes(source))

    def test_empty_verification_field_with_omitted_end_tag(self) -> None:
        source = plan().replace('<dd class="cases">null returns 20.</dd>', '<dd class="cases">')
        self.assertIn("PF3_VERIFICATION_FIELD", self.codes(source))

    def test_optional_definition_end_tags_preserve_field_text_and_metadata(self) -> None:
        source = plan().replace('</dt>', '').replace('</dd>', '')
        self.assertEqual(self.codes(source), set())
        parser = validator.PlanParser()
        parser.feed(source)
        parser.close()
        cases = next(element for element in parser.elements if 'cases' in element.classes)
        self.assertEqual(cases.text, 'null returns 20.')
        self.assertEqual(parser.metadata['created'], '2026-01-01T00:00:00Z')

    def test_multiple_coverage_rows_with_optional_end_tags(self) -> None:
        source = plan().replace('</ul></section>\n<section id="coverage">',
                                '<li class="criterion" id="ac-boundary">Maximum is 100.</li>'
                                '</ul></section>\n<section id="coverage">')
        source = source.replace('</tr></tbody>',
                                '</tr><tr><td><a href="#ac-boundary">Boundary</a></td>'
                                '<td><a href="#task-parser">Parser</a></td>'
                                '<td><a href="#verify-parser">Boundary case</a></td></tr></tbody>')
        for omitted in (('</tr>',), ('</td>', '</th>', '</tr>')):
            with self.subTest(omitted=omitted):
                optional = source
                for closing in omitted:
                    optional = optional.replace(closing, '')
                self.assertEqual(self.codes(optional), set())

    def test_implied_end_tags_respect_nested_list_and_table_scopes(self) -> None:
        parser = validator.PlanParser()
        parser.feed('<dl><dd id="outer-value">Outer<dl><dt>Inner<dd id="inner-value">Value</dl>Tail</dl>'
                    '<table><tbody><tr id="outer-row"><td id="outer-cell">Before'
                    '<table><tbody><tr id="inner-row"><td>Inner</table>After'
                    '<td id="next-cell">Next</table>')
        parser.close()
        elements = {element.attrs['id']: element for element in parser.elements if 'id' in element.attrs}
        self.assertTrue(elements['inner-value'].within(elements['outer-value']))
        self.assertEqual(elements['outer-value'].text, 'OuterInnerValueTail')
        self.assertTrue(elements['inner-row'].within(elements['outer-cell']))
        self.assertTrue(elements['next-cell'].within(elements['outer-row']))
        self.assertEqual(elements['outer-cell'].text, 'BeforeInnerAfter')

    def test_metadata_void_tags_do_not_leak_into_multiple_verifications(self) -> None:
        source = plan()
        block = re.search(r'<div class="verification".*?</div>', source, re.S).group(0)
        source = source.replace(block, block + block.replace('id="verify-parser"', 'id="verify-second"'))
        for line_break in ('<br>', '<br/>', '<br />'):
            with self.subTest(line_break=line_break):
                candidate = source.replace('<dd>Fixture</dd>', f'<dd>Fixture{line_break}agent</dd>', 1)
                self.assertEqual(self.codes(candidate), set())
                parser = validator.PlanParser()
                parser.feed(candidate)
                parser.close()
                self.assertFalse(parser.in_meta)
                self.assertEqual(set(parser.metadata), validator.REQUIRED_METADATA)

    def test_empty_criterion_with_optional_list_end_tag(self) -> None:
        source = plan().replace('<li class="criterion" id="ac-default">Missing pageSize yields 20.</li>',
                                '<li class="criterion" id="ac-default"><li>Unrelated item</li>')
        self.assertIn("PF3_CONTRACT_EMPTY", self.codes(source))

    def test_dangling_fragment_including_outside_coverage(self) -> None:
        source = plan().replace("No blockers.", '<a href="#missing">Missing</a>')
        self.assertIn("PF3_REFERENCE_MISSING", self.codes(source))

    def test_duplicate_ids(self) -> None:
        source = plan().replace("No blockers.", '<p id="task-parser">Duplicate</p>')
        self.assertIn("PF3_DUPLICATE_ID", self.codes(source))

    def test_coverage_row_requires_criterion_task_and_verification(self) -> None:
        for target in ("ac-default", "task-parser", "verify-parser"):
            with self.subTest(target=target):
                source = plan().replace(f'href="#{target}"', 'href="#files"')
                self.assertIn("PF3_COVERAGE_ROW", self.codes(source))

    def test_every_criterion_and_task_must_be_mapped(self) -> None:
        source = plan().replace('</ul></section>\n<section id="coverage">',
                                '<li class="criterion" id="ac-boundary">Maximum is 100.</li>'
                                '</ul></section>\n<section id="coverage">')
        self.assertIn("PF3_CRITERION_UNCOVERED", self.codes(source))
        source = plan().replace('</div></div></section>',
                                '</div><div class="task" id="task-orphan">Unmapped</div></div></section>')
        self.assertIn("PF3_TASK_UNCOVERED", self.codes(source))

    def test_verification_must_belong_to_a_mapped_task(self) -> None:
        source = plan().replace('<div class="verification"',
                                '</div><div class="task" id="task-other"><div class="verification"', 1)
        self.assertIn("PF3_COVERAGE_OWNER", self.codes(source))

    def test_contract_elements_require_correct_location_and_id_prefix(self) -> None:
        source = plan().replace('id="acceptance"', 'id="elsewhere"')
        self.assertIn("PF3_CONTRACT_LOCATION", self.codes(source))
        source = plan().replace('id="task-parser"', 'id="parser"').replace('#task-parser', '#parser')
        self.assertIn("PF3_CONTRACT_ID", self.codes(source))

    def test_empty_coverage_table(self) -> None:
        source = plan().replace('<tbody>', '<tfoot>').replace('</tbody>', '</tfoot>')
        self.assertIn("PF3_COVERAGE_MISSING", self.codes(source))

    def test_multi_task_mapping(self) -> None:
        source = plan().replace('<td><a href="#task-parser">Parser</a></td>',
                                '<td><a href="#task-parser">Parser</a> '
                                '<a href="#task-route">Route</a></td>')
        source = source.replace('</div></div></section>',
                                '</div><div class="task" id="task-route">Integrate route.'
                                '<div class="verification" id="verify-route"><dl>'
                                '<dd class="cases">HTTP response has 20 items.</dd>'
                                '<dd class="command">pnpm test -- route</dd>'
                                '<dd class="expected">Exit 0; response case passes.</dd>'
                                '<dd class="evidence">Not run.</dd>'
                                '</dl></div></div></div></section>')
        self.assertEqual(self.codes(source), set())

    def test_previous_metadata_protection_still_applies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            previous = Path(directory) / "previous.html"
            previous.write_text(plan(), encoding="utf-8")
            source = plan().replace("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z")
            codes = {item.code for item in validator.validate(previous, source, previous)}
            self.assertIn("PF3_CREATED_CHANGED", codes)



def done_plan(evidence: str = "pnpm test exited 0; default case passed.") -> str:
    """Fixture with the task, its checklist item, and its phase marked complete."""
    return (plan()
            .replace('<h3>Phase 1</h3>', '<h3><code class="status">[x]</code> Phase 1</h3>')
            .replace('<h4>Parse page size</h4>', '<h4><code class="status">[x]</code> Parse page size</h4>')
            .replace('<li>[] Implement parser.</li>', '<li><code class="status">[x]</code> Implement parser.</li>')
            .replace('<dd class="evidence">Not run.</dd>', f'<dd class="evidence">{evidence}</dd>'))


def with_amendments(source: str, *entries: str) -> str:
    body = "".join(f"<details><summary>{summary}</summary><p>{text}</p></details>" for summary, text in entries)
    return source.replace('<section id="amendments"></section>', f'<section id="amendments">{body}</section>')


FIRST = ("2026-01-02 — Initial review", "Tightened wording after review.")
SECOND = ("2026-01-03 — Boundary", "Added the boundary case.")


class AntiDriftTests(unittest.TestCase):
    def diagnostics(self, source: str, previous: str | None = None, repo_root: Path | None = None):
        with tempfile.TemporaryDirectory() as directory:
            previous_path = None
            if previous is not None:
                previous_path = Path(directory) / "previous.html"
                previous_path.write_text(previous, encoding="utf-8")
            return validator.validate(Path(directory) / "plan.html", source, previous_path, repo_root)

    def codes(self, source: str, previous: str | None = None, repo_root: Path | None = None) -> dict[str, str]:
        return {item.code: item.severity for item in self.diagnostics(source, previous, repo_root)}

    def run_cli(self, source: str, *flags: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.html"
            path.write_text(source, encoding="utf-8")
            return subprocess.run([sys.executable, str(SCRIPT), str(path), *flags],
                                  capture_output=True, text=True, check=False)

    def test_mutated_or_deleted_criterion_without_amendment_fails(self) -> None:
        changed = plan().replace("Missing pageSize yields 20.", "Missing pageSize yields 50.")
        self.assertEqual(self.codes(changed, plan()).get("PF3_AC_MUTATED"), "error")
        removed = plan().replace('class="criterion" id="ac-default"', 'id="dropped"')
        self.assertIn("PF3_AC_MUTATED", self.codes(removed, plan()))

    def test_appended_amendment_naming_exact_id_with_rationale_passes(self) -> None:
        previous = with_amendments(plan(), FIRST)
        changed = with_amendments(plan().replace("yields 20.", "yields 50."), FIRST,
                                  ("2026-01-04 — ac-default", "Product raised the default page size for ac-default."))
        self.assertEqual(self.codes(changed, previous), {})

    def test_amendment_must_name_exact_id_and_give_a_rationale(self) -> None:
        previous = with_amendments(plan(), FIRST)
        for summary, text in (("2026-01-04 — ac-default-rate", "Raised the limit for ac-default-rate."),
                              ("2026-01-04 — ac-default", "ac-default")):
            with self.subTest(summary=summary, text=text):
                changed = with_amendments(plan().replace("yields 20.", "yields 50."), FIRST, (summary, text))
                self.assertIn("PF3_AC_MUTATED", self.codes(changed, previous))

    def test_prefix_substring_never_satisfies_a_shorter_id(self) -> None:
        base = plan().replace('id="ac-default"', 'id="ac-login"').replace('#ac-default', '#ac-login')
        changed = with_amendments(base.replace("yields 20.", "yields 50."),
                                  ("2026-01-04 — ac-login-rate", "Changed ac-login-rate because traffic grew."))
        self.assertIn("PF3_AC_MUTATED", self.codes(changed, base))

    def test_old_amendment_rewritten_reordered_or_preceded_fails(self) -> None:
        previous = with_amendments(plan(), FIRST, SECOND)
        for label, current in (
                ("rewritten", with_amendments(plan(), (FIRST[0], "Different rationale."), SECOND)),
                ("reordered", with_amendments(plan(), SECOND, FIRST)),
                ("deleted", with_amendments(plan(), SECOND)),
                ("inserted first", with_amendments(plan(), ("2026-01-05 — New", "New entry."), FIRST, SECOND))):
            with self.subTest(label=label):
                self.assertEqual(self.codes(current, previous).get("PF3_AMENDMENT_REWRITTEN"), "error")
        appended = with_amendments(plan(), FIRST, SECOND, ("2026-01-05 — New", "New entry."))
        self.assertEqual(self.codes(appended, previous), {})

    def test_adding_a_new_criterion_is_not_a_mutation(self) -> None:
        current = plan().replace('</ul></section>\n<section id="coverage">',
                                 '<li class="criterion" id="ac-boundary">Maximum is 100.</li>'
                                 '</ul></section>\n<section id="coverage">')
        self.assertNotIn("PF3_AC_MUTATED", self.codes(current, plan()))

    def test_done_task_with_blank_evidence_warns_by_default_and_fails_strict(self) -> None:
        source = done_plan(" ")
        self.assertEqual(self.codes(source), {"PF3_DONE_WITHOUT_EVIDENCE": "warning"})
        default = self.run_cli(source, "--json")
        self.assertEqual(default.returncode, 0, default.stderr)
        self.assertTrue(json.loads(default.stdout)["ok"])
        strict = self.run_cli(source, "--json", "--strict")
        self.assertEqual(strict.returncode, 1)
        self.assertFalse(json.loads(strict.stdout)["ok"])

    def test_missing_duplicate_or_unfinished_blank_evidence_stays_structural(self) -> None:
        missing = done_plan().replace('class="evidence"', '')
        duplicate = done_plan().replace('<dd class="evidence">', '<dd class="evidence">Ran.</dd><dd class="evidence">')
        unfinished = plan().replace('<dd class="evidence">Not run.</dd>', '<dd class="evidence"> </dd>')
        for label, source in (("missing", missing), ("duplicate", duplicate), ("unfinished", unfinished)):
            with self.subTest(label=label):
                codes = self.codes(source)
                self.assertEqual(codes.get("PF3_VERIFICATION_FIELD"), "error")
                self.assertNotIn("PF3_DONE_WITHOUT_EVIDENCE", codes)

    def test_done_task_with_placeholder_evidence_warns(self) -> None:
        for evidence in ("Not run.", "Stale: parser changed.", "DEFERRED: needs staging.", "not run yet"):
            with self.subTest(evidence=evidence):
                self.assertEqual(self.codes(done_plan(evidence)), {"PF3_DONE_WITHOUT_EVIDENCE": "warning"})
                self.assertEqual(self.run_cli(done_plan(evidence), "--strict").returncode, 1)

    def test_current_and_mixed_historical_evidence_pass_strict(self) -> None:
        for evidence in ("pnpm test exited 0.",
                         "Historical (superseded): Not run. Final: pnpm test exited 0 after the rename."):
            with self.subTest(evidence=evidence):
                self.assertEqual(self.codes(done_plan(evidence)), {})
                result = self.run_cli(done_plan(evidence), "--strict")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("STRUCTURALLY VALID", result.stdout)

    def test_task_status_reads_only_its_own_heading(self) -> None:
        source = (plan().replace('<h4>Parse page size</h4>', '<h4><code class="status">[]</code> Parse page size</h4>')
                  .replace('<li>[] Implement parser.</li>', '<li><code class="status">[x]</code> Implement parser.</li>'))
        self.assertEqual(self.codes(source), {})

    def test_done_phase_with_unfinished_task_or_checklist_warns(self) -> None:
        unfinished_task = done_plan().replace('<h4><code class="status">[x]</code>', '<h4><code class="status">[wip]</code>')
        unmarked_item = done_plan().replace('<li><code class="status">[x]</code> Implement parser.</li>',
                                            '<li><code class="status">[x]</code> Implement parser.</li><li>Run tests.</li>')
        for label, source in (("task", unfinished_task), ("checklist", unmarked_item)):
            with self.subTest(label=label):
                self.assertEqual(self.codes(source).get("PF3_PHASE_PREMATURE_DONE"), "warning")
                self.assertEqual(self.run_cli(source, "--strict").returncode, 1)
                result = self.run_cli(source)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("STRUCTURALLY VALID (", result.stdout)
        self.assertEqual(self.codes(done_plan()), {})

    def test_repo_root_missing_existing_file_errors_until_a_build_starts(self) -> None:
        files = ('<section id="files" class="files"><ul><li><span class="tag existing">existing</span> '
                 '<code>src/pagination.ts</code> — run with <code>--repo-root</code> and <code>sol-loop</code></li>'
                 '<li><span class="tag new">new</span> <code>src/new.ts</code></li></ul></section>')
        source = plan().replace('<section id="files">src/pagination.ts</section>', files)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(self.codes(source, repo_root=root).get("PF3_EXISTING_FILE_MISSING"), "error")
            resumed = source.replace('<h4>Parse page size</h4>', '<h4><code class="status">[x]</code> Parse page size</h4>')
            self.assertEqual(self.codes(resumed, repo_root=root).get("PF3_EXISTING_FILE_MISSING"), "warning")
            (root / "src").mkdir()
            (root / "src" / "pagination.ts").write_text("export {};\n", encoding="utf-8")
            self.assertEqual(self.codes(source, repo_root=root), {})
            self.assertEqual(self.codes(source), {})
            escaping = source.replace('<code>src/pagination.ts</code>', '<code>../outside.ts</code>')
            self.assertEqual(self.codes(escaping, repo_root=root).get("PF3_EXISTING_FILE_MISSING"), "error")

    def test_repo_root_cli_reports_warning_for_resumed_build(self) -> None:
        files = ('<section id="files" class="files"><ul><li><span class="tag existing">existing</span> '
                 '<code>src/renamed.ts</code></li></ul></section>')
        source = done_plan().replace('<section id="files">src/pagination.ts</section>', files)
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli(source, "--repo-root", directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("STRUCTURALLY VALID (1 warning)", result.stdout)
            self.assertIn("PF3_EXISTING_FILE_MISSING", result.stderr)
            self.assertEqual(self.run_cli(source, "--repo-root", directory, "--strict").returncode, 1)

    def test_sidecar_image_resolves_only_beside_the_materialized_plan(self) -> None:
        figure = '<figure><img src="plan/flow.png" alt="Request flow"><figcaption>Flow.</figcaption></figure>'
        source = plan().replace('<section id="purpose">', figure + '<section id="purpose">')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "plan").mkdir()
            (root / "plan" / "flow.png").write_bytes(b"\x89PNG fixture")
            materialized = {item.code for item in validator.validate(root / "plan.html", source, None)}
            self.assertEqual(materialized, set())
        with tempfile.TemporaryDirectory() as directory:
            standalone = {item.code for item in validator.validate(Path(directory) / "plan.html", source, None)}
            self.assertIn("PF3_IMAGE_MISSING", standalone)

    def test_amendment_of_only_criterion_ids_is_not_a_rationale(self) -> None:
        changed = with_amendments(plan().replace("yields 20.", "yields 50."),
                                  ("2026-01-04 — ac-default", "ac-default, ac-other"))
        self.assertIn("PF3_AC_MUTATED", self.codes(changed, plan()))

    def test_compact_amendment_html_still_cites_the_id(self) -> None:
        changed = plan().replace("yields 20.", "yields 50.").replace(
            '<section id="amendments"></section>',
            '<section id="amendments"><details><summary>2026-01-04 change</summary>'
            '<p>ac-default raised because product asked.</p></details></section>')
        self.assertEqual(self.codes(changed, plan()), {})

    def test_unmarked_checklist_item_does_not_inherit_a_nested_status(self) -> None:
        nested = done_plan().replace('<li><code class="status">[x]</code> Implement parser.</li>',
                                     '<li><ul><li>[x] Sub-step.</li></ul>Implement parser.</li>')
        self.assertEqual(self.codes(nested).get("PF3_PHASE_PREMATURE_DONE"), "warning")

    def test_cli_bad_repo_root_exits_2(self) -> None:
        result = self.run_cli(plan(), "--repo-root", "/nonexistent/plan-root")
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
