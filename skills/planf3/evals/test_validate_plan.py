"""Focused mechanical checks for the engineering-plan contract; standard library only."""

from __future__ import annotations

import importlib.util
import re
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


if __name__ == "__main__":
    unittest.main()
