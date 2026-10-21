import { execFile } from 'node:child_process';
import { createHash } from 'node:crypto';
import { copyFile, mkdir, mkdtemp, readFile, realpath, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { Type, type Static } from 'typebox';
import {
  FindingSchema, OmissionSchema, PathSchema, RevisionSchema, ReviewError, SnapshotIdentitySchema,
  hash, safePath, validate, validateFindingEvidence, validateRequest,
  type Finding, type Omission, type Policy, type ReviewRequest,
} from './contracts.js';

export const FILTER_VERSION = 'git-text-v1';
export const TOOL_VERSION = 'pinned-read-search-v1';
const ChangeSchema = Type.Object({
  status: Type.Union([Type.Literal('A'), Type.Literal('D'), Type.Literal('M'), Type.Literal('R'), Type.Literal('T')]),
  oldPath: Type.Union([PathSchema, Type.Null()]), path: PathSchema,
  oldMode: Type.String(), mode: Type.String(), oldObject: Type.String(), object: Type.String(),
  summary: Type.Union([Type.String(), Type.Null()]),
}, { additionalProperties: false });
const PayloadSchema = Type.Object({
  goal: Type.String(), baseMeaning: Type.Literal('merge-base'),
  inventory: Type.Array(ChangeSchema, { maxItems: 60 }),
  diff: Type.Array(Type.Object({ path: PathSchema, patch: Type.String() }, { additionalProperties: false })),
  context: Type.Array(Type.Object({ path: PathSchema, revision: RevisionSchema, text: Type.String() }, { additionalProperties: false })),
  omissions: Type.Array(OmissionSchema),
}, { additionalProperties: false });
export const SnapshotSchema = Type.Object({ identity: SnapshotIdentitySchema, payload: PayloadSchema, omissions: Type.Array(OmissionSchema), payloadBytes: Type.Integer({ minimum: 0, maximum: 32768 }) }, { additionalProperties: false });
export type Snapshot = Static<typeof SnapshotSchema>;
type Change = Static<typeof ChangeSchema>;
type Revision = Static<typeof RevisionSchema>;
const ReadSchema = Type.Object({ revision: RevisionSchema, path: PathSchema, start: Type.Integer({ minimum: 1 }), end: Type.Integer({ minimum: 1 }) }, { additionalProperties: false });
const SearchSchema = Type.Object({ revision: RevisionSchema, literal: Type.String({ minLength: 1, maxLength: 256 }), pathPrefix: Type.String({ maxLength: 1024 }) }, { additionalProperties: false });
export const SOURCE_TOOL_SCHEMAS = Object.freeze({ read_git: ReadSchema, search_git: SearchSchema });
export class SnapshotError extends ReviewError {
  constructor(message: string, readonly omissions: readonly Omission[] = [], code: 20 | 21 | 30 = 20) { super(code, message); this.name = 'SnapshotError'; }
}

// Explicit allowlisted environment. Never inherit Git, provider, SSH, loader or auth settings.
function gitEnvironment(): NodeJS.ProcessEnv {
  return {
    PATH: '/usr/bin:/bin', HOME: '/dev/null', XDG_CONFIG_HOME: '/dev/null', LC_ALL: 'C',
    GIT_CONFIG_NOSYSTEM: '1', GIT_CONFIG_GLOBAL: '/dev/null', GIT_ATTR_NOSYSTEM: '1',
    GIT_TERMINAL_PROMPT: '0', GIT_NO_REPLACE_OBJECTS: '1', GIT_NO_LAZY_FETCH: '1',
    GIT_OPTIONAL_LOCKS: '0', GIT_PAGER: 'cat', GIT_PROTOCOL_FROM_USER: '0',
  };
}
const gitOptions = ['--no-pager', '--no-optional-locks', '--no-replace-objects', '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false', '-c', 'protocol.allow=never'];
function git(cwd: string, args: readonly string[], policy: Policy, extraEnv: NodeJS.ProcessEnv = {}): Promise<Buffer> {
  return new Promise((accept, reject) => {
    execFile('/usr/bin/git', [...gitOptions, ...args], { cwd, env: { ...gitEnvironment(), ...extraEnv }, encoding: 'buffer', timeout: policy.gitTimeoutMs, maxBuffer: policy.gitOutputBytes, windowsHide: true, killSignal: 'SIGKILL' }, (error, stdout) => {
      if (error) reject(new SnapshotError('Git object operation failed, timed out or exceeded output limit'));
      else accept(stdout);
    });
  });
}
function utf8(buffer: Buffer): string {
  const text = buffer.toString('utf8');
  if (!Buffer.from(text).equals(buffer)) throw new SnapshotError('Non-UTF-8 Git metadata');
  return text;
}
function nul(text: string): string[] {
  if (!text) return [];
  if (!text.endsWith('\0')) throw new SnapshotError('Incomplete NUL-delimited Git output');
  return text.slice(0, -1).split('\0');
}
function objectId(value: string): string {
  if (!/^(?:[a-f0-9]{40}|[a-f0-9]{64})$/.test(value)) throw new SnapshotError('Invalid pinned object ID');
  return value;
}
function bytes(value: unknown): number { return Buffer.byteLength(JSON.stringify(value), 'utf8'); }
const lockNames = new Set(['pnpm-lock.yaml', 'package-lock.json', 'npm-shrinkwrap.json', 'yarn.lock', 'bun.lock', 'bun.lockb', 'Cargo.lock', 'Gemfile.lock', 'poetry.lock', 'uv.lock', 'composer.lock', 'go.sum']);
function lockfile(path: string): boolean { return lockNames.has(path.split('/').at(-1) ?? ''); }
function pathExclusion(path: string): string | null {
  if (!safePath(path)) return 'unsafe path';
  if (containsSecret(path)) return 'sensitive path';
  if (/(^|\/)(?:\.env(?:\..*)?|\.npmrc|\.netrc|\.pypirc|\.git-credentials|auth\.json|credentials(?:\..*)?|secrets?(?:\..*)?|id_(?:rsa|ed25519)|\.ssh|\.aws|private|\.private)(?:\/|$)/i.test(path)
    || /\.(?:pem|key|p12|pfx|keystore|sqlite3?|db|log|csv|tsv|env|secrets?)$/i.test(path)) return 'private or credential data';
  if (lockfile(path)) return 'lock payload (summary only)';
  if (/(^|\/)(?:node_modules|vendor|dist|build|coverage|generated|\.next|\.cache)(?:\/|$)/i.test(path)
    || /(?:\.min\.[cm]?js|\.map|\.generated\.[^/]+)$/i.test(path)) return 'generated or vendor payload';
  return null;
}
// Conservative detector, not an export guarantee. Deny whole file, not just matching line.
export function containsSecret(text: string): boolean {
  return /-----BEGIN (?:[A-Z ]*PRIVATE KEY|OPENSSH PRIVATE KEY)-----/.test(text)
    || /\b(?:sk-(?:ant-)?[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|xox[baprs]-[A-Za-z0-9-]{12,})\b/.test(text)
    || /(?:password|passwd|secret|api[_-]?key|access[_-]?token|authorization)\s*[=:]\s*["']?(?!(?:process\.|import\.|\$\{|<|REDACTED|EXAMPLE|placeholder|undefined|null|false|true)\b)[A-Za-z0-9_+\/.=-]{8,}/i.test(text)
    || /\bBearer\s+[A-Za-z0-9._~+/-]{16,}={0,2}/i.test(text)
    || /\bAIza[A-Za-z0-9_-]{30,}\b/.test(text)
    || /https?:\/\/[^\s/@:]+:[^\s/@]+@/i.test(text);
}
type TreeEntry = { path: string; mode: string; oid: string; size: number };
function parseTree(buffer: Buffer, limit: number): Map<string, TreeEntry> {
  const entries = nul(utf8(buffer));
  if (entries.length > limit) throw new SnapshotError('Tracked tree exceeds entry limit');
  const tree = new Map<string, TreeEntry>();
  for (const entry of entries) {
    const match = /^(\d{6}) (blob|commit) ([a-f0-9]+) +([0-9]+|-)\t([\s\S]+)$/.exec(entry);
    if (!match) throw new SnapshotError('Invalid Git tree entry');
    const [, mode, , oid, size, path] = match;
    if (!mode || !oid || !size || !path || tree.has(path)) throw new SnapshotError('Invalid or duplicate tree path');
    tree.set(path, { path, mode, oid: objectId(oid), size: size === '-' ? 0 : Number(size) });
  }
  return tree;
}
function parseChanges(buffer: Buffer): Change[] {
  const fields = nul(utf8(buffer));
  const changes: Change[] = [];
  for (let i = 0; i < fields.length;) {
    const header = fields[i++];
    const match = header && /^:(\d{6}) (\d{6}) ([a-f0-9]+) ([a-f0-9]+) ([ADMRT])\d*$/.exec(header);
    if (!match) throw new SnapshotError('Unsupported changed path status');
    const [, oldMode, mode, oldObject, object, status] = match;
    const first = fields[i++];
    const path = status === 'R' ? fields[i++] : first;
    if (!first || !path || !oldMode || !mode || !oldObject || !object || !status) throw new SnapshotError('Truncated changed-path inventory');
    changes.push(validate(ChangeSchema, { status, oldPath: status === 'R' ? first : status === 'A' ? null : path, path, oldMode, mode, oldObject: objectId(oldObject), object: objectId(object), summary: null }));
  }
  return changes;
}
type Span = { start: number; end: number };
function patchSpans(patch: string): { base: Span[]; head: Span[] } {
  const spans: { base: Span[]; head: Span[] } = { base: [], head: [] };
  let base = 0; let head = 0; let inHunk = false;
  for (const line of patch.split('\n')) {
    const hunk = /^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/.exec(line);
    if (hunk) { base = Number(hunk[1]); head = Number(hunk[2]); inHunk = true; continue; }
    if (!inHunk) continue;
    if (line.startsWith('-')) { spans.base.push({ start: base, end: base }); base++; }
    else if (line.startsWith('+')) { spans.head.push({ start: head, end: head }); head++; }
    else if (line.startsWith(' ')) { base++; head++; }
  }
  return spans;
}
function deepFreeze<T>(value: T): T {
  if (value !== null && typeof value === 'object') { for (const child of Object.values(value)) deepFreeze(child); Object.freeze(value); }
  return value;
}

/** Captures only committed Git objects. No checkout, fetch, hooks, credentials, model or product execution. */
export async function captureSnapshot(input: unknown) {
  const request: ReviewRequest = structuredClone(validateRequest(input));
  const policy = { ...request.policy };
  if (containsSecret(request.goal)) throw new SnapshotError('Suspected secret in user goal');
  const started = Date.now();
  const checkDeadline = () => { if (Date.now() - started > policy.roundDeadlineMs) throw new SnapshotError('Snapshot capture deadline exceeded'); };
  let repo: string;
  try { repo = await realpath(request.repo); } catch { throw new SnapshotError('Cannot locate requested checkout', [], 30); }
  const original = async (args: readonly string[]) => utf8(await git(repo, args, policy)).trimEnd();
  let toplevel: string;
  try { toplevel = await realpath(await original(['rev-parse', '--show-toplevel'])); } catch { throw new SnapshotError('Not a Git checkout', [], 30); }
  if (repo !== toplevel) throw new SnapshotError('Repo must be canonical checkout root', [], 30);
  const commonDir = await realpath(await original(['rev-parse', '--path-format=absolute', '--git-common-dir']));
  const objects = await realpath(await original(['rev-parse', '--path-format=absolute', '--git-path', 'objects']));
  const index = await original(['rev-parse', '--path-format=absolute', '--git-path', 'index']);
  const objectFormat = await original(['rev-parse', '--show-object-format']);
  if (objectFormat !== 'sha1' && objectFormat !== 'sha256') throw new SnapshotError('Unsupported object format');
  // Resolve user refs once, with end-of-options. Object operations below never consume refs.
  const base = objectId(await original(['rev-parse', '--verify', '--end-of-options', `${request.baseRef}^{commit}`]));
  const head = objectId(await original(['rev-parse', '--verify', '--end-of-options', `${request.headRef}^{commit}`]));
  const checkoutHead = objectId(await original(['rev-parse', '--verify', 'HEAD^{commit}']));
  if (checkoutHead !== head) throw new SnapshotError('Candidate is not checked-out HEAD', [], 21);
  const isolated = await mkdtemp(join(await realpath(tmpdir()), 'file-pr-git-'));
  try {
    // An isolated index/config avoids fsmonitor, clean/process filters, include files and extensions
    // from repo config. Objects alone point back to the original immutable object store.
    await writeFile(join(isolated, 'config'), `[core]\nrepositoryformatversion = ${objectFormat === 'sha256' ? 1 : 0}\nbare = false\nfilemode = true\nuntrackedCache = false\n${objectFormat === 'sha256' ? '[extensions]\nobjectformat = sha256\n' : ''}`, { mode: 0o600 });
    await writeFile(join(isolated, 'HEAD'), `${head}\n`, { mode: 0o600 });
    await writeFile(join(isolated, 'description'), 'isolated review\n', { mode: 0o600 });
    // Git recognizes a repository only with an objects and refs directory.
    await mkdir(join(isolated, 'objects')); await mkdir(join(isolated, 'refs'));
    await copyFile(index, join(isolated, 'index'));
    const environment = { GIT_DIR: isolated, GIT_WORK_TREE: repo, GIT_OBJECT_DIRECTORY: objects };
    const run = async (args: readonly string[]) => { checkDeadline(); return git(repo, args, policy, environment); };
    const text = async (args: readonly string[]) => utf8(await run(args)).trimEnd();
    const flags = nul(utf8(await run(['ls-files', '-v', '-z'])));
    if (flags.some(entry => !entry.startsWith('H '))) throw new SnapshotError('Sparse, assume-unchanged or unsupported index flags', [], 21);
    const dirtyIndex = await run(['diff-index', '--cached', '--raw', '-z', '--no-ext-diff', '--no-textconv', '--ignore-submodules=none', head, '--']);
    const dirty = await run(['status', '--porcelain=v1', '-z', '--untracked-files=all', '--ignore-submodules=all']);
    if (dirtyIndex.length || dirty.length) throw new SnapshotError('Dirty tracked or untracked input', [], 21);
    const mergeBases = (await text(['merge-base', '--all', base, head])).split('\n');
    if (mergeBases.length !== 1) throw new SnapshotError('Ambiguous merge base');
    const mergeBase = objectId(mergeBases[0] ?? '');
    const baseTree = objectId(await text(['rev-parse', `${base}^{tree}`]));
    const headTree = objectId(await text(['rev-parse', `${head}^{tree}`]));
    const mergeBaseTree = objectId(await text(['rev-parse', `${mergeBase}^{tree}`]));
    const changes = parseChanges(await run(['diff', '--raw', '-z', '--no-abbrev', '--no-ext-diff', '--no-textconv', '--find-renames=50%', mergeBase, head, '--']));
    if (!changes.length) throw new SnapshotError('Empty candidate diff');
    if (changes.length > policy.maxChangedFiles) throw new SnapshotError('Changed-file limit exceeded');
    if (changes.some(change => containsSecret(change.path) || (change.oldPath && containsSecret(change.oldPath)))) throw new SnapshotError('Sensitive changed path');
    const trees = {
      base: parseTree(await run(['ls-tree', '-r', '-l', '-z', mergeBaseTree]), policy.maxTreeEntries),
      head: parseTree(await run(['ls-tree', '-r', '-l', '-z', headTree]), policy.maxTreeEntries),
    };
    const sources = { base: new Map<string, string>(), head: new Map<string, string>() };
    const omissions: Omission[] = [];
    const cache = new Map<string, { text?: string; reason?: string }>();
    let scanned = 0;
    const changedPaths = new Set(changes.flatMap(change => [change.path, ...(change.oldPath ? [change.oldPath] : [])]));
    for (const revision of ['base', 'head'] as const) {
      for (const entry of trees[revision].values()) {
        checkDeadline();
        let reason = pathExclusion(entry.path);
        if (entry.mode !== '100644' && entry.mode !== '100755') reason = entry.mode === '120000' ? 'symlink object' : 'submodule or unsupported mode';
        if (!reason && entry.size > policy.maxBlobBytes) reason = 'blob byte limit';
        if (!reason) {
          let content = cache.get(entry.oid);
          if (!content) {
            scanned += entry.size;
            if (scanned > policy.maxScanBytes) throw new SnapshotError('Source scan byte limit exceeded');
            const buffer = await run(['cat-file', 'blob', entry.oid]);
            if (buffer.length !== entry.size) throw new SnapshotError('Unexpected Git blob size');
            const actualObject = createHash(objectFormat).update(`blob ${buffer.length}\0`).update(buffer).digest('hex');
            if (actualObject !== entry.oid) throw new SnapshotError('Git blob identity mismatch');
            const decoded = buffer.toString('utf8');
            if (!Buffer.from(decoded).equals(buffer) || /[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/.test(decoded)) content = { reason: 'binary or non-UTF-8 object' };
            else if (containsSecret(decoded)) content = { reason: 'suspected secret content' };
            else if (decoded.startsWith('version https://git-lfs.github.com/spec/v1\n')) content = { reason: 'LFS pointer; semantic content unavailable' };
            else if (/^(?:[^\n]*\n){0,5}[^\n]*(?:code generated|automatically generated|@generated)[^\n]*(?:do not edit)?/i.test(decoded)) content = { reason: 'generated content marker' };
            else content = { text: decoded };
            cache.set(entry.oid, content);
          }
          reason = content.reason ?? null;
          if (content.text !== undefined) sources[revision].set(entry.path, content.text);
        }
        if (reason) omissions.push({ path: entry.path, revision, reason, changed: changedPaths.has(entry.path), semantic: !lockfile(entry.path) });
      }
    }
    if (omissions.some(item => item.changed && item.semantic)) throw new SnapshotError('Changed semantic source excluded; review incomplete', omissions.filter(item => item.changed));
    const payload: Static<typeof PayloadSchema> = { goal: request.goal, baseMeaning: 'merge-base', inventory: changes, diff: [], context: [], omissions: omissions.filter(item => item.changed) };
    const spans = { base: new Map<string, Span[]>(), head: new Map<string, Span[]>() };
    let diffBytes = 0;
    const paths = [...changedPaths].sort();
    for (const path of paths) {
      if (lockfile(path)) {
        const before = trees.base.get(path); const after = trees.head.get(path);
        const change = changes.find(item => item.path === path || item.oldPath === path);
        if (change) change.summary = `Lock payload excluded; base ${before?.size ?? 0} bytes (${before?.oid ?? 'absent'}); head ${after?.size ?? 0} bytes (${after?.oid ?? 'absent'}).`;
        continue;
      }
      const patch = utf8(await run(['diff', '--text', '--no-ext-diff', '--no-textconv', '--no-color', '--no-renames', `--unified=${policy.contextLines}`, mergeBase, head, '--', `:(literal)${path}`]));
      diffBytes += Buffer.byteLength(patch);
      if (diffBytes > policy.maxDiffBytes) throw new SnapshotError('Full diff byte limit exceeded');
      if (containsSecret(patch)) throw new SnapshotError('Suspected secret in diff metadata');
      payload.diff.push({ path, patch });
      const ranges = patchSpans(patch);
      if (!ranges.base.length && !ranges.head.length) {
        const source = sources.head.get(path) ?? sources.base.get(path);
        if (source === undefined || source.split('\n').length > policy.readLines || bytes({ path, revision: 'head', text: source }) > policy.readBytes) throw new SnapshotError('Mode-only change requires complete bounded source context');
        payload.context.push({ path, revision: sources.head.has(path) ? 'head' : 'base', text: source });
      }
      spans.base.set(path, ranges.base); spans.head.set(path, ranges.head);
    }
    // Changed lockfiles retain complete matching manifest evidence, never lock payload.
    const manifests = new Set<string>();
    for (const path of paths.filter(lockfile)) {
      const directory = path.includes('/') ? path.slice(0, path.lastIndexOf('/') + 1) : '';
      for (const name of ['package.json', 'Cargo.toml', 'Gemfile', 'pyproject.toml', 'composer.json', 'go.mod']) {
        const candidate = directory + name;
        if (trees.head.has(candidate) || trees.base.has(candidate)) manifests.add(candidate);
      }
      if (![...manifests].some(candidate => candidate.startsWith(directory))) throw new SnapshotError('Changed lockfile has no manifest context');
    }
    for (const path of manifests) {
      const revision = trees.head.has(path) ? 'head' : 'base';
      const source = sources[revision].get(path);
      if (source === undefined || source.split('\n').length > policy.readLines || bytes({ path, revision, text: source }) > policy.readBytes) throw new SnapshotError('Required manifest context unavailable or oversized');
      payload.context.push({ path, revision, text: source });
    }
    if (bytes(payload) > policy.payloadBytes) throw new SnapshotError('Full diff and required context exceed request payload limit');
    // Whole small relevant tests/contracts are optional context; no silent slicing.
    for (const [path, source] of [...sources.head.entries()].sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0)) {
      if (changedPaths.has(path) || manifests.has(path) || !/(?:^|\/)(?:[^/]*\.)?(?:test|spec|schema|contract)s?(?:\.|\/)|(?:^|\/)package\.json$/i.test(path)) continue;
      const context = { path, revision: 'head' as const, text: source };
      if (source.split('\n').length <= policy.readLines && bytes(context) <= policy.readBytes && bytes({ ...payload, context: [...payload.context, context] }) <= policy.payloadBytes) payload.context.push(context);
    }
    const snapshot: Snapshot = deepFreeze(validate(SnapshotSchema, { identity: { repo, gitCommonDir: commonDir, objectFormat, intendedBaseRef: request.baseRef, intendedHeadRef: request.headRef, base, head, mergeBase, baseTree, headTree, mergeBaseTree, surfaceDigest: hash(payload) }, payload, omissions, payloadBytes: bytes(payload) }));
    const readSource = (revision: Revision, path: string): string => {
      if (!safePath(path) || !trees[revision].has(path) || !sources[revision].has(path)) throw new SnapshotError('Path is not readable filtered pinned text', omissions.filter(item => item.revision === revision && item.path === path));
      return sources[revision].get(path)!;
    };
    const tools = Object.freeze({
      read_git(revision: Revision, path: string, start: number, end: number) {
        validate(ReadSchema, { revision, path, start, end });
        if (end < start || end - start + 1 > policy.readLines) throw new SnapshotError('Read line bound exceeded');
        const source = readSource(revision, path).split('\n');
        if (end > source.length) throw new SnapshotError('Read extends beyond pinned text');
        const result = { revision, path, start, end, text: source.slice(start - 1, end).join('\n') };
        if (bytes(result) > policy.readBytes) throw new SnapshotError('Read byte bound exceeded');
        return result;
      },
      search_git(revision: Revision, literal: string, pathPrefix: string) {
        validate(SearchSchema, { revision, literal, pathPrefix });
        const prefix = pathPrefix.endsWith('/') ? pathPrefix.slice(0, -1) : pathPrefix;
        if (pathPrefix === '/' || (prefix && !safePath(prefix)) || /[\x00-\x1f\x7f]/.test(literal)) throw new SnapshotError('Unsafe search arguments');
        const hits: { path: string; line: number; text: string }[] = [];
        const excludedFiles = omissions.filter(item => item.revision === revision && (!prefix || item.path === prefix || item.path.startsWith(`${prefix}/`))).length;
        if (bytes({ hits, truncated: true, excludedFiles }) > policy.searchBytes) throw new SnapshotError('Search byte bound too small for result');
        for (const [path, source] of sources[revision]) {
          if (prefix && path !== prefix && !path.startsWith(`${prefix}/`)) continue;
          for (const [index, line] of source.split('\n').entries()) {
            if (!line.includes(literal)) continue;
            const hit = { path, line: index + 1, text: line };
            if (hits.length >= policy.searchHits || bytes({ hits: [...hits, hit], truncated: false, excludedFiles }) > policy.searchBytes) return { hits, truncated: true, excludedFiles };
            hits.push(hit);
          }
        }
        return { hits, truncated: false, excludedFiles };
      },
    });
    const validateFinding = (inputFinding: unknown): Finding => {
      const candidate = validate(FindingSchema, inputFinding);
      return validateFindingEvidence(candidate, readSource(candidate.revision, candidate.path), spans[candidate.revision].get(candidate.path) ?? []);
    };
    // Recheck source/index against original pinned HEAD after capture, not moving refs.
    const currentIndex = await readFile(index);
    if (!currentIndex.equals(await readFile(join(isolated, 'index')))) {
      // status may refresh copied stat info; compare semantic stages instead of raw bytes.
      const refreshed = join(isolated, 'fresh-index'); await writeFile(refreshed, currentIndex, { mode: 0o600 });
      const before = await run(['ls-files', '--stage', '-z']);
      const after = await git(repo, ['ls-files', '--stage', '-z'], policy, { ...environment, GIT_INDEX_FILE: refreshed });
      const currentFlags = nul(utf8(await git(repo, ['ls-files', '-v', '-z'], policy, { ...environment, GIT_INDEX_FILE: refreshed })));
      if (!before.equals(after) || currentFlags.some(entry => !entry.startsWith('H '))) throw new SnapshotError('Index changed during capture', [], 21);
    }
    if ((await run(['status', '--porcelain=v1', '-z', '--untracked-files=all', '--ignore-submodules=all'])).length) throw new SnapshotError('Source changed during capture', [], 21);
    checkDeadline();
    return { snapshot, tools, validateFinding };
  } finally { await rm(isolated, { recursive: true, force: true }); }
}
