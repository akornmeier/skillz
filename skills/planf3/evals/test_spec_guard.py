"""End-to-end spec_guard.py tests on real temporary git repos; standard library only."""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "spec_guard.py"
sys.path.insert(0, str(SCRIPTS))
import course_parser  # noqa: E402
import spec_guard  # noqa: E402

LOCAL = ("--local-base", "main")
REMOTE = ("--base-remote", "origin", "--base-branch", "main")
BASE = [("ac-base", "Base text."), ("ac-keep", "Keep one."), ("ac-keep2", "Keep two.")]


def spec_html(criteria=BASE, amendments=(), modified="None", images=(), title="Fixture") -> str:
    """Valid strict plan; one line per criterion, row, and amendment so rebases merge cleanly."""
    items = "\n".join(f'<li class="criterion" id="{key}">{text}</li>' for key, text in criteria)
    rows = "\n".join(f'<tr><td><a href="#{key}">{key}</a></td><td><a href="#task-build">Build</a></td>'
                     f'<td><a href="#verify-build">Check</a></td></tr>' for key, _ in criteria)
    notes = "\n".join(f'<figure><img src="{src}" alt="Diagram"><figcaption>Diagram</figcaption></figure>'
                      for src in images)
    entries = "\n".join(f"<details><summary>{summary}</summary><p>{body}</p></details>"
                        for summary, body in amendments)
    return f"""<!doctype html><html lang="en"><head><title>{title}</title>
<style>:root {{ --bg: #000; --paper-2: #000; --ink: #fff; --muted: #fff;
--soft: #fff; --rule: #fff; --accent: #fff; --accent-tint: #000; }}</style>
</head><body><details class="meta"><summary>Metadata</summary><dl>
<dt>created</dt><dd>2026-01-01T00:00:00Z</dd>
<dt>modified</dt><dd>{modified}</dd>
<dt>commits</dt><dd>None</dd>
<dt>agent name</dt><dd>Fixture</dd>
<dt>session id</dt><dd>Fixture</dd>
<dt>back refs</dt><dd>None</dd>
<dt>forward refs</dt><dd>None</dd>
</dl></details>
<section id="purpose">Purpose.</section>
<section id="problem">Problem.</section>
<section id="solution">Solution.</section>
<section id="acceptance"><ul>
{items}
</ul></section>
<section id="coverage"><table><thead><tr><th>Criterion</th><th>Task</th><th>Verification</th></tr></thead><tbody>
{rows}
</tbody></table></section>
<section id="files">src/app.py</section>
<section id="phases"><div class="phase"><h3>Phase 1</h3>
<div class="task" id="task-build"><h4>Build</h4>
<div class="verification" id="verify-build"><dl>
<dt>Cases</dt><dd class="cases">Happy path.</dd>
<dt>Command</dt><dd class="command"><code>make test</code></dd>
<dt>Expected</dt><dd class="expected">Exit 0.</dd>
<dt>Evidence</dt><dd class="evidence">Not run.</dd>
</dl></div></div></div></section>
<section id="validation">make test</section>
<section id="notes">Notes.
{notes}
</section>
<section id="amendments">
{entries}
</section></body></html>
"""


def course_md(north_star="Ship reliable widgets.", non_goal="No mobile app.", inferred=True, status="Active",
              area="src/", decision="Use Postgres") -> str:
    marker = " Inferred — needs developer review" if inferred else ""
    return f"""# Project Course

## North Star
{north_star}

## Milestones
| Milestone | Status | Spec | Notes |
|---|---|---|---|
| M1 Widgets | {status} | specs/s.html | first cut |

## Non-Goals
- {non_goal}
- No desktop app.{marker}

## Protected Boundaries
- `.github/workflows/`
- `/infra/`
- `Makefile`
- `db/migrations/*.sql`

## Precedence
1. Safety before speed.
2. Small reversible changes.

## Area Map
| Area | Paths | Verification | Invariants |
|---|---|---|---|
| App | {area} | make test | none |

## Decision Log
| ID | Date | Status | Decision | ADR |
|---|---|---|---|---|
| D-001 | 2026-01-01 | Accepted | {decision} | docs/adr/0001-postgres.md |
| D-002 | 2026-01-02 | Accepted | Use a queue | docs/adr/0002-queue.md |
"""


def course_files(**kwargs) -> dict:
    return {"specs/COURSE.md": course_md(**kwargs), "docs/adr/0001-postgres.md": "# ADR 1\n\nStatus: Accepted\n",
            "docs/adr/0002-queue.md": "# ADR 2\n\nStatus: Accepted\n", ".github/workflows/ci.yml": "on: push\n",
            "infra/main.tf": "# infra\n", "Makefile": "test:\n\ttrue\n",
            "db/migrations/001.sql": "create table a (id int);\n", "src/app.py": "print('app')\n"}


@contextlib.contextmanager
def working_dir(path: Path):
    previous = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class Sandbox:
    """Hermetic git environment: temp HOME, no system config, fixed identity and default branch."""

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="spec-guard-test-")
        self.root = Path(self._tmp.name).resolve()
        home = self.root / "home"
        home.mkdir()
        self.env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        self.env.update(HOME=str(home), XDG_CONFIG_HOME=str(home / ".config"), GIT_CONFIG_NOSYSTEM="1",
                        GIT_CONFIG_GLOBAL=str(home / ".gitconfig"), GIT_TERMINAL_PROMPT="0")
        for key, value in (("user.name", "Fixture"), ("user.email", "fixture@example.com"),
                           ("init.defaultBranch", "main"), ("advice.detachedHead", "false"),
                           ("commit.gpgsign", "false"), ("core.autocrlf", "false")):
            self.git(self.root, "config", "--global", key, value)

    def close(self) -> None:
        self._tmp.cleanup()

    def git(self, cwd: Path, *args: str, input: str | bytes | None = None, check: bool = True,
            env: dict | None = None) -> str:
        data = input.encode() if isinstance(input, str) else input
        proc = subprocess.run(["git", *args], cwd=cwd, input=data, capture_output=True,
                              env=dict(self.env, **(env or {})), timeout=60)
        if check and proc.returncode:
            raise AssertionError(f"git {' '.join(args)} failed: {proc.stderr.decode()}")
        return proc.stdout.decode().strip()

    def write(self, repo: Path, files: dict) -> None:
        for path, content in files.items():
            target = repo / path
            if content is None:
                if target.exists() or target.is_symlink():
                    target.unlink()
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                target.write_bytes(content)
            else:
                target.write_text(content, encoding="utf-8")

    def commit(self, repo: Path, files: dict | None = None, message: str = "change", amend: bool = False) -> str:
        self.write(repo, files or {})
        self.git(repo, "add", "-A")
        self.git(repo, "commit", "-q", "--allow-empty", "-m", message, *(["--amend"] if amend else []))
        return self.head(repo)

    def head(self, repo: Path, rev: str = "HEAD") -> str:
        return self.git(repo, "rev-parse", rev)

    def bare(self, name: str) -> Path:
        path = self.root / name
        self.git(self.root, "init", "-q", "--bare", str(path))
        return path

    def init_origin(self, files: dict) -> Path:
        origin = self.bare("origin.git")
        work = self.root / "work"
        self.git(self.root, "init", "-q", str(work))
        self.commit(work, files, "initial")
        self.git(work, "remote", "add", "origin", str(origin))
        self.git(work, "push", "-q", "origin", "main")
        return work

    def clone(self, name: str) -> Path:
        path = self.root / name
        self.git(self.root, "clone", "-q", str(self.root / "origin.git"), str(path))
        return path

    def refs(self, repo: Path, prefix: str = "refs/spec-guard/") -> list[str]:
        return self.git(repo, "for-each-ref", "--format=%(refname)", prefix).splitlines()

    def entry(self, repo: Path, rev: str, path: str) -> str:
        line = self.git(repo, "ls-tree", rev, "--", path)
        mode, _, rest = line.partition(" ")
        return f"{mode}:{rest.split()[1]}" if line else "absent"

    def guard(self, repo: Path, *args: str) -> tuple[int, dict]:
        proc = subprocess.run([sys.executable, str(SCRIPT), *args, "--json"], cwd=repo, capture_output=True,
                              env=self.env, timeout=120)
        try:
            return proc.returncode, json.loads(proc.stdout.decode())
        except ValueError as exc:
            raise AssertionError(f"spec_guard {args} printed no JSON: {proc.stdout!r} {proc.stderr!r}") from exc

    def set_created_at(self, repo: Path, prefix: str, stamp: str) -> None:
        old = self.head(repo, f"{prefix}/start-tree")
        run_id = json.loads(self.git(repo, "cat-file", "blob", f"{old}:run-id.txt"))
        run_id["created_at"] = stamp
        blob = self.git(repo, "hash-object", "-w", "--stdin", input=json.dumps(run_id))
        env = {"GIT_INDEX_FILE": str(self.root / "fixture-index")}
        self.git(repo, "read-tree", old, env=env)
        self.git(repo, "update-index", "--cacheinfo", f"100644,{blob},run-id.txt", env=env)
        new = self.git(repo, "write-tree", env=env)
        self.git(repo, "update-ref", f"{prefix}/start-tree", new, old)


class SpecGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.box = Sandbox()
        self.addCleanup(self.box.close)

    def guard(self, repo: Path, *args: str, code: int | None = None) -> dict:
        rc, data = self.box.guard(repo, *args)
        if code is not None:
            self.assertEqual(rc, code, json.dumps(data, indent=1)[:6000])
        return data

    def ids(self, data: dict) -> tuple[str, ...]:
        return ("--guard-prefix", data["guard_prefix"], "--invocation-id", data["invocation_id"])

    def inprocess(self, repo: Path, *argv: str) -> tuple[int, dict]:
        out = io.StringIO()
        with mock.patch.dict(os.environ, self.box.env, clear=True), working_dir(repo), \
                contextlib.redirect_stdout(out):
            code = spec_guard.main([*argv, "--json"])
        return code, json.loads(out.getvalue())

    # (1)
    def test_01_exact_candidate_skip_late_activation_and_resume(self) -> None:
        box = self.box
        work = box.init_origin({"src/app.py": "print(1)\n"})
        box.git(work, "checkout", "-q", "-b", "topic")
        published = box.commit(work, {"src/app.py": "print(2)\n"})
        box.git(work, "push", "-q", "origin", "topic")

        skipped = self.guard(work, "pin", *REMOTE, "--push-remote", "origin", code=0)
        self.assertEqual(skipped["status"], "guard: n/a")
        for key in ("prior_runs", "initial_head_sha", "initial_merge_base", "cand_sha", "push_endpoint",
                    "observed_remote_sha"):
            self.assertIn(key, skipped)
        self.assertEqual((skipped["cand_sha"], skipped["observed_remote_sha"]), (published, published))
        self.assertEqual(skipped["push_endpoint"], str(box.root / "origin.git"))
        self.assertEqual(box.refs(work), [])

        code_only = box.commit(work, {"src/app.py": "print(3)\n"})
        skipped = self.guard(work, "pin", *REMOTE, "--repo", "org/repo", "--pr", "7", "--branch", "topic",
                             "--head-sha", published, "--cand-sha", code_only, code=0)
        self.assertEqual((skipped["status"], skipped["cand_sha"]), ("guard: n/a", code_only))
        outgoing = box.commit(work, {"specs/first.html": spec_html()}, "first spec")
        caught = self.guard(work, "pin", *REMOTE, "--repo", "org/repo", "--pr", "7", "--branch", "topic",
                            "--head-sha", published, "--cand-sha", outgoing, code=0)
        self.assertEqual((caught["status"], caught["cand_sha"]), ("pinned", outgoing))
        self.assertEqual(caught["bound_specs"], ["specs/first.html"])
        self.guard(work, "cleanup", *self.ids(caught), code=0)

        # Late activation keeps the run-start baseline so same-run drafted criteria never freeze.
        box.git(work, "checkout", "-q", "-b", "late", "main")
        skipped = self.guard(work, "pin", *LOCAL, code=0)
        self.assertEqual(skipped["status"], "guard: n/a")
        box.commit(work, {"specs/late.html": spec_html([("ac-late", "Draft one.")])}, "draft")
        active = self.guard(work, "pin", *LOCAL, "--run-start-head", skipped["initial_head_sha"],
                            "--run-start-merge-base", skipped["initial_merge_base"], code=0)
        self.assertEqual(active["status"], "pinned")
        prefix = active["guard_prefix"]
        self.assertEqual(box.head(work, f"{prefix}/start"), skipped["initial_head_sha"])
        self.assertEqual(box.head(work, f"{prefix}/merge-base"), skipped["initial_merge_base"])
        tree = box.git(work, "ls-tree", "-r", "--name-only", f"{prefix}/start-tree").splitlines()
        self.assertNotIn("specs/late.html", tree)
        self.assertEqual(box.git(work, "cat-file", "blob", f"{prefix}/start-tree:bound-specs.txt"), "specs/late.html")
        box.commit(work, {"specs/late.html": spec_html([("ac-late", "Draft two, revised.")])}, "revise")
        ids = self.ids(active)
        self.guard(work, "check", "--stage", "pre-commit", *LOCAL, *ids, code=0)
        self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=0)
        self.guard(work, "rebase-pin", *LOCAL, *ids, code=0)
        self.assertTrue(self.guard(work, "survival", *LOCAL, *ids, code=0)["cleared_pre_rebase"])
        self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=0)
        self.guard(work, "cleanup", *ids, code=0)
        self.assertEqual(box.refs(work), [])

        # Resuming a bound run after deleting its sole spec must not skip.
        box.git(work, "checkout", "-q", "-b", "solo", "main")
        box.commit(work, {"specs/solo.html": spec_html()}, "solo spec")
        pinned = self.guard(work, "pin", *LOCAL, code=0)
        box.commit(work, {"specs/solo.html": None}, "delete solo")
        fresh = self.guard(work, "pin", *LOCAL, code=2)
        self.assertEqual(fresh["status"], "resume_required")
        resumed = self.guard(work, "pin", *LOCAL, "--resume", *self.ids(pinned), code=0)
        self.assertEqual((resumed["status"], resumed["bound_specs"]), ("resumed", ["specs/solo.html"]))
        check = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *self.ids(pinned), code=1)
        self.assertEqual(check["bound_spec_deletions"], [{"spec": "specs/solo.html", "status": "unapproved"}])

    # (2)
    def test_02_isolated_temp_ref_fetch_and_pull_head(self) -> None:
        box = self.box
        work = box.init_origin({"src/app.py": "1\n"})
        box.git(work, "fetch", "-q", "origin")
        fetch_head = (work / ".git" / "FETCH_HEAD").read_bytes()
        tracking = box.head(work, "refs/remotes/origin/main")
        other = box.clone("other")
        upstream = box.commit(other, {"src/app.py": "2\n"}, "upstream")
        box.git(other, "tag", "v9")
        box.git(other, "push", "-q", "origin", "main", "--tags")
        box.git(other, "checkout", "-q", "-b", "feature")
        pr_head = box.commit(other, {"specs/feature.html": spec_html()}, "feature spec")
        box.git(other, "push", "-q", "origin", "HEAD:refs/pull/42/head")
        self.assertNotEqual(box.git(work, "cat-file", "-t", pr_head, check=False), "commit")

        mismatch = self.guard(work, "pin", *REMOTE, "--repo", "org/repo", "--pr", "42", "--branch", "feature",
                              "--head-sha", "1" * 40, code=2)
        self.assertIn("does not match", mismatch["error"])
        pinned = self.guard(work, "pin", *REMOTE, "--repo", "org/repo", "--pr", "42", "--branch", "feature",
                            "--head-sha", pr_head, code=0)
        self.assertEqual((pinned["base_sha"], pinned["cand_sha"]), (upstream, pr_head))
        self.assertEqual(pinned["bound_specs"], ["specs/feature.html"])
        self.assertTrue(pinned["guard_prefix"].startswith("refs/spec-guard/pr/org%2Frepo/42/"))
        self.assertEqual((work / ".git" / "FETCH_HEAD").read_bytes(), fetch_head)
        self.assertEqual(box.head(work, "refs/remotes/origin/main"), tracking)
        self.assertEqual(box.git(work, "tag", "-l"), "")
        self.assertEqual(box.refs(work, "refs/spec-guard/tmp/"), [])
        check = self.guard(work, "check", "--stage", "final", *REMOTE, *self.ids(pinned), "--repo", "org/repo",
                           "--pr", "42", "--head-sha", pr_head, code=0)
        self.assertEqual(check["cand_sha"], pr_head)
        self.assertEqual(box.refs(work, "refs/spec-guard/tmp/"), [])

    # (3)
    def test_03_direct_blob_reads_skip_hooks_filters_and_reject_links(self) -> None:
        box = self.box
        hook_marker, smudge_marker = box.root / "hook-fired", box.root / "smudge-fired"
        work = box.root / "work"
        box.git(box.root, "init", "-q", str(work))
        box.git(work, "config", "filter.boom.clean", "cat")
        box.git(work, "config", "filter.boom.smudge", f"sh -c 'touch {smudge_marker}; exit 1'")
        box.git(work, "config", "filter.boom.required", "true")
        hook = work / ".git" / "hooks" / "post-checkout"
        hook.parent.mkdir(parents=True, exist_ok=True)
        hook.write_text(f"#!/bin/sh\ntouch {hook_marker}\nexit 1\n")
        hook.chmod(0o755)
        image = b"\x89PNG\r\n\x1a\nfixture"
        box.commit(work, {".gitattributes": "specs/*.html filter=boom\nspecs/** export-ignore\n",
                          "specs/s.html": spec_html(images=["diagram.png"]), "specs/diagram.png": image,
                          "src/app.py": "1\n"}, "initial")

        # Positive controls: a real checkout fires both the hook and the smudge filter.
        box.git(work, "checkout", "-q", "-b", "topic", check=False)
        self.assertTrue(hook_marker.exists())
        (work / "specs" / "s.html").unlink()
        box.git(work, "checkout", "--", "specs/s.html", check=False)
        self.assertTrue(smudge_marker.exists())
        hook_marker.unlink()
        smudge_marker.unlink()
        quiet = ("-c", "core.hooksPath=/dev/null", "-c", "filter.boom.smudge=cat")

        criteria = BASE + [("ac-image", "Diagram stays.")]
        box.write(work, {"specs/s.html": spec_html(criteria, images=["diagram.png"])})
        os.symlink("app.py", work / "src" / "link")  # unrelated symlink must not block
        box.commit(work, message="branch edit")
        pinned = self.guard(work, "pin", *LOCAL, code=0)
        self.guard(work, "check", "--stage", "pre-commit", *LOCAL, *self.ids(pinned), code=0)
        ok = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *self.ids(pinned), code=0)
        self.assertEqual((ok["validation"], ok["symlink_rejected"]), ([], []))
        self.assertFalse(hook_marker.exists() or smudge_marker.exists())

        box.git(work, *quiet, "checkout", "-q", "-b", "sym", "main")
        os.symlink("/etc/hosts", work / "specs" / "evil.html")
        os.symlink("/etc/hosts", work / "specs" / "outside.png")
        box.write(work, {"specs/s.html": spec_html(criteria, images=["outside.png"])})
        box.commit(work, message="symlinks")
        pinned = self.guard(work, "pin", *LOCAL, code=0)
        rejected = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *self.ids(pinned), code=1)
        paths = {item["path"] for item in rejected["symlink_rejected"]}
        self.assertEqual(paths, {"specs/evil.html", "specs/outside.png"})
        self.assertIn("symlink_rejected", rejected["violations"])

        box.git(work, *quiet, "checkout", "-q", "-b", "gitlink", "main")
        box.git(work, "update-index", "--add", "--cacheinfo", f"160000,{box.head(work)},specs/vendor.html")
        box.git(work, "commit", "-q", "-m", "gitlink")
        pinned = self.guard(work, "pin", *LOCAL, code=0)
        rejected = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *self.ids(pinned), code=1)
        self.assertEqual([item["path"] for item in rejected["unsupported_tree_entry"]], ["specs/vendor.html"])
        self.assertFalse(hook_marker.exists() or smudge_marker.exists())

    # (4)
    def test_04_sparse_checkout_precommit_reads_index_blobs(self) -> None:
        box = self.box
        work = box.init_origin({"specs/s.html": spec_html(), "src/app.py": "1\n"})
        box.git(work, "checkout", "-q", "-b", "topic")
        pinned = self.guard(work, "pin", *LOCAL, "--spec", "specs/s.html", code=0)
        box.git(work, "sparse-checkout", "set", "--cone", "src")
        self.assertFalse((work / "specs" / "s.html").exists())

        def stage(text: str) -> None:
            blob = box.git(work, "hash-object", "-w", "--stdin", input=text)
            box.git(work, "update-index", "--cacheinfo", f"100644,{blob},specs/s.html")

        stage(spec_html(BASE + [("ac-sparse", "Staged without a worktree file.")]))
        ok = self.guard(work, "check", "--stage", "pre-commit", *LOCAL, *self.ids(pinned), code=0)
        self.assertEqual((ok["bound_specs"], ok["validation"], ok["unstaged_specs"]), (["specs/s.html"], [], []))
        stage(spec_html().replace('id="coverage"', 'id="gone"'))
        broken = self.guard(work, "check", "--stage", "pre-commit", *LOCAL, *self.ids(pinned), code=1)
        codes = {item["code"] for item in broken["validation"][0]["diagnostics"]}
        self.assertIn("PF3_SECTION_MISSING", codes)
        self.assertFalse((work / "specs" / "s.html").exists())

    # (5)
    def test_05_percent_first_escaping_and_namespace_isolation(self) -> None:
        box = self.box
        work = box.init_origin(course_files())
        prefixes = {}
        for branch in ("a/b", "a%2Fb", "pr-42"):
            box.git(work, "checkout", "-q", "-b", branch, "main")
            pinned = self.guard(work, "pin", *LOCAL, code=0)
            prefixes[branch] = (pinned["guard_prefix"], pinned["invocation_id"])
        box.git(work, "checkout", "-q", "-b", "feature", "main")
        pinned = self.guard(work, "pin", *LOCAL, "--repo", "org/repo", "--pr", "42", "--branch", "feature",
                            "--checkout-owns-pr", code=0)
        prefixes["pr"] = (pinned["guard_prefix"], pinned["invocation_id"])
        expected = {"a/b": "refs/spec-guard/branch/a%2Fb/", "a%2Fb": "refs/spec-guard/branch/a%252Fb/",
                    "pr-42": "refs/spec-guard/branch/pr-42/", "pr": "refs/spec-guard/pr/org%2Frepo/42/"}
        for key, start in expected.items():
            prefix, invocation = prefixes[key]
            self.assertEqual(prefix, start + invocation)
        self.assertEqual(len(box.refs(work)), 12)

        again = self.guard(work, "pin", *LOCAL, "--branch", "a/b", code=2)
        self.assertEqual([run["guard_prefix"] for run in again["prior_runs"]], [prefixes["a/b"][0]])
        for key in ("pr-42", "pr"):
            prefix, invocation = prefixes[key]
            self.guard(work, "cleanup", "--guard-prefix", prefix, "--invocation-id", invocation, code=0)
            self.assertEqual(box.refs(work, prefix + "/"), [])
        remaining = box.refs(work)
        self.assertEqual(len(remaining), 6)
        self.assertTrue(all(ref.startswith((expected["a/b"], expected["a%2Fb"])) for ref in remaining))

    # (6)
    def test_06_unchecked_out_pr_binding_and_foreign_spec_negative(self) -> None:
        box = self.box
        work = box.init_origin({"specs/old.html": spec_html(), "src/app.py": "1\n"})
        contributor = box.clone("contributor")
        box.git(contributor, "checkout", "-q", "-b", "feat")
        pr5 = box.commit(contributor, {"specs/new.html": spec_html()}, "spec pr")
        box.git(contributor, "push", "-q", "origin", "HEAD:refs/pull/5/head")
        box.git(contributor, "checkout", "-q", "-b", "code", "main")
        pr6 = box.commit(contributor, {"src/app.py": "2\n"}, "code pr")
        box.git(contributor, "push", "-q", "origin", "HEAD:refs/pull/6/head")

        box.git(work, "checkout", "-q", "-b", "unrelated")
        box.write(work, {"specs/foreign.html": spec_html(title="Foreign")})
        box.git(work, "add", "specs/foreign.html")
        bound = self.guard(work, "pin", *REMOTE, "--repo", "org/repo", "--pr", "5", "--branch", "feat",
                           "--head-sha", pr5, code=0)
        self.assertEqual((bound["status"], bound["bound_specs"]), ("pinned", ["specs/new.html"]))
        skipped = self.guard(work, "pin", *REMOTE, "--repo", "org/repo", "--pr", "6", "--branch", "code",
                             "--head-sha", pr6, code=0)
        self.assertEqual((skipped["status"], skipped["cand_sha"]), ("guard: n/a", pr6))
        self.assertNotIn("bound_specs", skipped)
        self.assertEqual(box.refs(work, "refs/spec-guard/pr/org%2Frepo/6/"), [])

    # (7)
    def test_07_dual_namespace_prior_runs_before_skip_and_resume(self) -> None:
        box = self.box
        work = box.init_origin({"src/app.py": "1\n"})
        box.git(work, "checkout", "-q", "-b", "topic")
        first = box.commit(work, {"specs/t.html": spec_html()}, "spec")
        pinned = self.guard(work, "pin", *LOCAL, code=0)
        invocation = pinned["invocation_id"]
        self.assertTrue(pinned["guard_prefix"].endswith("/" + invocation))
        run_id = json.loads(box.git(work, "cat-file", "blob", f"{pinned['guard_prefix']}/start-tree:run-id.txt"))
        self.assertEqual(run_id["invocation_id"], invocation)
        self.assertTrue(run_id["created_at"].endswith("Z"))

        box.git(work, "checkout", "-q", "main")
        pr_args = (*LOCAL, "--repo", "org/repo", "--pr", "9", "--branch", "topic")
        lost = self.guard(work, "pin", *pr_args, "--head-sha", first, code=2)
        self.assertEqual([run["guard_prefix"] for run in lost["prior_runs"]], [pinned["guard_prefix"]])

        moved = self.guard(work, "bind-pr", *self.ids(pinned), "--repo", "org/repo", "--pr", "9", code=0)
        self.assertEqual(moved["guard_prefix"], f"refs/spec-guard/pr/org%2Frepo/9/{invocation}")
        self.assertEqual(box.refs(work, "refs/spec-guard/branch/"), [])
        box.git(work, "checkout", "-q", "topic")
        deleted = box.commit(work, {"specs/t.html": None}, "drop the only spec")
        box.git(work, "checkout", "-q", "main")

        fresh = self.guard(work, "pin", *pr_args, "--head-sha", deleted, code=2)
        self.assertEqual(fresh["status"], "resume_required")
        self.assertEqual(fresh["prior_runs"][0]["guard_prefix"], moved["guard_prefix"])
        resumed = self.guard(work, "pin", *pr_args, "--head-sha", deleted, "--resume", *self.ids(moved), code=0)
        self.assertEqual((resumed["status"], resumed["bound_specs"]), ("resumed", ["specs/t.html"]))
        wrong = self.guard(work, "pin", *pr_args, "--head-sha", deleted, "--resume", "--guard-prefix",
                           moved["guard_prefix"], "--invocation-id", "not-the-id", code=2)
        self.assertEqual(wrong["status"], "error")
        missing = "refs/spec-guard/pr/org%2Frepo/9/missing"
        self.guard(work, "pin", *pr_args, "--head-sha", deleted, "--resume", "--guard-prefix", missing,
                   "--invocation-id", "missing", code=2)
        self.guard(work, "check", "--stage", "final", *LOCAL, *self.ids(moved), "--head-sha", deleted, code=1)

    # (8)
    def test_08_start_tree_precedence_and_mid_run_union(self) -> None:
        box = self.box
        work = box.init_origin({"src/app.py": "1\n"})
        box.git(work, "checkout", "-q", "-b", "topic")
        box.commit(work, {"specs/a.html": spec_html([("ac-one", "Committed text.")]),
                          "specs/b.html": spec_html([("ac-two", "B text.")])}, "specs")
        dirty = spec_html([("ac-one", "Dirty pre-existing text.")])
        box.write(work, {"specs/a.html": dirty})
        pinned = self.guard(work, "pin", *LOCAL, code=0)
        ids = self.ids(pinned)
        prefix = pinned["guard_prefix"]
        self.assertEqual(pinned["bound_specs"], ["specs/a.html", "specs/b.html"])
        tree = box.git(work, "ls-tree", "-r", "--name-only", f"{prefix}/start-tree").splitlines()
        self.assertIn("specs/a.html", tree)
        self.assertNotIn("specs/b.html", tree)
        self.assertEqual(box.git(work, "cat-file", "blob", f"{prefix}/start-tree:specs/a.html"), dirty.strip())

        box.commit(work, message="commit the pre-existing edit")
        ok = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=0)
        self.assertEqual(ok["accepted_criteria_changed"], [])
        box.commit(work, {"specs/a.html": spec_html([("ac-one", "Changed again.")])}, "rewrite")
        changed = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=1)
        self.assertEqual([(item["baseline"], item["from_text"]) for item in changed["accepted_criteria_changed"]],
                         [("run_start", "Dirty pre-existing text.")])
        box.git(work, "reset", "-q", "--hard", "HEAD~1")

        box.commit(work, {"specs/c.html": spec_html([("ac-three", "C draft.")])}, "mid-run spec")
        union = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=0)
        self.assertEqual(union["bound_specs"], ["specs/a.html", "specs/b.html", "specs/c.html"])
        self.assertEqual(box.git(work, "cat-file", "blob", f"{prefix}/start-tree:bound-specs.txt").splitlines(),
                         ["specs/a.html", "specs/b.html", "specs/c.html"])
        box.commit(work, {"specs/c.html": spec_html([("ac-three", "C draft, revised.")])}, "same-run edit")
        self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=0)

    # (9)
    def test_09_divergent_rebase_upstream_base_and_pending_checkpoint(self) -> None:
        box = self.box
        work = box.init_origin({"specs/s.html": spec_html(), "src/app.py": "1\n"})
        upstream = box.clone("upstream")
        box.git(work, "checkout", "-q", "-b", "topic")
        box.commit(work, {"specs/s.html": spec_html(BASE + [("ac-branch", "Branch criterion.")])}, "branch")
        box.git(work, "push", "-q", "origin", "topic")
        pinned = self.guard(work, "pin", *REMOTE, "--push-remote", "origin", code=0)
        ids = self.ids(pinned)
        amended = [("ac-base", "Base text, clarified.")] + BASE[1:]
        box.commit(upstream, {"specs/s.html": spec_html(amended, [("2026-02-01 Clarify ac-base",
                                                                   "Clarified ac-base wording for reviewers.")])})
        box.git(upstream, "push", "-q", "origin", "main")

        stale = self.guard(work, "check", "--stage", "pre-push", *REMOTE, *ids, code=0)
        self.assertTrue(stale["rebase_recommended"])
        self.assertEqual(stale["validation"], [])
        self.assertEqual({(item["criterion"], item["baseline"], item["status"])
                          for item in stale["accepted_criteria_changed"]}, {("ac-base", "base_sha", "upstream_base")})

        kept = box.head(work)
        lease = ("--push-remote", "origin", "--branch", "topic", "--pre-rebase-head", kept)
        checkpoint = self.guard(work, "rebase-pin", *REMOTE, *ids, *lease, code=0)
        self.assertEqual(checkpoint["pending_lease"], kept)
        self.guard(work, "rebase-pin", *REMOTE, *ids, *lease, code=2)
        self.guard(work, "bind-pr", *ids, "--repo", "org/repo", "--pr", "3", code=2)
        box.git(work, "rebase", "-q", checkpoint["base_sha"])
        survived = self.guard(work, "survival", *REMOTE, *ids, code=0)
        self.assertTrue(survived["cleared_pre_rebase"])
        self.assertEqual(box.refs(work, pinned["guard_prefix"] + "/pre-rebase"), [])
        rebased = self.guard(work, "check", "--stage", "pre-push", *REMOTE, *ids, code=0)
        self.assertFalse(rebased["rebase_recommended"])
        self.assertEqual(rebased["validation"], [])
        self.assertEqual([(item["criterion"], item["baseline"], item["status"])
                          for item in rebased["accepted_criteria_changed"]], [("ac-base", "run_start", "upstream_base")])
        box.git(work, "push", "-q", f"--force-with-lease=refs/heads/topic:{checkpoint['pending_lease']}",
                checkpoint["push_endpoint"], f"{rebased['cand_sha']}:refs/heads/topic")
        self.assertEqual(box.head(box.root / "origin.git", "refs/heads/topic"), rebased["cand_sha"])

    def test_09_survival_catches_drops_and_rewrites_then_clears(self) -> None:
        box = self.box
        work = box.init_origin({"specs/s.html": spec_html()})
        box.git(work, "checkout", "-q", "-b", "topic")
        branch = BASE + [("ac-branch", "Branch criterion.")]
        amendment = [("2026-02-01 Added ac-branch", "Added ac-branch to cover retries.")]
        modified = "None; 2026-02-01 branch edit"
        box.commit(work, {"specs/s.html": spec_html(branch, amendment, modified)}, "branch work")
        pinned = self.guard(work, "pin", *LOCAL, code=0)
        ids = self.ids(pinned)
        same_run = branch + [("ac-same", "Same-run draft.")]
        pre = box.commit(work, {"specs/s.html": spec_html(same_run, amendment, modified)}, "same run")
        self.guard(work, "rebase-pin", *LOCAL, *ids, code=0)

        rewritten = [(key, "Branch criterion, quietly changed." if key == "ac-branch" else text)
                     for key, text in same_run]
        mutated_same = [(key, "Same-run draft, mangled." if key == "ac-same" else text) for key, text in same_run]
        cases = [
            (spec_html([item for item in same_run if item[0] != "ac-branch"], amendment, modified),
             "criterion_dropped", "run_start"),
            (spec_html(rewritten, amendment, modified), "criterion_rewritten", "run_start"),
            (spec_html(same_run, (), modified), "amendment_missing", "run_start"),
            (spec_html(same_run, amendment, "None"), "metadata_dropped", "run_start"),
            (spec_html(mutated_same, amendment, modified), "criterion_rewritten", "pre_rebase"),
        ]
        for text, kind, source in cases:
            with self.subTest(kind=kind, source=source):
                box.commit(work, {"specs/s.html": text}, "bad rebase", amend=True)
                failed = self.guard(work, "survival", *LOCAL, *ids, code=1)
                self.assertIn((kind, source), {(item["kind"], item["source"]) for item in failed["survival"]})
                self.assertEqual(len(box.refs(work, pinned["guard_prefix"] + "/")), 5)
                box.git(work, "reset", "-q", "--hard", pre)

        cleared = self.guard(work, "survival", *LOCAL, *ids, code=0)  # unchanged tree, as after rebase --abort
        self.assertTrue(cleared["cleared_pre_rebase"])
        box.commit(work, {"specs/s.html": spec_html(mutated_same, amendment, modified)}, "same-run edit")
        self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=0)

    # (10)
    def test_10_unstaged_spec_allowed_precommit_blocked_prepush(self) -> None:
        box = self.box
        work = box.init_origin(course_files())
        box.git(work, "checkout", "-q", "-b", "topic")
        pinned = self.guard(work, "pin", *LOCAL, code=0)
        box.write(work, {"specs/draft.html": spec_html([("ac-draft", "Draft.")]), "src/app.py": "2\n"})
        box.git(work, "add", "src/app.py")
        early = self.guard(work, "check", "--stage", "pre-commit", *LOCAL, *self.ids(pinned), code=0)
        self.assertEqual(early["unstaged_specs"], ["specs/draft.html"])
        box.git(work, "commit", "-q", "-m", "code only")
        late = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *self.ids(pinned), code=1)
        self.assertEqual(late["bound_spec_deletions"], [{"spec": "specs/draft.html", "status": "unapproved"}])

    def test_10_push_endpoint_pushurl_suffix_and_unreachable(self) -> None:
        box = self.box
        work = box.init_origin({"src/app.py": "1\n"})
        mirror = box.bare("mirror.git")
        box.git(work, "checkout", "-q", "-b", "topic")
        on_origin = box.commit(work, {"src/app.py": "2\n"})
        box.git(work, "push", "-q", "origin", "topic")
        on_mirror = box.commit(work, {"src/app.py": "3\n"})
        box.git(work, "push", "-q", str(mirror), "topic")
        box.git(work, "config", "remote.origin.pushurl", "pushalias:mirror")
        box.git(work, "config", f"url.{mirror}.pushInsteadOf", "pushalias:mirror")
        observed = self.guard(work, "pin", *LOCAL, "--push-remote", "origin", "--branch", "topic", code=0)
        self.assertEqual((observed["push_endpoint"], observed["observed_remote_sha"]), (str(mirror), on_mirror))
        self.assertNotEqual(observed["observed_remote_sha"], on_origin)
        outgoing = box.commit(work, {"src/app.py": "4\n"})
        box.git(work, "push", "-q", observed["push_endpoint"], f"{outgoing}:refs/heads/topic")
        self.assertEqual(box.head(mirror, "refs/heads/topic"), outgoing)
        self.assertEqual(box.head(box.root / "origin.git", "refs/heads/topic"), on_origin)

        box.git(work, "remote", "add", "multi", str(box.root / "origin.git"))
        box.git(work, "remote", "set-url", "--add", "--push", "multi", str(box.root / "origin.git"))
        box.git(work, "remote", "set-url", "--add", "--push", "multi", str(mirror))
        multi = self.guard(work, "pin", *LOCAL, "--push-remote", "multi", "--branch", "topic", code=2)
        self.assertEqual(len(multi["push_urls"]), 2)

        box.git(work, "remote", "add", "plain", str(box.root / "origin.git"))
        box.git(work, "push", "-q", "plain", "HEAD:refs/heads/other/refs/heads/solo")
        suffix = self.guard(work, "pin", *LOCAL, "--push-remote", "plain", "--branch", "solo", code=0)
        self.assertIsNone(suffix["observed_remote_sha"])
        box.git(work, "remote", "add", "dead", str(box.root / "missing.git"))
        self.guard(work, "pin", *LOCAL, "--push-remote", "dead", "--branch", "topic", code=2)

    def test_10_leases_divergence_and_cherry_pick_recovery(self) -> None:
        box = self.box
        work = box.init_origin({"src/app.py": "1\n", "README": "r\n"})
        collab = box.clone("collab")
        box.git(work, "checkout", "-q", "-b", "topic")
        kept = box.commit(work, {"src/topic.py": "t1\n"}, "topic")
        box.git(work, "push", "-q", "origin", "topic")
        box.commit(collab, {"README": "r2\n"}, "upstream one")
        box.git(collab, "push", "-q", "origin", "main")
        endpoint = str(box.root / "origin.git")
        gate = (*REMOTE, "--push-remote", "origin", "--branch", "topic")

        first = self.guard(work, "pin", *gate, "--pre-rebase-head", kept, code=0)
        self.assertEqual((first["status"], first["pending_lease"]), ("guard: n/a", kept))
        box.git(work, "rebase", "-q", first["base_sha"])
        box.commit(collab, {"README": "r3\n"}, "upstream two")
        box.git(collab, "push", "-q", "origin", "main")
        second = self.guard(work, "pin", *gate, "--pre-rebase-head", kept, "--pending-lease", kept, code=0)
        box.git(work, "rebase", "-q", second["base_sha"])
        post = box.commit(work, {"src/post.py": "p\n"}, "post-rebase work")

        box.git(collab, "fetch", "-q", "origin", "topic")
        box.git(collab, "checkout", "-q", "-b", "topic", "FETCH_HEAD")
        collaborator = box.commit(collab, {"src/collab.py": "c\n"}, "collaborator")
        box.git(collab, "push", "-q", "origin", "topic")
        plain = subprocess.run(["git", "push", endpoint, "HEAD:refs/heads/topic"], cwd=work, env=box.env,
                               capture_output=True)
        self.assertNotEqual(plain.returncode, 0)
        leased = subprocess.run(["git", "push", f"--force-with-lease=refs/heads/topic:{kept}", endpoint,
                                 "HEAD:refs/heads/topic"], cwd=work, env=box.env, capture_output=True)
        self.assertNotEqual(leased.returncode, 0)
        for extra in (("--pending-lease", kept), (), ("--pending-lease", collaborator)):
            with self.subTest(extra=extra):
                refused = self.guard(work, "pin", *gate, "--pre-rebase-head", kept, *extra, code=1)
                self.assertTrue(refused["remote_head_diverged"])

        box.git(work, "branch", "backup", post)
        box.git(work, "reset", "-q", "--hard", kept)
        box.git(work, "fetch", "-q", "origin", "topic")
        box.git(work, "merge", "-q", "--ff-only", collaborator)
        recovered = self.guard(work, "pin", *gate, "--pre-rebase-head", collaborator, code=0)
        box.git(work, "rebase", "-q", recovered["base_sha"])
        box.git(work, "cherry-pick", "backup")
        box.git(work, "push", "-q", f"--force-with-lease=refs/heads/topic:{recovered['pending_lease']}", endpoint,
                "HEAD:refs/heads/topic")
        published = box.git(box.root / "origin.git", "ls-tree", "-r", "--name-only", "refs/heads/topic").splitlines()
        self.assertTrue({"src/collab.py", "src/post.py", "src/topic.py"} <= set(published))

        # Remote rolls back against an existing pending lease.
        tip = box.head(work)
        held = self.guard(work, "pin", *gate, "--pre-rebase-head", tip, code=0)["pending_lease"]
        box.git(collab, "push", "-q", "--force", "origin", f"{collaborator}:refs/heads/topic")
        rolled = self.guard(work, "pin", *gate, "--pre-rebase-head", tip, "--pending-lease", held, code=1)
        self.assertTrue(rolled["remote_head_diverged"])

        # The same refusals hold for a guarded rebase-pin.
        box.git(work, "push", "-q", "--force", endpoint, "HEAD:refs/heads/topic")
        box.commit(work, {"specs/g.html": spec_html()}, "spec")
        box.git(work, "push", "-q", endpoint, "HEAD:refs/heads/topic")
        guarded = self.guard(work, "pin", *gate, code=0)
        kept = box.head(work)
        box.git(collab, "fetch", "-q", "origin", "topic")
        box.git(collab, "reset", "-q", "--hard", "FETCH_HEAD")
        rival = box.commit(collab, {"src/rival.py": "r\n"}, "rival")
        box.git(collab, "push", "-q", "origin", "topic")
        for extra in ((), ("--pending-lease", rival), ("--pending-lease", kept)):
            with self.subTest(guarded=extra):
                refused = self.guard(work, "rebase-pin", *gate, *self.ids(guarded), "--pre-rebase-head", kept,
                                     *extra, code=1)
                self.assertTrue(refused["remote_head_diverged"])
        self.assertEqual(box.refs(work, guarded["guard_prefix"] + "/pre-rebase"), [])

    def test_10_deleting_last_spec_needs_delete_spec_approval(self) -> None:
        box = self.box
        work = box.init_origin({"specs/s.html": spec_html(), "src/app.py": "1\n"})
        box.git(work, "checkout", "-q", "-b", "topic")
        box.commit(work, {"specs/s.html": None}, "delete the last spec")
        self.assertEqual(box.git(work, "ls-tree", "HEAD", "specs"), "")
        pinned = self.guard(work, "pin", *LOCAL, code=0)
        ids = self.ids(pinned)
        blocked = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=1)
        self.assertEqual(blocked["bound_spec_deletions"], [{"spec": "specs/s.html", "status": "unapproved"}])
        self.guard(work, "approve", *ids, "--delete-spec", "specs/s.html", "--reason", "user approved", code=0)
        allowed = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=0)
        self.assertEqual(allowed["bound_spec_deletions"], [{"spec": "specs/s.html", "status": "approved"}])

    def test_10_amend_and_delete_criterion_approvals_are_text_bound(self) -> None:
        box = self.box
        work = box.init_origin({"specs/s.html": spec_html()})
        box.git(work, "checkout", "-q", "-b", "topic")
        pinned = self.guard(work, "pin", *LOCAL, "--spec", "specs/s.html", code=0)
        ids = self.ids(pinned)
        first = [("2026-02-01 Amend ac-base", "Changed ac-base wording after review.")]
        box.commit(work, {"specs/s.html": spec_html([("ac-base", "Base text v2.")] + BASE[1:], first)}, "amend")
        blocked = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=1)
        self.assertEqual([item["status"] for item in blocked["accepted_criteria_changed"]], ["unapproved"])
        self.assertEqual(blocked["validation"], [])  # the agent-appended amendment satisfies the validator only
        self.guard(work, "approve", *ids, "--amend-criterion", "specs/s.html:ac-base", "--from-text", "Base text.",
                   "--to-text", "Base text v2.", "--reason", "user approved", code=0)
        approved = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=0)
        self.assertEqual([item["status"] for item in approved["accepted_criteria_changed"]], ["approved"])
        second = first + [("2026-02-02 Amend ac-base again", "Changed ac-base wording a second time.")]
        box.commit(work, {"specs/s.html": spec_html([("ac-base", "Base text v3.")] + BASE[1:], second)}, "again")
        self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=1)

        box.git(work, "reset", "-q", "--hard", "HEAD~1")
        dropped = first + [("2026-02-03 Remove ac-keep", "Removed ac-keep because it is obsolete.")]
        criteria = [("ac-base", "Base text v2."), BASE[2]]
        box.commit(work, {"specs/s.html": spec_html(criteria, dropped)}, "drop")
        removed = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=1)
        self.assertIn(("ac-keep", None, "unapproved"), {(item["criterion"], item["to_text"], item["status"])
                                                         for item in removed["accepted_criteria_changed"]})
        self.guard(work, "approve", *ids, "--delete-criterion", "specs/s.html:ac-keep", "--from-text", "Keep one.",
                   "--reason", "user approved", code=0)
        self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=0)

    def test_10_allow_path_binds_mode_and_oid(self) -> None:
        box = self.box
        work = box.init_origin(course_files())
        box.git(work, "checkout", "-q", "-b", "topic")
        pinned = self.guard(work, "pin", *LOCAL, code=0)
        ids = self.ids(pinned)
        path = "db/migrations/001.sql"
        before = box.entry(work, "main", path)
        box.commit(work, {path: "create table a (id bigint);\n"}, "edit migration")
        after = box.entry(work, "HEAD", path)
        hit = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=1)
        self.assertEqual([(item["path"], item["status"]) for item in hit["protected_path_hits"]], [(path, "unapproved")])
        self.guard(work, "approve", *ids, "--allow-path", path, "--from-entry", before, "--to-entry", after,
                   "--reason", "user asked for this migration", code=0)
        self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=0)

        box.git(work, "update-index", "--chmod=+x", path)
        box.git(work, "commit", "-q", "-m", "mode only")
        self.assertEqual(box.entry(work, "HEAD", path), after.replace("100644", "100755"))
        self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=1)
        box.git(work, "reset", "-q", "--hard", "HEAD~1")
        box.commit(work, {path: "create table a (id text);\n"}, "second edit")
        self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=1)
        box.git(work, "reset", "-q", "--hard", "HEAD~1")
        box.commit(work, {"db/migrations/002.sql": "create table b (id int);\n"}, "new migration")
        other = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=1)
        self.assertEqual({(item["path"], item["status"]) for item in other["protected_path_hits"]},
                         {(path, "approved"), ("db/migrations/002.sql", "unapproved")})

    # (11)
    def test_11_legacy_spec_warns_instead_of_failing(self) -> None:
        box = self.box
        legacy = "<!doctype html><html><head><title>Old</title></head><body><h1>Old plan</h1><p>Steps.</p>"
        work = box.init_origin({"specs/old.html": legacy + "</body></html>\n"})
        box.git(work, "checkout", "-q", "-b", "topic")
        box.commit(work, {"specs/old.html": legacy + "<p>More steps.</p></body></html>\n"}, "touch legacy")
        pinned = self.guard(work, "pin", *LOCAL, code=0)
        result = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *self.ids(pinned), code=0)
        self.assertEqual([item["code"] for item in result["warnings"]], ["legacy-format"])
        self.assertEqual(result["validation"], [])

    # (12)
    def test_12_bind_pr_resume_cleanup_interleaving_and_prune(self) -> None:
        box = self.box
        work = box.init_origin({"specs/s.html": spec_html(), "src/app.py": "1\n"})
        box.git(work, "checkout", "-q", "-b", "topic")
        box.commit(work, {"specs/s.html": spec_html(BASE + [("ac-branch", "Branch criterion.")])}, "branch")
        pinned = self.guard(work, "pin", *LOCAL, code=0)
        branch_prefix = pinned["guard_prefix"]
        self.guard(work, "rebase-pin", *LOCAL, *self.ids(pinned), code=0)
        self.guard(work, "bind-pr", *self.ids(pinned), "--repo", "org/repo", "--pr", "12", code=2)
        self.assertEqual(len(box.refs(work, branch_prefix + "/")), 5)
        self.guard(work, "survival", *LOCAL, *self.ids(pinned), code=0)
        moved = self.guard(work, "bind-pr", *self.ids(pinned), "--repo", "org/repo", "--pr", "12", code=0)
        self.assertEqual(box.refs(work, "refs/spec-guard/branch/"), [])
        self.assertEqual(len(box.refs(work, moved["guard_prefix"] + "/")), 3)
        self.guard(work, "check", "--stage", "pre-push", *LOCAL, *self.ids(pinned), code=2)  # old prefix is gone
        self.guard(work, "approve", *self.ids(moved), "--allow-path", "src/app.py", "--from-entry", "absent",
                   "--to-entry", "absent", "--reason", "user approved", code=0)
        resumed = self.guard(work, "pin", *LOCAL, "--repo", "org/repo", "--pr", "12", "--branch", "topic",
                             "--checkout-owns-pr", "--resume", *self.ids(moved), code=0)
        self.assertEqual(resumed["status"], "resumed")
        self.guard(work, "cleanup", *self.ids(moved), code=0)
        self.assertEqual(box.refs(work), [])

        # Interleaved writers make cleanup fail atomically without deleting anything.
        racing_run = self.guard(work, "pin", *LOCAL, code=0)
        prefix = racing_run["guard_prefix"]
        original = spec_guard.transact
        racers = [
            ("approve", *self.ids(racing_run), "--delete-spec", "specs/s.html", "--reason", "concurrent"),
            ("rebase-pin", *LOCAL, *self.ids(racing_run)),
        ]
        for racer in racers:
            with self.subTest(racer=racer[0]):
                def racing(git, commands, racer=racer):
                    if any(command.startswith("delete ") for command in commands):
                        self.guard(work, *racer, code=0)
                    return original(git, commands)

                before = box.refs(work, prefix + "/")
                with mock.patch.object(spec_guard, "transact", racing):
                    code, data = self.inprocess(work, "cleanup", *self.ids(racing_run))
                self.assertEqual((code, data["status"]), (2, "error"))
                after = box.refs(work, prefix + "/")
                self.assertTrue(set(before) <= set(after))
        self.assertEqual(len(box.refs(work, prefix + "/")), 5)
        self.guard(work, "survival", *LOCAL, *self.ids(racing_run), code=0)
        self.guard(work, "cleanup", *self.ids(racing_run), code=0)
        self.assertEqual(box.refs(work), [])

        runs = {}
        for name in ("old", "fresh", "pending"):
            box.git(work, "checkout", "-q", "-b", name, "main")
            runs[name] = self.guard(work, "pin", *LOCAL, "--spec", "specs/s.html", code=0)
        stale = (datetime.now(timezone.utc) - timedelta(days=8)).strftime("%Y-%m-%dT%H:%M:%SZ")
        for name in ("old", "pending"):
            box.set_created_at(work, runs[name]["guard_prefix"], stale)
        self.guard(work, "rebase-pin", *LOCAL, *self.ids(runs["pending"]), code=0)
        pruned = self.guard(work, "cleanup", "--prune-stale", "--older-than-days", "7", code=0)
        self.assertEqual(pruned["pruned"], [runs["old"]["guard_prefix"]])
        self.assertEqual(box.refs(work, runs["old"]["guard_prefix"] + "/"), [])
        self.assertEqual(len(box.refs(work, runs["fresh"]["guard_prefix"] + "/")), 3)
        self.assertEqual(len(box.refs(work, runs["pending"]["guard_prefix"] + "/")), 5)

    # (13)
    def test_13_course_accepted_and_governed_changes(self) -> None:
        box = self.box
        files = course_files()
        course = course_parser.parse_course(files["specs/COURSE.md"], read_file=files.get)
        self.assertEqual(course.accepted["north_star"], "Ship reliable widgets.")
        self.assertEqual(course.accepted["precedence"], ["Safety before speed.", "Small reversible changes."])
        self.assertEqual(course.accepted["non_goals"], ["No mobile app."])
        self.assertEqual(course.accepted["protected_boundaries"],
                         [".github/workflows/", "infra/", "Makefile", "db/migrations/*.sql"])
        self.assertEqual([item["id"] for item in course.accepted["accepted_decisions"]], ["D-001", "D-002"])
        work = box.init_origin(files)

        def scenario(name: str, **changes) -> tuple[dict, tuple[str, ...]]:
            box.git(work, "checkout", "-q", "-b", name, "main")
            box.commit(work, {"specs/COURSE.md": course_md(**changes)}, name)
            pinned = self.guard(work, "pin", *LOCAL, code=0)
            return pinned, self.ids(pinned)

        pinned, ids = scenario("north", north_star="Ship fast widgets.")
        self.assertEqual(pinned["base_constraints"], course.accepted)
        blocked = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=1)
        governed = blocked["governed_course_changes"]
        self.assertEqual([(item["status"], [f["field"] for f in item["fields"]]) for item in governed],
                         [("unapproved", ["north_star"])])
        self.guard(work, "approve", *ids, "--allow-path", "specs/COURSE.md", "--from-entry", governed[0]["from_entry"],
                   "--to-entry", governed[0]["to_entry"], "--reason", "user approved", code=0)
        self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=0)
        box.git(work, "update-index", "--chmod=+x", "specs/COURSE.md")
        box.git(work, "commit", "-q", "-m", "mode change")
        self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=1)
        box.commit(work, {"specs/COURSE.md": course_md(north_star="Ship faster widgets.")}, "second edit")
        self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=1)

        for name, changes, field in (("promote", {"inferred": False}, "non_goals"),
                                     ("nongoal", {"non_goal": "No mobile or tablet app."}, "non_goals")):
            with self.subTest(name=name):
                _, ids = scenario(name, **changes)
                result = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=1)
                self.assertEqual([f["field"] for f in result["governed_course_changes"][0]["fields"]], [field])
        _, ids = scenario("bookkeeping", status="Done", area="src/ lib/")
        exempt = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=0)
        self.assertEqual(exempt["governed_course_changes"], [])
        self.assertEqual([item["path"] for item in exempt["spec_course_adr_diffs"]], ["specs/COURSE.md"])

    def test_13_upstream_course_amendment_then_clean_rebase(self) -> None:
        box = self.box
        work = box.init_origin(course_files())
        box.git(work, "checkout", "-q", "-b", "topic")
        box.commit(work, {"src/app.py": "print('topic')\n"}, "topic work")
        pinned = self.guard(work, "pin", *LOCAL, code=0)
        ids = self.ids(pinned)
        box.git(work, "checkout", "-q", "main")
        box.commit(work, {"specs/COURSE.md": course_md(north_star="Ship reliable, observable widgets.",
                                                       decision="Use Postgres 16")}, "upstream course")
        box.git(work, "checkout", "-q", "topic")
        stale = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=0)
        self.assertTrue(stale["rebase_recommended"])
        self.assertEqual([(item["baseline"], item["status"]) for item in stale["governed_course_changes"]],
                         [("base_sha", "upstream_base")])
        self.assertEqual({f["field"] for f in stale["governed_course_changes"][0]["fields"]},
                         {"north_star", "accepted_decisions"})
        self.guard(work, "rebase-pin", *LOCAL, *ids, code=0)
        box.git(work, "rebase", "-q", "main")
        self.guard(work, "survival", *LOCAL, *ids, code=0)
        clean = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, code=0)
        self.assertEqual((clean["governed_course_changes"], clean["rebase_recommended"]), ([], False))
        self.assertEqual(clean["base_constraints"]["north_star"], "Ship reliable, observable widgets.")

    def test_13_protected_path_hits_nul_delimited_no_renames(self) -> None:
        box = self.box
        work = box.init_origin(course_files())
        box.git(work, "checkout", "-q", "-b", "topic")
        box.git(work, "mv", ".github/workflows/ci.yml", "ci-old.yml")
        box.commit(work, {"infra/café.tf": "# new\n", "Makefile": "test:\n\tfalse\n",
                          "db/migrations/002.sql": "create table b (id int);\n",
                          "docs/adr/0002-queue.md": "# ADR 2\n\nStatus: Accepted\n\nMore context.\n",
                          "src/app.py": "print('changed')\n"}, "touch protected paths")
        pinned = self.guard(work, "pin", *LOCAL, code=0)
        result = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *self.ids(pinned), code=1)
        hits = {item["path"]: item for item in result["protected_path_hits"]}
        self.assertEqual(set(hits), {".github/workflows/ci.yml", "infra/café.tf", "Makefile",
                                     "db/migrations/002.sql", "docs/adr/0002-queue.md"})
        self.assertEqual(hits[".github/workflows/ci.yml"]["to_entry"], "absent")
        self.assertEqual(hits["infra/café.tf"]["boundaries"], ["infra/"])
        self.assertEqual(hits["db/migrations/002.sql"]["boundaries"], ["db/migrations/*.sql"])
        self.assertIn("ci-old.yml", result["changed_paths"])
        self.assertIn("docs/adr/0002-queue.md", [item["path"] for item in result["spec_course_adr_diffs"]])
        self.assertTrue(all(item["status"] == "unapproved" for item in hits.values()))


    def test_14_upstream_cannot_replace_a_branch_added_criterion(self) -> None:
        box = self.box
        work = box.init_origin({"specs/s.html": spec_html(), "src/app.py": "print(1)\n"})
        box.git(work, "checkout", "-q", "-b", "topic")
        box.commit(work, {"specs/s.html": spec_html(BASE + [("ac-new", "Branch text.")]), "src/app.py": "print(2)\n"},
                   "branch adds ac-new")
        ids = self.ids(self.guard(work, "pin", *LOCAL, code=0))
        box.git(work, "checkout", "-q", "main")
        box.commit(work, {"specs/s.html": spec_html(BASE + [("ac-new", "Upstream text.")])}, "main adds ac-new")
        box.git(work, "checkout", "-q", "topic")
        self.guard(work, "rebase-pin", *LOCAL, *ids, code=0)
        box.git(work, "rebase", "-q", "main", check=False)
        box.git(work, "checkout", "--ours", "specs/s.html")  # during a rebase, ours is the upstream side
        box.git(work, "add", "specs/s.html")
        box.git(work, "-c", "core.editor=true", "rebase", "--continue")
        survival = self.guard(work, "survival", *LOCAL, *ids, code=1)
        self.assertIn(("criterion_rewritten", "ac-new"),
                      {(item["kind"], item.get("criterion")) for item in survival["survival"]})

    def test_15_boundary_prose_edit_is_a_governed_change(self) -> None:
        box = self.box
        work = box.init_origin(course_files())
        box.git(work, "checkout", "-q", "-b", "topic")
        course = (work / "specs" / "COURSE.md").read_text(encoding="utf-8")
        box.commit(work, {"specs/COURSE.md": course.replace("- `Makefile`", "- `Makefile`: edit freely, no approval")},
                   "loosen boundary prose")
        result = self.guard(work, "check", "--stage", "pre-push", *LOCAL,
                            *self.ids(self.guard(work, "pin", *LOCAL, code=0)), code=1)
        self.assertEqual({field["field"] for item in result["governed_course_changes"] for field in item["fields"]},
                         {"protected_boundary_items"})

    def test_16_relative_adr_links_resolve_to_repo_paths(self) -> None:
        box = self.box
        files = course_files()
        files["specs/COURSE.md"] = (files["specs/COURSE.md"]
                                    .replace("| docs/adr/0001-postgres.md |", "| [ADR](../docs/adr/0001-postgres.md) |")
                                    .replace("| docs/adr/0002-queue.md |", "| `./docs/adr/0002-queue.md` |"))
        work = box.init_origin(files)
        box.git(work, "checkout", "-q", "-b", "topic")
        box.commit(work, {"docs/adr/0001-postgres.md": "# ADR 1\n\nStatus: Accepted\n\nEdited.\n",
                          "docs/adr/0002-queue.md": "# ADR 2\n\nStatus: Accepted\n\nEdited.\n"}, "edit ADRs")
        pinned = self.guard(work, "pin", *LOCAL, code=0)
        result = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *self.ids(pinned), code=1)
        self.assertEqual({item["path"] for item in result["protected_path_hits"]},
                         {"docs/adr/0001-postgres.md", "docs/adr/0002-queue.md"})

    def test_17_pre_push_binds_untracked_specs_only_in_the_candidate_checkout(self) -> None:
        box = self.box
        work = box.init_origin({"specs/s.html": spec_html(), "src/app.py": "print(1)\n"})
        box.git(work, "checkout", "-q", "-b", "topic")
        cand = box.commit(work, {"specs/s.html": spec_html(BASE + [("ac-new", "New.")])}, "edit spec")
        ids = self.ids(self.guard(work, "pin", *LOCAL, code=0))
        box.git(work, "checkout", "-q", "main")
        box.write(work, {"specs/foreign.html": spec_html(title="Foreign")})
        elsewhere = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, "--cand-sha", cand, code=0)
        self.assertNotIn("specs/foreign.html", elsewhere["bound_specs"])
        self.assertEqual(elsewhere["bound_spec_deletions"], [])
        box.git(work, "checkout", "-q", "topic")
        owned = self.guard(work, "check", "--stage", "pre-push", *LOCAL, *ids, "--cand-sha", cand, code=1)
        self.assertIn("specs/foreign.html", owned["bound_specs"])

    def test_18_pin_for_a_pr_needs_the_exact_candidate(self) -> None:
        work = self.box.init_origin({"src/app.py": "print(1)\n"})
        missing = self.guard(work, "pin", *LOCAL, "--repo", "org/repo", "--pr", "4", "--branch", "topic", code=2)
        self.assertIn("--head-sha", missing["error"])
        self.guard(work, "pin", *LOCAL, "--repo", "org/repo", "--pr", "4", "--head-sha", self.box.head(work), code=2)


if __name__ == "__main__":
    unittest.main()
