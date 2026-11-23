#!/usr/bin/env python3
"""Pin, check, and clean up PR spec/course guard baselines kept under refs/spec-guard/.

Subcommands: pin, bind-pr, rebase-pin, survival, check, approve, cleanup. Every git read is plumbing
(ls-tree / ls-files -s / diff --no-renames with -z, cat-file --batch), so no hook or checkout/smudge
filter runs, and every ref change is one conditional `git update-ref --stdin` transaction.

Exit 0: mechanically clean or "guard: n/a" (still review non-empty judgment fields such as
changed_paths, spec_course_adr_diffs, and base_constraints). Exit 1: deterministic guard violation
(unapproved accepted_criteria_changed, governed_course_changes, protected_path_hits, survival
drops/rewrites, or bound-spec deletion; strict validator error; symlink_rejected /
unsupported_tree_entry; remote_head_diverged). Exit 2: bad input, unreachable remote or fetch, OID
mismatch, pending pre-rebase checkpoint, missing or mismatched --guard-prefix/--invocation-id, or a
ref-transaction conflict (Ask). Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import subprocess
import sys
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import course_parser  # noqa: E402  (sibling: single owner of COURSE.md parsing)
import validate_plan  # noqa: E402  (sibling: PlanParser and validate)

COURSE = "specs/COURSE.md"
SPEC_PATHSPEC = "specs/*.html"
BASELINE = ("start", "merge-base", "start-tree")
CHECKPOINTS = ("pre-rebase", "pre-rebase-base")
REF_NAMES = BASELINE + CHECKPOINTS
REGULAR_MODES = {"100644", "100755"}
REJECTION_KIND = {"120000": "symlink_rejected", "160000": "unsupported_tree_entry"}
ENTRY = re.compile(r"(?:100644|100755|120000|160000):(?:[0-9a-f]{40}|[0-9a-f]{64})")
OID = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
PREFIX = re.compile(r"refs/spec-guard/(?:branch/[^/]+|pr/[^/]+/[0-9]+)/[^/]+")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
ABSENT = "absent"
NETWORK_TIMEOUT = 60
LOCAL_TIMEOUT = 300


class GuardError(Exception):
    """Exit 2: bad input, git or remote failure, OID mismatch, or a conflict that needs an Ask."""

    def __init__(self, message: str, **fields) -> None:
        super().__init__(message)
        self.fields = fields


def decode(data: bytes) -> str:
    return data.decode("utf-8", "surrogateescape")


class Git:
    def __init__(self, cwd: Path) -> None:
        self.cwd = cwd
        self.env = dict(os.environ, GIT_TERMINAL_PROMPT="0")

    def run(self, *args: str, input: bytes | str | None = None, check: bool = True, literal: bool = False,
            network: bool = False, env: dict | None = None) -> subprocess.CompletedProcess:
        # Guard plumbing never runs repository hooks (reference-transaction included).
        command = ["git", "-c", f"core.hooksPath={os.devnull}"]
        if literal:
            command.append("--literal-pathspecs")
        command.extend(args)
        data = input.encode("utf-8", "surrogateescape") if isinstance(input, str) else input
        try:
            proc = subprocess.run(command, cwd=self.cwd, input=data, capture_output=True,
                                  env=dict(self.env, **(env or {})),
                                  timeout=NETWORK_TIMEOUT if network else LOCAL_TIMEOUT)
        except subprocess.TimeoutExpired as exc:
            raise GuardError(f"git {args[0]} timed out", command=args[:3]) from exc
        if check and proc.returncode != 0:
            raise GuardError(f"git {' '.join(args[:2])} failed: {decode(proc.stderr).strip()}")
        return proc

    def out(self, *args: str, **kwargs) -> str:
        return decode(self.run(*args, **kwargs).stdout).strip()

    def zlist(self, *args: str, **kwargs) -> list[str]:
        return [item for item in decode(self.run(*args, **kwargs).stdout).split("\0") if item]


# ---------------------------------------------------------------- small git helpers

def esc(value: str) -> str:
    """Escape '%' first, then '/', so a/b and a%2Fb never collide."""
    return value.replace("%", "%25").replace("/", "%2F")


def branch_namespace(branch: str) -> str:
    return f"refs/spec-guard/branch/{esc(branch)}"


def pr_namespace(repo: str, pr: int) -> str:
    return f"refs/spec-guard/pr/{esc(repo)}/{pr}"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def plain_arg(value: str, flag: str) -> str:
    if not value or value.startswith("-") or any(char in value for char in "\0\n"):
        raise GuardError(f"invalid {flag} value {value!r}")
    return value


def repo_path(value: str, flag: str) -> str:
    """Normalize a repo-relative file path; reject absolute paths and '..' escapes."""
    path = posixpath.normpath(plain_arg(value.strip(), flag).replace("\\", "/"))
    if path.startswith("/") or path == "." or path == ".." or path.startswith("../"):
        raise GuardError(f"{flag} must be a repo-relative path inside the repository: {value!r}")
    return path


def resolve_commit(git: Git, name: str, flag: str) -> str:
    proc = git.run("rev-parse", "--verify", "--quiet", f"{plain_arg(name, flag)}^{{commit}}", check=False)
    if proc.returncode:
        raise GuardError(f"{flag} {name!r} is not a local commit")
    return decode(proc.stdout).strip()


def current_branch(git: Git) -> str | None:
    proc = git.run("symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    if proc.returncode:
        return None
    return decode(proc.stdout).strip() or None


def check_branch_name(git: Git, branch: str, flag: str) -> str:
    plain_arg(branch, flag)
    if git.run("check-ref-format", f"refs/heads/{branch}", check=False).returncode:
        raise GuardError(f"{flag} {branch!r} is not a valid branch name")
    return branch


def merge_base(git: Git, left: str, right: str) -> str:
    proc = git.run("merge-base", left, right, check=False)
    if proc.returncode:
        raise GuardError(f"no merge base between {left} and {right}")
    return decode(proc.stdout).strip()


def is_ancestor(git: Git, ancestor: str, descendant: str) -> bool:
    code = git.run("merge-base", "--is-ancestor", ancestor, descendant, check=False).returncode
    if code not in (0, 1):
        raise GuardError(f"cannot compare ancestry of {ancestor} and {descendant}")
    return code == 0


def zero_oid(git: Git) -> str:
    return "0" * (64 if git.out("rev-parse", "--show-object-format") == "sha256" else 40)


def list_refs(git: Git, pattern: str) -> dict[str, str]:
    refs = {}
    for line in git.out("for-each-ref", "--format=%(objectname) %(refname)", pattern).splitlines():
        oid, _, ref = line.partition(" ")
        refs[ref] = oid
    return refs


def prefix_refs(git: Git, prefix: str) -> dict[str, str]:
    return {ref[len(prefix) + 1:]: oid for ref, oid in list_refs(git, prefix + "/").items()}


def transact(git: Git, commands: list[str]) -> None:
    """Apply ref updates as one all-or-nothing transaction; any stale old value aborts all of them."""
    script = "start\n" + "".join(f"{command}\n" for command in commands) + "prepare\ncommit\n"
    proc = git.run("update-ref", "--stdin", input=script, check=False)
    if proc.returncode:
        raise GuardError("ref transaction conflict: refs changed concurrently; re-read state or Ask",
                         detail=decode(proc.stderr).strip())


def fetch_isolated(git: Git, source: str, source_ref: str, label: str) -> str:
    """Fetch one ref into a unique temp ref, leaving FETCH_HEAD, tracking refs, and tags untouched."""
    temp = f"refs/spec-guard/tmp/{uuid.uuid4()}/{label}"
    try:
        git.run("fetch", "--no-write-fetch-head", "--no-tags", "--no-prune", "--refmap=",
                "--no-recurse-submodules", "--quiet", plain_arg(source, "remote"), f"+{source_ref}:{temp}",
                network=True)
        return git.out("rev-parse", "--verify", temp)
    finally:
        git.run("update-ref", "-d", temp, check=False)


def diff_names(git: Git, revs: tuple = (), paths: tuple = (), cached: bool = False,
               literal: bool = False) -> list[str]:
    args = ["diff", "--no-renames", "--name-only", "-z", "--no-ext-diff", "--no-textconv"]
    if cached:
        args.append("--cached")
    return git.zlist(*args, *revs, "--", *paths, literal=literal)


def untracked(git: Git, paths: tuple = ()) -> list[str]:
    return git.zlist("ls-files", "-z", "--others", "--exclude-standard", "--", *paths)


def build_tree(git: Git, files: dict[str, bytes], base_tree: str | None = None) -> str:
    """Write a tree (via a temp GIT_INDEX_FILE) holding files, optionally layered over base_tree."""
    with tempfile.TemporaryDirectory(prefix="spec-guard-index-") as folder:
        env = {"GIT_INDEX_FILE": os.path.join(folder, "index")}
        if base_tree:
            git.run("read-tree", base_tree, env=env)
        info = []
        for path, data in sorted(files.items()):
            oid = git.out("hash-object", "-w", "--stdin", input=data)
            info.append(f"100644 {oid}\t{path}\0")
        if info:
            git.run("update-index", "-z", "--index-info", input="".join(info), env=env)
        return git.out("write-tree", env=env)


def read_blobs(git: Git, oids: list[str], cache: dict[str, bytes] = {}) -> dict[str, bytes]:  # noqa: B006
    """Read blobs with `cat-file --batch` (no filters); the default dict is a per-process cache."""
    wanted = [oid for oid in dict.fromkeys(oids) if oid not in cache]
    if wanted:
        raw = git.run("cat-file", "--batch", input="".join(f"{oid}\n" for oid in wanted)).stdout
        position = 0
        for oid in wanted:
            end = raw.index(b"\n", position)
            header = decode(raw[position:end]).split()
            if len(header) != 3 or header[1] != "blob":
                raise GuardError(f"object {oid} is not a readable blob")
            size = int(header[2])
            cache[oid] = raw[end + 1:end + 1 + size]
            position = end + 2 + size
    return {oid: cache[oid] for oid in oids}


# ---------------------------------------------------------------- snapshots and plan facts

class Findings:
    """Non-regular entries met on read/validated paths."""

    def __init__(self) -> None:
        self.rejected: dict[str, list[dict]] = {"symlink_rejected": [], "unsupported_tree_entry": []}

    def reject(self, path: str, mode: str, tree: str) -> None:
        bucket = self.rejected[REJECTION_KIND.get(mode, "unsupported_tree_entry")]
        if not any(item["path"] == path and item["mode"] == mode for item in bucket):
            bucket.append({"path": path, "mode": mode, "tree": tree})


class Snapshot:
    """Entries and regular-file bytes from a tree-ish, or from the index when treeish is None."""

    def __init__(self, git: Git, treeish: str | None, label: str, fallback: Snapshot | None = None) -> None:
        self.git, self.treeish, self.label, self.fallback = git, treeish, label, fallback
        self.cache: dict[str, tuple[str, str] | None] = {}

    def prefetch(self, paths) -> None:
        missing = [path for path in dict.fromkeys(paths) if path not in self.cache]
        if not missing:
            return
        for path in missing:
            self.cache[path] = None
        if self.treeish is None:
            items = self.git.zlist("ls-files", "-s", "-z", "--", *missing, literal=True)
        else:
            items = self.git.zlist("ls-tree", "-r", "-z", "--full-tree", self.treeish, "--", *missing, literal=True)
        for item in items:
            meta, path = item.split("\t", 1)
            parts = meta.split()
            if self.treeish is None:
                mode, oid, stage = parts
                if stage != "0":
                    raise GuardError(f"unmerged index entry {path}; resolve conflicts first")
            else:
                mode, _, oid = parts
            if path in self.cache:
                self.cache[path] = (mode, oid)
        if self.fallback is not None:
            self.fallback.prefetch(missing)

    def entry(self, path: str) -> tuple[str, str] | None:
        self.prefetch([path])
        found = self.cache[path]
        if found is None and self.fallback is not None:
            return self.fallback.entry(path)
        return found

    def read(self, path: str, findings: Findings | None) -> bytes | None:
        found = self.entry(path)
        if found is None:
            return None
        mode, oid = found
        if mode not in REGULAR_MODES:
            if findings is not None:
                findings.reject(path, mode, self.label)
            return None
        return read_blobs(self.git, [oid])[oid]

    def text(self, path: str, findings: Findings | None) -> str | None:
        data = self.read(path, findings)
        return None if data is None else data.decode("utf-8", "replace")


def entry_str(found: tuple[str, str] | None) -> str:
    return f"{found[0]}:{found[1]}" if found else ABSENT


@dataclass
class PlanFacts:
    criteria: dict = field(default_factory=dict)
    amendments: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    legacy: bool = False
    resources: list = field(default_factory=list)


def plan_facts(text: str) -> PlanFacts:
    parser = validate_plan.PlanParser()
    parser.feed(text)
    parser.close()
    markers = any({"criterion", "task"} & element.classes for element in parser.elements)
    legacy = "acceptance" not in parser.ids and "coverage" not in parser.ids and not markers
    resources = [resource for resource, _, _ in parser.resources] + [figure.image_src for figure in parser.figures]
    return PlanFacts(validate_plan.criteria_text(parser), [entry[0] for entry in validate_plan.amendment_entries(parser)],
                     dict(parser.metadata), legacy, resources)


def facts_at(snapshot: Snapshot, path: str, findings: Findings | None,
             cache: dict[str, PlanFacts] = {}) -> PlanFacts | None:  # noqa: B006
    text = snapshot.text(path, findings)
    if text is None:
        return None
    if text not in cache:
        cache[text] = plan_facts(text)
    return cache[text]


# ---------------------------------------------------------------- run state

@dataclass
class Run:
    prefix: str
    invocation_id: str
    refs: dict
    created_at: str
    bound: list
    approvals: list


def tree_blob(git: Git, tree: str, name: str) -> bytes | None:
    proc = git.run("cat-file", "blob", f"{tree}:{name}", check=False)
    return proc.stdout if proc.returncode == 0 else None


def read_run_id(git: Git, tree: str | None) -> dict | None:
    data = tree_blob(git, tree, "run-id.txt") if tree else None
    try:
        value = json.loads(data) if data is not None else None
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def load_run(git: Git, prefix: str | None, invocation_id: str | None) -> Run:
    if not prefix or not invocation_id:
        raise GuardError("pass --guard-prefix and --invocation-id from the pinned run")
    if not PREFIX.fullmatch(prefix) or prefix.rsplit("/", 1)[1] != invocation_id:
        raise GuardError(f"--guard-prefix {prefix!r} does not belong to invocation {invocation_id!r}")
    refs = prefix_refs(git, prefix)
    missing = [name for name in BASELINE if name not in refs]
    if missing:
        raise GuardError(f"guard baseline refs missing under {prefix}: {', '.join(missing)}", missing=missing)
    run_id = read_run_id(git, refs["start-tree"])
    if not run_id or run_id.get("invocation_id") != invocation_id:
        raise GuardError("start-tree:run-id.txt invocation_id does not match --invocation-id")
    bound = decode(tree_blob(git, refs["start-tree"], "bound-specs.txt") or b"").splitlines()
    approvals_blob = tree_blob(git, refs["start-tree"], "approvals.json")
    try:
        approvals = json.loads(approvals_blob) if approvals_blob is not None else []
    except ValueError as exc:
        raise GuardError("start-tree:approvals.json is not valid JSON") from exc
    return Run(prefix, invocation_id, refs, run_id.get("created_at", ""), [path for path in bound if path], approvals)


def describe_run(git: Git, prefix: str, refs: dict) -> dict:
    run_id = read_run_id(git, refs.get("start-tree")) or {}
    return {"guard_prefix": prefix, "invocation_id": run_id.get("invocation_id"),
            "created_at": run_id.get("created_at"), "refs": sorted(refs),
            "pending_pre_rebase": any(name in refs for name in CHECKPOINTS)}


def group_runs(git: Git, pattern: str) -> dict[str, dict]:
    runs: dict[str, dict] = {}
    for ref, oid in list_refs(git, pattern).items():
        prefix, _, name = ref.rpartition("/")
        if name in REF_NAMES and PREFIX.fullmatch(prefix):
            runs.setdefault(prefix, {})[name] = oid
    return runs


def scan_runs(git: Git, namespaces: list[str]) -> list[dict]:
    runs: dict[str, dict] = {}
    for namespace in namespaces:
        for prefix, refs in group_runs(git, namespace + "/").items():
            if prefix.rpartition("/")[0] == namespace:
                runs[prefix] = refs
    return [describe_run(git, prefix, refs) for prefix, refs in sorted(runs.items())]


def run_start_snapshot(git: Git, run: Run) -> Snapshot:
    """start-tree snapshots of pre-existing dirty specs take precedence over the start commit."""
    return Snapshot(git, run.refs["start-tree"], "start-tree", fallback=Snapshot(git, run.refs["start"], "start"))


def update_bound(git: Git, run: Run, discovered) -> list[str]:
    """Union newly discovered specs into start-tree:bound-specs.txt (mid-run binding)."""
    merged = sorted(set(run.bound) | set(discovered))
    if merged != sorted(run.bound):
        tree = build_tree(git, {"bound-specs.txt": bound_text(merged)}, base_tree=run.refs["start-tree"])
        transact(git, [f"update {run.prefix}/start-tree {tree} {run.refs['start-tree']}"])
        run.refs["start-tree"], run.bound = tree, merged
    return merged


def bound_text(paths) -> bytes:
    return "".join(f"{path}\n" for path in sorted(paths)).encode("utf-8", "surrogateescape")


# ---------------------------------------------------------------- remotes, bases, candidates

def resolve_base(git: Git, args) -> str:
    if args.local_base:
        if args.base_remote or args.base_branch:
            raise GuardError("pass either --local-base or --base-remote with --base-branch, not both")
        branch = check_branch_name(git, args.local_base, "--local-base")
        return resolve_commit(git, f"refs/heads/{branch}", "--local-base")
    if not (args.base_remote and args.base_branch):
        raise GuardError("pass --base-remote and --base-branch (or --local-base when there is no remote)")
    branch = check_branch_name(git, args.base_branch, "--base-branch")
    return fetch_isolated(git, args.base_remote, f"refs/heads/{branch}", "base")


def url_rewrites(git: Git) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    proc = git.run("config", "-z", "--get-regexp", r"^url\..*\.(insteadof|pushinsteadof)$", check=False)
    fetch_rules, push_rules = [], []
    for item in decode(proc.stdout).split("\0"):
        key, _, value = item.partition("\n")
        for suffix, rules in ((".pushinsteadof", push_rules), (".insteadof", fetch_rules)):
            if key.startswith("url.") and key.endswith(suffix) and value:
                rules.append((value, key[4:-len(suffix)]))
                break
    return fetch_rules, push_rules


def rewrite(url: str, rules: list[tuple[str, str]]) -> str | None:
    matches = [(prefix, base) for prefix, base in rules if url.startswith(prefix)]
    if not matches:
        return None
    prefix, base = max(matches, key=lambda rule: len(rule[0]))
    return base + url[len(prefix):]


def resolve_push_endpoint(git: Git, remote: str) -> str:
    """One concrete URL that `git push <url>` and `git ls-remote <url>` both reach unchanged."""
    proc = git.run("remote", "get-url", "--push", "--all", plain_arg(remote, "--push-remote"), check=False)
    if proc.returncode:
        raise GuardError(f"--push-remote {remote!r} is not a configured remote")
    urls = [line for line in decode(proc.stdout).splitlines() if line]
    if len(urls) != 1:
        raise GuardError(f"push remote {remote!r} has {len(urls)} push URLs; Ask which one to use", push_urls=urls)
    url = urls[0]
    fetch_rules, push_rules = url_rewrites(git)
    # A command-line URL is rewritten again by pushInsteadOf (else insteadOf) on push and by insteadOf
    # on ls-remote/fetch, so follow the rewrites to a fixed point.
    for _ in range(10):
        following = rewrite(url, push_rules) or rewrite(url, fetch_rules)
        if following is None or following == url:
            return url
        url = following
    raise GuardError(f"url rewrite loop resolving push remote {remote!r}")


def observe_remote(git: Git, endpoint: str, branch: str) -> str | None:
    """Exact-refname existence via ls-remote, then an isolated fetch so ancestry checks are local."""
    ref = f"refs/heads/{branch}"
    proc = git.run("ls-remote", "--exit-code", endpoint, ref, check=False, network=True)
    if proc.returncode == 2:
        return None
    if proc.returncode != 0:
        raise GuardError(f"push endpoint {endpoint!r} is unreachable: {decode(proc.stderr).strip()}")
    matches = [line.split("\t", 1)[0] for line in decode(proc.stdout).splitlines()
               if line.partition("\t")[2] == ref]
    if not matches:
        return None
    fetched = fetch_isolated(git, endpoint, ref, "remote")
    if fetched != matches[0]:
        raise GuardError("remote head moved between ls-remote and fetch; retry", listed=matches[0], fetched=fetched)
    return fetched


def observe(git: Git, push_remote: str | None, branch: str | None) -> tuple[str | None, str | None]:
    if not push_remote:
        return None, None
    if not branch:
        raise GuardError("pass --branch so the remote head branch can be observed")
    endpoint = resolve_push_endpoint(git, push_remote)
    return endpoint, observe_remote(git, endpoint, branch)


def lease_problem(git: Git, observed: str | None, kept: str, pending: str | None) -> str | None:
    if pending is not None:
        expected = None if pending == ABSENT else pending
        if observed != expected:
            return f"remote head {observed or ABSENT} does not equal --pending-lease {pending}"
        if expected and not is_ancestor(git, expected, kept):
            return "--pending-lease is not an ancestor of --pre-rebase-head"
        return None
    if observed and not is_ancestor(git, observed, kept):
        return "remote head is not an ancestor of --pre-rebase-head"
    return None


def pending_lease_arg(git: Git, value: str | None) -> str | None:
    if value is None or value == ABSENT:
        return value
    if OID.fullmatch(value.lower()):
        return value.lower()
    return resolve_commit(git, value, "--pending-lease")


def verify_head(git: Git, args) -> str | None:
    """Verify the live PR head locally, fetching refs/pull/<n>/head into a temp ref only if absent."""
    if not getattr(args, "head_sha", None):
        return None
    head = args.head_sha.lower()
    if not OID.fullmatch(head):
        raise GuardError("--head-sha must be a full object id")
    if git.run("cat-file", "-e", f"{head}^{{commit}}", check=False).returncode == 0:
        return head
    if not (args.pr and args.base_remote):
        raise GuardError("--head-sha is not local; pass --pr and --base-remote to fetch refs/pull/<n>/head")
    fetched = fetch_isolated(git, args.base_remote, f"refs/pull/{args.pr}/head", "pr")
    if fetched != head:
        raise GuardError("fetched refs/pull/<n>/head does not match --head-sha", fetched=fetched, head_sha=head)
    return head


def checkout_owned(git: Git, args, head: str | None) -> bool:
    if not args.pr or args.checkout_owns_pr:
        return True
    return bool(head and args.branch and current_branch(git) == args.branch
                and resolve_commit(git, "HEAD", "HEAD") == head)


def is_spec(path: str) -> bool:
    return path.startswith("specs/") and path.endswith(".html")


# ---------------------------------------------------------------- course helpers

def load_course(snapshot: Snapshot, findings: Findings):
    text = snapshot.text(COURSE, findings)
    if text is None:
        return None

    def read_file(path: str) -> str | None:
        normalized = posixpath.normpath(path)
        return None if normalized.startswith("..") else snapshot.text(normalized, findings)

    course = course_parser.parse_course(text, read_file=read_file)
    for decision in course.accepted.get("accepted_decisions", []):
        for path in decision["adr_paths"]:
            found = snapshot.entry(posixpath.normpath(path))
            if found and found[0] not in REGULAR_MODES:  # linked ADRs are read/validated entries
                findings.reject(path, found[0], snapshot.label)
    return course


def accepted_diff(old: dict, new: dict) -> list[dict]:
    return [{"field": key, "from": old.get(key), "to": new.get(key)}
            for key in sorted(set(old) | set(new)) if old.get(key) != new.get(key)]


def adr_paths(*courses) -> set[str]:
    return {posixpath.normpath(path) for course in courses if course for decision in course.decisions
            for path in decision["adr_paths"]}


# ---------------------------------------------------------------- approvals

def approved_path(approvals: list, path: str, from_entry: str, to_entry: str) -> bool:
    return any(item.get("kind") == "allow-path" and item.get("path") == path
               and item.get("from_entry") == from_entry and item.get("to_entry") == to_entry for item in approvals)


def approved_spec_deletion(approvals: list, spec: str) -> bool:
    return any(item.get("kind") == "delete-spec" and item.get("spec") == spec for item in approvals)


def approved_criterion(approvals: list, spec: str, criterion: str, old: str, new: str | None) -> bool:
    for item in approvals:
        if item.get("spec") != spec or item.get("criterion") != criterion or item.get("from_text") != old:
            continue
        if new is None and item.get("kind") == "delete-criterion":
            return True
        if new is not None and item.get("kind") == "amend-criterion" and item.get("to_text") == new:
            return True
    return False


def upstream_match(upstream: PlanFacts | None, fork: PlanFacts | None, criterion: str, old: str,
                   new: str | None) -> bool:
    """True when <base_sha> changed exactly the accepted text `old` (as of the fork) into `new`."""
    if upstream is None or fork is None:
        return False
    return fork.criteria.get(criterion) == old != new and upstream.criteria.get(criterion) == new


# ---------------------------------------------------------------- survival

def metadata_delta(old: str, new: str) -> list[str]:
    delta = new.replace(old, " ", 1) if old and old in new else new
    return [part for part in (validate_plan.normalize_text(piece) for piece in re.split(r"[;,]", delta))
            if part.strip(" .")]


def spec_survival(spec: str, label: str, source: Snapshot, fork: Snapshot, target: Snapshot, upstream: Snapshot,
                  approvals: list, findings: Findings) -> list[dict]:
    """Branch-only criteria, amendments, and metadata in source must reach target intact."""
    branch = facts_at(source, spec, findings)
    if branch is None:
        return []
    base = facts_at(fork, spec, findings) or PlanFacts()
    now = facts_at(target, spec, findings)
    upstream_facts = facts_at(upstream, spec, findings)
    item = {"spec": spec, "source": label}
    if now is None:
        if target.entry(spec) is not None or approved_spec_deletion(approvals, spec):
            return []
        return [dict(item, kind="spec_dropped")]
    failures = []
    for criterion, text in branch.criteria.items():
        if base.criteria.get(criterion) == text:
            continue
        found = now.criteria.get(criterion)
        if found == text or approved_criterion(approvals, spec, criterion, text, found) \
                or upstream_match(upstream_facts, base, criterion, text, found):
            continue
        kind = "criterion_dropped" if found is None else "criterion_rewritten"
        failures.append(dict(item, kind=kind, criterion=criterion, expected=text, found=found))
    for entry in branch.amendments:
        if entry not in base.amendments and entry not in now.amendments:
            failures.append(dict(item, kind="amendment_missing", amendment=entry[:240]))
    for key, value in branch.metadata.items():
        old = base.metadata.get(key, "")
        if value == old:
            continue
        missing = [part for part in metadata_delta(old, value) if part not in now.metadata.get(key, "")]
        if missing:
            failures.append(dict(item, kind="metadata_dropped", key=key, missing=missing))
    return failures


def survival_failures(git: Git, run: Run, target: Snapshot, upstream: Snapshot, findings: Findings,
                      skip: tuple = ()) -> list[dict]:
    """Run-start survival, plus pending pre-rebase survival while that checkpoint is unverified."""
    sources = [("run_start", run_start_snapshot(git, run), Snapshot(git, run.refs["merge-base"], "merge-base"), set())]
    pending = [name for name in CHECKPOINTS if name in run.refs]
    if pending and len(pending) != len(CHECKPOINTS):
        raise GuardError(f"incomplete pre-rebase checkpoint under {run.prefix}: only {pending}")
    if pending:
        before, before_base = run.refs["pre-rebase"], run.refs["pre-rebase-base"]
        extra = {path for path in diff_names(git, (before_base, before), (SPEC_PATHSPEC,)) if is_spec(path)}
        sources.append(("pre_rebase", Snapshot(git, before, "pre-rebase"),
                        Snapshot(git, before_base, "pre-rebase-base"), extra))
    failures = []
    for label, source, fork, extra in sources:
        for spec in sorted((set(run.bound) | extra) - set(skip)):
            failures.extend(spec_survival(spec, label, source, fork, target, upstream, run.approvals, findings))
    return failures


# ---------------------------------------------------------------- validation

def local_reference(spec: str, reference: str) -> str | None:
    value = reference.strip()
    if not value or value.startswith(("#", "//")) or SCHEME.match(value) or validate_plan.is_remote(value):
        return None
    path = posixpath.normpath(posixpath.join(posixpath.dirname(spec), unquote(value)))
    return None if path.startswith("../") or path in (".", "..") or path.startswith("/") else path


def write_inside(root: Path, path: str, data: bytes) -> Path:
    target = (root / path).resolve()
    target.relative_to(root.resolve())  # raises ValueError on ../ escapes
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return target


def validate_spec(spec: str, text: str, facts: PlanFacts, previous: str | None, candidate: Snapshot,
                  findings: Findings) -> list[dict]:
    """Strict validate_plan run on verified regular blobs materialized in an isolated temp dir."""
    with tempfile.TemporaryDirectory(prefix="spec-guard-") as folder:
        root = Path(folder) / "tree"
        path = write_inside(root, spec, text.encode("utf-8", "surrogateescape"))
        for reference in facts.resources:
            asset = local_reference(spec, reference)
            data = candidate.read(asset, findings) if asset else None
            if asset and data is not None:
                try:
                    write_inside(root, asset, data)
                except (ValueError, OSError):
                    continue
        previous_path = None
        if previous is not None:
            previous_path = Path(folder) / "previous.html"
            previous_path.write_text(previous, encoding="utf-8", errors="surrogateescape")
        try:
            diagnostics = validate_plan.validate(path, text, previous_path, None)
        except ValueError as exc:
            return [{"code": "PF3_PREVIOUS_UNREADABLE", "message": str(exc), "severity": "error", "line": 1,
                     "column": 1}]
    return [asdict(item) for item in diagnostics]


# ---------------------------------------------------------------- subcommands

def discover_specs(git: Git, args, diff_base: str, cand: str, start: str, start_base: str, owned: bool) -> list[str]:
    named = {repo_path(path, "--spec") for path in (args.spec or [])}
    found = set(named)
    found.update(diff_names(git, (diff_base, cand), (SPEC_PATHSPEC,)))
    found.update(diff_names(git, (start_base, start), (SPEC_PATHSPEC,)))
    if owned:
        found.update(diff_names(git, ("HEAD",), (SPEC_PATHSPEC,)))
        found.update(diff_names(git, ("HEAD",), (SPEC_PATHSPEC,), cached=True))
        found.update(untracked(git, (SPEC_PATHSPEC,)))
    return sorted(path for path in found if is_spec(path) or path in named)


def dirty_snapshots(git: Git, bound: list[str]) -> dict[str, bytes]:
    """Worktree bytes of bound specs that differ from HEAD (or are untracked) at run start."""
    if not bound:
        return {}
    dirty = set(diff_names(git, ("HEAD",), tuple(bound), literal=True))
    dirty |= set(diff_names(git, ("HEAD",), tuple(bound), cached=True, literal=True))
    dirty |= set(untracked(git, tuple(f":(literal){path}" for path in bound)))
    snapshots = {}
    for spec in sorted(dirty):
        full = git.cwd / spec
        if full.is_file() and not full.is_symlink():
            snapshots[spec] = full.read_bytes()
    return snapshots


def validate_pin_args(args) -> None:
    if bool(args.repo) != bool(args.pr):
        raise GuardError("--repo and --pr must be passed together")
    if args.repo and not re.fullmatch(r"[^/\s]+/[^/\s]+", args.repo):
        raise GuardError("--repo must look like owner/repo")
    if args.pr and not args.resume and not (args.branch and (args.head_sha or args.cand_sha or args.checkout_owns_pr)):
        raise GuardError("--pr needs --branch <headRefName> and the exact candidate: --head-sha <headRefOid>, "
                         "--cand-sha, or --checkout-owns-pr")
    if bool(args.run_start_head) != bool(args.run_start_merge_base):
        raise GuardError("--run-start-head and --run-start-merge-base must be passed together")
    if args.pending_lease is not None and not args.pre_rebase_head:
        raise GuardError("--pending-lease needs --pre-rebase-head")
    if args.resume and not (args.guard_prefix and args.invocation_id):
        raise GuardError("--resume needs --guard-prefix and --invocation-id")
    if not args.resume and (args.guard_prefix or args.invocation_id):
        raise GuardError("--guard-prefix/--invocation-id on pin require --resume")
    if args.resume and args.run_start_head:
        raise GuardError("--run-start-head is only for skipped runs; a resumed run keeps its pinned start")


def cmd_pin(git: Git, args) -> tuple[int, dict]:
    validate_pin_args(args)
    run = load_run(git, args.guard_prefix, args.invocation_id) if args.resume else None  # restore FIRST
    branch = args.branch or (None if args.pr else current_branch(git))
    if branch:
        check_branch_name(git, branch, "--branch")
    if not args.pr and not branch:
        raise GuardError("detached HEAD: pass --branch, or --repo with --pr")
    namespaces = ([pr_namespace(args.repo, args.pr)] if args.pr else []) + ([branch_namespace(branch)] if branch else [])
    prior_runs = scan_runs(git, namespaces)  # before any guard: n/a decision
    if run is None and prior_runs:
        return 2, {"status": "resume_required", "prior_runs": prior_runs,
                   "error": "earlier guard runs exist for this PR/branch; resume one with --resume or Ask"}

    base_sha = resolve_base(git, args)
    head = verify_head(git, args)
    cand = resolve_commit(git, args.cand_sha, "--cand-sha") if args.cand_sha else head or resolve_commit(git, "HEAD", "HEAD")
    owned = checkout_owned(git, args, head)
    endpoint, observed = observe(git, args.push_remote, branch)
    result = {"push_endpoint": endpoint, "observed_remote_sha": observed, "cand_sha": cand, "base_sha": base_sha}
    if args.pre_rebase_head:
        kept = resolve_commit(git, args.pre_rebase_head, "--pre-rebase-head")
        problem = lease_problem(git, observed, kept, pending_lease_arg(git, args.pending_lease))
        result.update(pre_rebase_head=kept, pending_lease=observed or ABSENT)
        if problem:
            return 1, dict(result, status="remote_head_diverged", remote_head_diverged=True, reason=problem,
                           prior_runs=prior_runs)

    diff_base = merge_base(git, base_sha, cand)
    if run is not None:
        start, start_base = run.refs["start"], run.refs["merge-base"]
    elif args.run_start_head:
        start = resolve_commit(git, args.run_start_head, "--run-start-head")
        start_base = resolve_commit(git, args.run_start_merge_base, "--run-start-merge-base")
    else:
        start = resolve_commit(git, "HEAD", "HEAD") if owned else cand
        start_base = merge_base(git, base_sha, start)
    discovered = discover_specs(git, args, diff_base, cand, start, start_base, owned)

    findings = Findings()
    base_snapshot = Snapshot(git, base_sha, "base_sha")
    course_touched = base_snapshot.entry(COURSE) is not None or Snapshot(git, cand, "cand").entry(COURSE) is not None \
        or (owned and (Snapshot(git, None, "index").entry(COURSE) is not None or os.path.lexists(git.cwd / COURSE)))
    result.update(initial_head_sha=start, initial_merge_base=start_base)
    if run is None and not discovered and not course_touched:
        return 0, dict(result, status="guard: n/a", prior_runs=prior_runs)

    if run is not None:
        bound = update_bound(git, run, discovered)
        prefix, invocation_id, status = run.prefix, run.invocation_id, "resumed"
    else:
        if any("\n" in path for path in discovered):
            raise GuardError("spec paths containing newlines are not supported")
        invocation_id = str(uuid.uuid4())
        prefix = f"{pr_namespace(args.repo, args.pr) if args.pr else branch_namespace(branch)}/{invocation_id}"
        files = {"run-id.txt": (json.dumps({"invocation_id": invocation_id, "created_at": now_iso()}) + "\n").encode(),
                 "bound-specs.txt": bound_text(discovered)}
        if owned and not args.run_start_head:  # a late activation cannot know run-start dirty state
            files.update(dirty_snapshots(git, discovered))
        tree = build_tree(git, files)
        zero = zero_oid(git)
        transact(git, [f"update {prefix}/start {start} {zero}", f"update {prefix}/merge-base {start_base} {zero}",
                       f"update {prefix}/start-tree {tree} {zero}"])
        bound, status = discovered, "pinned"
    base_course = load_course(base_snapshot, findings)
    return 0, dict(result, status=status, guard_prefix=prefix, invocation_id=invocation_id, prior_runs=prior_runs,
                   base_sha=base_sha, merge_base=start_base, diff_base=diff_base, bound_specs=bound,
                   base_constraints=base_course.accepted if base_course else None, **findings.rejected)


def cmd_bind_pr(git: Git, args) -> tuple[int, dict]:
    if not (args.repo and args.pr) or not re.fullmatch(r"[^/\s]+/[^/\s]+", args.repo):
        raise GuardError("bind-pr needs --repo owner/repo and --pr <n>")
    run = load_run(git, args.guard_prefix, args.invocation_id)
    if not run.prefix.startswith("refs/spec-guard/branch/"):
        raise GuardError("bind-pr moves a branch-namespace run; this run is already PR-bound")
    pending = [name for name in CHECKPOINTS if name in run.refs]
    if pending:
        raise GuardError("pending pre-rebase checkpoint; run survival before bind-pr", pending=pending)
    new_prefix = f"{pr_namespace(args.repo, args.pr)}/{run.invocation_id}"
    zero = zero_oid(git)
    commands = [f"verify {run.prefix}/{name} {zero}" for name in CHECKPOINTS]
    commands += [f"update {new_prefix}/{name} {run.refs[name]} {zero}" for name in BASELINE]
    commands += [f"delete {run.prefix}/{name} {run.refs[name]}" for name in BASELINE]
    transact(git, commands)
    return 0, {"status": "bound", "guard_prefix": new_prefix, "invocation_id": run.invocation_id,
               "previous_guard_prefix": run.prefix}


def cmd_rebase_pin(git: Git, args) -> tuple[int, dict]:
    run = load_run(git, args.guard_prefix, args.invocation_id)
    pending = [name for name in CHECKPOINTS if name in run.refs]
    if pending:
        raise GuardError("a pre-rebase checkpoint is already pending; run survival first", pending=pending)
    if args.pending_lease is not None and not args.pre_rebase_head:
        raise GuardError("--pending-lease needs --pre-rebase-head")
    base_sha = resolve_base(git, args)
    head = resolve_commit(git, "HEAD", "HEAD")
    kept = resolve_commit(git, args.pre_rebase_head, "--pre-rebase-head") if args.pre_rebase_head else head
    branch = args.branch or current_branch(git)
    endpoint, observed = observe(git, args.push_remote, branch)
    result = {"guard_prefix": run.prefix, "invocation_id": run.invocation_id, "base_sha": base_sha,
              "push_endpoint": endpoint, "observed_remote_sha": observed, "pre_rebase_head": kept,
              "pending_lease": observed or ABSENT}
    problem = lease_problem(git, observed, kept, pending_lease_arg(git, args.pending_lease))
    if problem:
        return 1, dict(result, status="remote_head_diverged", remote_head_diverged=True, reason=problem)
    before_base = merge_base(git, base_sha, head)
    zero = zero_oid(git)
    transact(git, [f"verify {run.prefix}/start-tree {run.refs['start-tree']}",
                   f"update {run.prefix}/pre-rebase {head} {zero}",
                   f"update {run.prefix}/pre-rebase-base {before_base} {zero}"])
    return 0, dict(result, status="pre-rebase pinned", remote_head_diverged=False, pre_rebase=head,
                   pre_rebase_base=before_base)


def cmd_survival(git: Git, args) -> tuple[int, dict]:
    run = load_run(git, args.guard_prefix, args.invocation_id)
    base_sha = resolve_base(git, args)
    head = resolve_commit(git, "HEAD", "HEAD")
    findings = Findings()
    failures = survival_failures(git, run, Snapshot(git, head, "HEAD"), Snapshot(git, base_sha, "base_sha"), findings)
    result = {"guard_prefix": run.prefix, "invocation_id": run.invocation_id, "base_sha": base_sha,
              "merge_base": merge_base(git, base_sha, head), "head_sha": head, "survival": failures,
              **findings.rejected}
    if failures or any(findings.rejected.values()):
        return 1, dict(result, status="violation", cleared_pre_rebase=False)
    cleared = all(name in run.refs for name in CHECKPOINTS)
    if cleared:
        transact(git, [f"verify {run.prefix}/start-tree {run.refs['start-tree']}"]
                 + [f"delete {run.prefix}/{name} {run.refs[name]}" for name in CHECKPOINTS])
    return 0, dict(result, status="ok", cleared_pre_rebase=cleared)


def worktree_entry(git: Git, path: str) -> tuple[str, str] | None:
    full = git.cwd / path
    if full.is_symlink():
        return "120000", git.out("hash-object", "--stdin", input=os.readlink(full).encode("utf-8", "surrogateescape"))
    if not full.is_file():
        return None
    mode = "100755" if full.stat().st_mode & 0o111 else "100644"
    return mode, git.out("hash-object", "--", path)


def in_change_paths(path: str, change_paths: list[str]) -> bool:
    return any(path == item or path.startswith(item.rstrip("/") + "/") for item in change_paths)


def check_candidate(git: Git, args, base_sha: str) -> tuple[str | None, str, Snapshot]:
    if args.stage == "pre-commit":
        return None, merge_base(git, base_sha, resolve_commit(git, "HEAD", "HEAD")), Snapshot(git, None, "index")
    head = verify_head(git, args) if args.stage == "final" else None
    cand = head or (resolve_commit(git, args.cand_sha, "--cand-sha") if args.cand_sha
                    else resolve_commit(git, "HEAD", "HEAD"))
    return cand, merge_base(git, base_sha, cand), Snapshot(git, cand, "cand")


def cmd_check(git: Git, args) -> tuple[int, dict]:
    run = load_run(git, args.guard_prefix, args.invocation_id)
    base_sha = resolve_base(git, args)
    cand_sha, base_cmp, cand = check_candidate(git, args, base_sha)
    findings = Findings()
    base_cmp_snapshot = Snapshot(git, base_cmp, "base_cmp")
    upstream = Snapshot(git, base_sha, "base_sha")
    run_start = run_start_snapshot(git, run)
    fork = Snapshot(git, run.refs["merge-base"], "merge-base")
    change_paths = [repo_path(path, "--change-paths") for group in (args.change_paths or []) for path in group]

    worktree: dict[str, tuple[str, str] | None] = {}
    if cand_sha is None:
        changed = diff_names(git, (base_cmp,), cached=True)
        for path in (diff_names(git) + untracked(git)) if change_paths else []:
            if in_change_paths(path, change_paths) and path not in changed:
                worktree[path] = worktree_entry(git, path)
        changed += sorted(worktree)
    else:
        changed = diff_names(git, (base_cmp, cand_sha))
    # Untracked drafts belong to this run only in the checkout that produces the candidate.
    owns_checkout = cand_sha is None or (args.stage == "pre-push" and cand_sha == resolve_commit(git, "HEAD", "HEAD"))
    local_specs = untracked(git, (SPEC_PATHSPEC,)) if owns_checkout else []
    bound = update_bound(git, run, [path for path in changed + local_specs if is_spec(path)])

    def cand_entry(path: str):
        return worktree[path] if path in worktree else cand.entry(path)

    for snapshot in (base_cmp_snapshot, cand, upstream, run_start, fork):
        snapshot.prefetch([COURSE] + bound + (changed if snapshot in (base_cmp_snapshot, cand) else []))
    validation, warnings, unstaged, deletions, criteria = [], [], [], [], []
    rebase_recommended = False
    for spec in bound:
        found = cand.entry(spec)
        if found is None and cand_sha is None and os.path.lexists(git.cwd / spec):
            unstaged.append(spec)  # unstaged untracked addition: fine until pre-push
            continue
        if found is not None and found[0] not in REGULAR_MODES:
            findings.reject(spec, found[0], cand.label)
            continue
        deletion_ok = approved_spec_deletion(run.approvals, spec)
        if found is None:
            deletions.append({"spec": spec, "status": "approved" if deletion_ok else "unapproved"})
        text = cand.text(spec, findings)
        now = facts_at(cand, spec, findings)
        base_facts = facts_at(base_cmp_snapshot, spec, findings)
        start_facts = facts_at(run_start, spec, findings)
        upstream_facts = facts_at(upstream, spec, findings)
        seen = set()
        for label, accepted, fork_facts in (("base", base_facts, base_facts),
                                            ("run_start", start_facts, facts_at(fork, spec, findings))):
            for criterion, old in (accepted.criteria.items() if accepted else ()):
                new = now.criteria.get(criterion) if now else None
                if new == old or (criterion, old) in seen:
                    continue
                seen.add((criterion, old))
                if upstream_match(upstream_facts, fork_facts, criterion, old, new):
                    status = "upstream_base"
                elif (deletion_ok and now is None) or approved_criterion(run.approvals, spec, criterion, old, new):
                    status = "approved"
                else:
                    status = "unapproved"
                criteria.append({"spec": spec, "criterion": criterion, "baseline": label, "from_text": old,
                                 "to_text": new, "status": status})
        if base_cmp != base_sha and base_facts and upstream_facts:
            for criterion in sorted(set(base_facts.criteria) | set(upstream_facts.criteria)):
                old, new = base_facts.criteria.get(criterion), upstream_facts.criteria.get(criterion)
                if old != new:
                    rebase_recommended = True
                    criteria.append({"spec": spec, "criterion": criterion, "baseline": "base_sha", "from_text": old,
                                     "to_text": new, "status": "upstream_base"})
        if now is None:
            continue
        if now.legacy:
            warnings.append({"spec": spec, "code": "legacy-format",
                             "message": "pre-engineering spec (no #acceptance/#coverage, no contract markers); "
                                        "validation skipped"})
            continue
        previous_label = "base_cmp" if base_facts else "run_start" if start_facts else None
        previous = base_cmp_snapshot.text(spec, findings) if base_facts else run_start.text(spec, findings) \
            if start_facts else None
        diagnostics = validate_spec(spec, text, now, previous, cand, findings)
        if diagnostics:
            validation.append({"spec": spec, "previous": previous_label, "diagnostics": diagnostics})

    base_course, cand_course = load_course(base_cmp_snapshot, findings), load_course(cand, findings)
    upstream_course = load_course(upstream, findings)
    governed = []
    fields = accepted_diff(course_parser.governed_view(base_course), course_parser.governed_view(cand_course))
    if fields:
        from_entry, to_entry = entry_str(base_cmp_snapshot.entry(COURSE)), entry_str(cand_entry(COURSE))
        status = "approved" if approved_path(run.approvals, COURSE, from_entry, to_entry) else "unapproved"
        governed.append({"path": COURSE, "baseline": "base_cmp", "from_entry": from_entry, "to_entry": to_entry,
                         "fields": fields, "status": status})
    if base_cmp != base_sha:
        fields = accepted_diff(course_parser.governed_view(base_course), course_parser.governed_view(upstream_course))
        if fields:
            rebase_recommended = True
            governed.append({"path": COURSE, "baseline": "base_sha", "from_entry": entry_str(base_cmp_snapshot.entry(COURSE)),
                             "to_entry": entry_str(upstream.entry(COURSE)), "fields": fields, "status": "upstream_base"})

    boundaries = course_parser.protected_paths(upstream_course) if upstream_course else []
    adrs = adr_paths(base_course, cand_course, upstream_course)
    hits, judgment = [], []
    for path in changed:
        from_entry, to_entry = entry_str(base_cmp_snapshot.entry(path)), entry_str(cand_entry(path))
        if path.startswith("specs/") or path in adrs:
            judgment.append({"path": path, "from_entry": from_entry, "to_entry": to_entry})
        matched = [boundary for boundary in boundaries if course_parser.match_protected_path(path, boundary)]
        if matched:
            status = "approved" if approved_path(run.approvals, path, from_entry, to_entry) else "unapproved"
            hits.append({"path": path, "boundaries": matched, "from_entry": from_entry, "to_entry": to_entry,
                         "status": status})

    survival = survival_failures(git, run, cand, upstream, findings, skip=tuple(unstaged))
    violations = [name for name, failed in (
        ("accepted_criteria_changed", any(item["status"] == "unapproved" for item in criteria)),
        ("governed_course_changes", any(item["status"] == "unapproved" for item in governed)),
        ("protected_path_hits", any(item["status"] == "unapproved" for item in hits)),
        ("bound_spec_deletions", any(item["status"] == "unapproved" for item in deletions)),
        ("validation", bool(validation)),
        ("survival", bool(survival)),
        ("symlink_rejected", bool(findings.rejected["symlink_rejected"])),
        ("unsupported_tree_entry", bool(findings.rejected["unsupported_tree_entry"])),
    ) if failed]
    result = {"status": "violation" if violations else "ok", "stage": args.stage, "guard_prefix": run.prefix,
              "invocation_id": run.invocation_id, "base_sha": base_sha, "base_cmp": base_cmp,
              "merge_base": base_cmp if cand_sha is None else None, "diff_base": None if cand_sha is None else base_cmp, "cand_sha": cand_sha, "bound_specs": bound,
              "unstaged_specs": unstaged, "bound_spec_deletions": deletions, "validation": validation,
              "warnings": warnings, "accepted_criteria_changed": criteria, "governed_course_changes": governed,
              "protected_path_hits": hits, "survival": survival, "rebase_recommended": rebase_recommended,
              "changed_paths": changed, "spec_course_adr_diffs": judgment,
              "base_constraints": upstream_course.accepted if upstream_course else None,
              "violations": violations, **findings.rejected}
    return (1 if violations else 0), result


def approval_record(args) -> dict:
    chosen = [flag for flag in ("delete_spec", "amend_criterion", "delete_criterion", "allow_path")
              if getattr(args, flag)]
    if len(chosen) != 1:
        raise GuardError("pass exactly one of --delete-spec, --amend-criterion, --delete-criterion, --allow-path")
    if not (args.reason or "").strip():
        raise GuardError("--reason is required")
    record = {"reason": args.reason.strip(), "approved_at": now_iso()}
    kind = chosen[0]
    if kind == "delete_spec":
        return dict(record, kind="delete-spec", spec=repo_path(args.delete_spec, "--delete-spec"))
    if kind == "allow_path":
        path = repo_path(args.allow_path, "--allow-path")
        if args.allow_path.rstrip().endswith("/") or any(char in path for char in "*?["):
            raise GuardError("--allow-path takes one exact file path, never a prefix or glob")
        for flag, value in (("--from-entry", args.from_entry), ("--to-entry", args.to_entry)):
            if value != ABSENT and not ENTRY.fullmatch(value or ""):
                raise GuardError(f"{flag} must be <mode>:<oid> (for example 100644:<40-hex>) or absent")
        return dict(record, kind="allow-path", path=path, from_entry=args.from_entry, to_entry=args.to_entry)
    target = args.amend_criterion or args.delete_criterion
    spec, _, criterion = target.rpartition(":")
    if not spec or not criterion.startswith("ac-"):
        raise GuardError("criterion target must look like <spec>:<ac-id>")
    if args.from_text is None:
        raise GuardError("--from-text is required")
    record.update(spec=repo_path(spec, "criterion spec"), criterion=criterion,
                  from_text=validate_plan.normalize_text(args.from_text))
    if kind == "delete_criterion":
        return dict(record, kind="delete-criterion")
    if args.to_text is None:
        raise GuardError("--amend-criterion needs --to-text")
    return dict(record, kind="amend-criterion", to_text=validate_plan.normalize_text(args.to_text))


def cmd_approve(git: Git, args) -> tuple[int, dict]:
    run = load_run(git, args.guard_prefix, args.invocation_id)
    record = approval_record(args)
    approvals = run.approvals + [record]
    data = (json.dumps(approvals, indent=2, sort_keys=True) + "\n").encode()
    tree = build_tree(git, {"approvals.json": data}, base_tree=run.refs["start-tree"])
    transact(git, [f"update {run.prefix}/start-tree {tree} {run.refs['start-tree']}"])
    return 0, {"status": "approved", "guard_prefix": run.prefix, "invocation_id": run.invocation_id,
               "approval": record, "approvals": approvals}


def delete_prefix(git: Git, prefix: str, refs: dict) -> None:
    zero = zero_oid(git)
    commands = [f"delete {prefix}/{name} {oid}" for name, oid in sorted(refs.items())]
    commands += [f"verify {prefix}/{name} {zero}" for name in CHECKPOINTS if name not in refs]
    transact(git, commands)


def prune_stale(git: Git, days: int) -> tuple[list[str], list[dict]]:
    pruned, skipped = [], []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    runs = {**group_runs(git, "refs/spec-guard/branch/"), **group_runs(git, "refs/spec-guard/pr/")}
    for prefix, refs in sorted(runs.items()):
        if any(name in refs for name in CHECKPOINTS):
            skipped.append({"guard_prefix": prefix, "reason": "pending pre-rebase checkpoint"})
            continue
        created = (read_run_id(git, refs.get("start-tree")) or {}).get("created_at", "")
        try:
            stamp = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
            stamp = stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)
        except ValueError:
            skipped.append({"guard_prefix": prefix, "reason": "unreadable run-id.txt created_at"})
            continue
        if stamp > cutoff:
            skipped.append({"guard_prefix": prefix, "reason": f"newer than {days} days"})
            continue
        try:
            delete_prefix(git, prefix, refs)
            pruned.append(prefix)
        except GuardError as exc:
            skipped.append({"guard_prefix": prefix, "reason": str(exc)})
    return pruned, skipped


def cmd_cleanup(git: Git, args) -> tuple[int, dict]:
    result: dict = {"status": "ok"}
    if args.guard_prefix or args.invocation_id or not args.prune_stale:
        run = load_run(git, args.guard_prefix, args.invocation_id)
        refs = prefix_refs(git, run.prefix)
        delete_prefix(git, run.prefix, refs)
        result.update(guard_prefix=run.prefix, invocation_id=run.invocation_id, deleted=sorted(refs))
    if args.prune_stale:
        if args.older_than_days < 0:
            raise GuardError("--older-than-days must be >= 0")
        result["pruned"], result["prune_skipped"] = prune_stale(git, args.older_than_days)
    return 0, result


# ---------------------------------------------------------------- CLI

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="spec_guard.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", metavar="command")
    subparsers.required = True

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="print one JSON object on stdout")
    ids = argparse.ArgumentParser(add_help=False)
    ids.add_argument("--guard-prefix", help="refs/spec-guard/... prefix returned by pin or bind-pr")
    ids.add_argument("--invocation-id", help="invocation_id returned by pin")
    base = argparse.ArgumentParser(add_help=False)
    base.add_argument("--base-remote", help="remote (name or URL) holding the target base branch")
    base.add_argument("--base-branch", help="target base branch name on --base-remote")
    base.add_argument("--local-base", help="local base branch when no remote exists")
    pr = argparse.ArgumentParser(add_help=False)
    pr.add_argument("--repo", help="owner/repo of the PR")
    pr.add_argument("--pr", type=int, help="PR number; selects the PR ref namespace")
    pr.add_argument("--head-sha", help="live PR headRefOid; fetched from refs/pull/<n>/head if absent locally")
    lease = argparse.ArgumentParser(add_help=False)
    lease.add_argument("--push-remote", help="remote whose single effective push URL is observed")
    lease.add_argument("--branch", help="head branch name (defaults to the checked-out branch)")
    lease.add_argument("--pre-rebase-head", help="kept pre-rebase head the remote tip must be an ancestor of")
    lease.add_argument("--pending-lease", help="lease retained from an earlier rebase: <sha> or absent")

    pin = subparsers.add_parser("pin", parents=[common, ids, base, pr, lease],
                                help="pin run-start baselines, or report guard: n/a")
    pin.add_argument("--cand-sha", help="exact outgoing commit about to be pushed (pre-push)")
    pin.add_argument("--checkout-owns-pr", action="store_true", help="local checkout is confirmed to be the PR")
    pin.add_argument("--spec", action="append", help="user-named or PR-referenced spec path (repeatable)")
    pin.add_argument("--resume", action="store_true", help="restore the run named by --guard-prefix/--invocation-id")
    pin.add_argument("--run-start-head", help="initial_head_sha from an earlier guard: n/a pin")
    pin.add_argument("--run-start-merge-base", help="initial_merge_base from an earlier guard: n/a pin")
    pin.set_defaults(handler=cmd_pin)

    bind = subparsers.add_parser("bind-pr", parents=[common, ids],
                                 help="atomically move a branch run to the PR namespace")
    bind.add_argument("--repo", help="owner/repo of the PR")
    bind.add_argument("--pr", type=int, help="PR number")
    bind.set_defaults(handler=cmd_bind_pr)

    rebase = subparsers.add_parser("rebase-pin", parents=[common, ids, base, lease],
                                   help="create-only pre-rebase checkpoint after a lease check")
    rebase.set_defaults(handler=cmd_rebase_pin)

    survival = subparsers.add_parser("survival", parents=[common, ids, base],
                                     help="verify branch-only criteria/amendments/metadata survived a rebase")
    survival.set_defaults(handler=cmd_survival)

    check = subparsers.add_parser("check", parents=[common, ids, base, pr],
                                  help="validate bound specs, course, and protected paths at a gate")
    check.add_argument("--stage", required=True, choices=("pre-commit", "pre-push", "final"))
    check.add_argument("--cand-sha", help="exact commit to check at pre-push/final (default HEAD)")
    check.add_argument("--change-paths", nargs="+", action="append",
                       help="pre-commit: unstaged paths about to be committed")
    check.set_defaults(handler=cmd_check)

    approve = subparsers.add_parser("approve", parents=[common, ids],
                                    help="record ONE exact user-approved exception in approvals.json")
    approve.add_argument("--delete-spec", help="bound spec path whose deletion the user approved")
    approve.add_argument("--amend-criterion", help="<spec>:<ac-id> rewrite the user approved")
    approve.add_argument("--delete-criterion", help="<spec>:<ac-id> removal the user approved")
    approve.add_argument("--allow-path", help="exact changed file path the user approved")
    approve.add_argument("--from-text", help="normalized accepted criterion text before the change")
    approve.add_argument("--to-text", help="normalized approved criterion text after the change")
    approve.add_argument("--from-entry", help="<base_cmp> entry: <mode>:<oid> or absent")
    approve.add_argument("--to-entry", help="<cand> entry: <mode>:<oid> or absent")
    approve.add_argument("--reason", help="why the user approved it")
    approve.set_defaults(handler=cmd_approve)

    cleanup = subparsers.add_parser("cleanup", parents=[common, ids],
                                    help="atomically delete this run's refs; optionally prune stale runs")
    cleanup.add_argument("--prune-stale", action="store_true", help="also prune abandoned runs")
    cleanup.add_argument("--older-than-days", type=int, default=14, help="prune age threshold (default 14)")
    cleanup.set_defaults(handler=cmd_cleanup)
    return parser


def emit(result: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    stream = sys.stderr if result.get("status") == "error" else sys.stdout
    for key in sorted(result):
        value = result[key]
        print(f"{key}: {value if isinstance(value, str) else json.dumps(value, sort_keys=True)}", file=stream)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        top = Git(Path.cwd()).run("rev-parse", "--show-toplevel", check=False)
        if top.returncode:
            raise GuardError("run spec_guard.py inside a git worktree")
        code, result = args.handler(Git(Path(decode(top.stdout).strip())), args)
    except GuardError as exc:
        code, result = 2, {"status": "error", "error": str(exc), **exc.fields}
    emit(result, args.json)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
