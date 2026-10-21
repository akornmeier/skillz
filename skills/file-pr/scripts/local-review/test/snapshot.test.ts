import { chmod, lstat, readFile, rm, symlink, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { deflateSync } from 'node:zlib';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { hash, reportExit, ReviewError, sealReport, validateReport } from '../src/contracts.js';
import { captureSnapshot, containsSecret, SnapshotError } from '../src/snapshot.js';
import { body, finding, request } from './fixtures.js';
import { commit, fixtureGit, gitFixture, put } from './git-fixture.js';

const roots: string[] = [];
async function repo(files?: Record<string, string>) { const fixture = await gitFixture(files); roots.push(fixture.repo); return fixture; }
async function changed(files?: Record<string, string>) {
  const fixture = await repo(files);
  await put(fixture.repo, 'src/a.ts', 'export const enabled = false;\n');
  const head = await commit(fixture.repo);
  return { ...fixture, head };
}
afterEach(async () => { vi.unstubAllEnvs(); await Promise.all(roots.splice(0).map(path => rm(path, { recursive: true, force: true }))); });

describe('real synthetic Git snapshot and pinned evidence', () => {
  it('captures exact identity, complete patch/surroundings, relevant tests and exactly two bounded tools', async () => {
    const { repo: path, base, head } = await changed();
    const { snapshot, tools } = await captureSnapshot(request(path));
    expect(snapshot.identity).toMatchObject({ repo: path, base, head, mergeBase: base, intendedBaseRef: 'base' });
    expect(snapshot.identity.baseTree).toBe(await fixtureGit(path, 'rev-parse', 'base^{tree}'));
    expect(snapshot.identity.headTree).toBe(await fixtureGit(path, 'rev-parse', 'HEAD^{tree}'));
    expect(snapshot.identity.surfaceDigest).toBe(hash(snapshot.payload));
    expect(snapshot.payloadBytes).toBe(Buffer.byteLength(JSON.stringify(snapshot.payload)));
    expect(snapshot.payload.diff[0]?.patch).toContain('-export const enabled = true;\n+export const enabled = false;');
    expect(snapshot.payload.context).toContainEqual({ path: 'src/a.test.ts', revision: 'head', text: 'export const test = "valid behavior";\n' });
    expect(Object.keys(tools)).toEqual(['read_git', 'search_git']);
    expect(tools.read_git('base', 'src/a.ts', 1, 1).text).toBe('export const enabled = true;');
    expect(tools.search_git('head', 'false', 'src').hits).toEqual([{ path: 'src/a.ts', line: 1, text: 'export const enabled = false;' }]);
    expect(Object.isFrozen(snapshot.identity)).toBe(true);
  });

  it('integrates real source evidence, P2 report, omissions and exact receipt freshness', async () => {
    const { repo: path, base } = await changed({ 'src/a.ts': 'export const enabled = true;\n', '.env': 'private source, never exported\n' });
    const captured = await captureSnapshot(request(path));
    const reportBody = body();
    reportBody.identity.snapshot = captured.snapshot.identity;
    reportBody.omissions = captured.snapshot.omissions;
    reportBody.lenses.correctness.findings = [captured.validateFinding({ ...finding(), path: 'src/a.ts', start: 1, end: 1, quote: 'export const enabled = false;' })];
    const receipt = sealReport(reportBody);
    expect(reportExit(receipt)).toBe(10);
    expect(validateReport(receipt, reportBody.identity)).toEqual(receipt);
    expect(captured.tools.search_git('head', 'private source', '').excludedFiles).toBe(1);
    await fixtureGit(path, 'branch', 'other-base', base);
    const newSnapshot = await captureSnapshot({ ...request(path), baseRef: 'other-base' });
    expect(() => validateReport(receipt, { ...reportBody.identity, snapshot: newSnapshot.snapshot.identity })).toThrow('Stale');
  });

  it('computes merge-base…head rather than base tip; moving refs/checkout cannot alter captured tools', async () => {
    const { repo: path, base } = await changed();
    const capturedHead = await fixtureGit(path, 'rev-parse', 'HEAD');
    await fixtureGit(path, 'checkout', '--quiet', 'base');
    await put(path, 'base-only.ts', 'export const baseOnly = 1;\n');
    const baseTip = await commit(path);
    await fixtureGit(path, 'checkout', '--quiet', 'feature');
    const captured = await captureSnapshot(request(path));
    expect(captured.snapshot.identity).toMatchObject({ base: baseTip, head: capturedHead, mergeBase: base });
    expect(captured.snapshot.payload.inventory.map(change => change.path)).not.toContain('base-only.ts');
    expect(() => captured.tools.read_git('base', 'base-only.ts', 1, 1)).toThrow();
    await fixtureGit(path, 'branch', '--force', 'base', capturedHead);
    await put(path, 'src/a.ts', 'host mutation\n');
    await commit(path);
    expect(captured.tools.read_git('head', 'src/a.ts', 1, 1).text).toBe('export const enabled = false;');
    expect(captured.tools.read_git('base', 'src/a.ts', 1, 1).text).toBe('export const enabled = true;');
  });

  it.each(['tracked', 'untracked', 'staged', 'assume-unchanged', 'skip-worktree'] as const)('rejects %s input before a dispatch boundary can run', async kind => {
    const { repo: path } = await changed();
    if (kind === 'untracked') await put(path, 'private-untracked.ts', 'never export\n');
    else {
      await put(path, 'src/a.ts', 'dirty\n');
      if (kind === 'staged') await fixtureGit(path, 'add', '--all');
      if (kind === 'assume-unchanged') await fixtureGit(path, 'update-index', '--assume-unchanged', 'src/a.ts');
      if (kind === 'skip-worktree') await fixtureGit(path, 'update-index', '--skip-worktree', 'src/a.ts');
    }
    let dispatches = 0;
    try { await captureSnapshot(request(path)); dispatches++; } catch (error) { expect(error).toBeInstanceOf(ReviewError); expect((error as ReviewError).code).toBe(21); }
    expect(dispatches).toBe(0);
  });

  it('handles rename, deletion, mode-only changes, spaces and option-like names with NUL inventory', async () => {
    const { repo: path } = await repo({ 'old name.ts': 'export const a = 1;\n'.repeat(10), 'delete.ts': 'gone\n', 'mode.ts': 'mode\n', '--output=escape.ts': 'before\n' });
    await fixtureGit(path, 'mv', '--', 'old name.ts', 'new name.ts');
    await fixtureGit(path, 'rm', '--', 'delete.ts');
    await chmod(join(path, 'mode.ts'), 0o755);
    await put(path, '--output=escape.ts', 'after\n');
    await commit(path);
    const { snapshot, tools } = await captureSnapshot(request(path));
    expect(snapshot.payload.inventory).toEqual(expect.arrayContaining([
      expect.objectContaining({ status: 'R', oldPath: 'old name.ts', path: 'new name.ts' }),
      expect.objectContaining({ status: 'D', path: 'delete.ts' }),
      expect.objectContaining({ path: 'mode.ts', oldMode: '100644', mode: '100755' }),
    ]));
    expect(tools.read_git('head', '--output=escape.ts', 1, 1).text).toBe('after');
    expect(tools.read_git('head', 'new name.ts', 1, 1).text).toBe('export const a = 1;');
    expect(tools.read_git('base', 'delete.ts', 1, 1).text).toBe('gone');
    expect(() => tools.read_git('head', 'delete.ts', 1, 1)).toThrow();
    expect(snapshot.payload.diff.find(diff => diff.path === 'mode.ts')?.patch).toContain('new mode 100755');
    expect(snapshot.payload.context).toContainEqual({ path: 'mode.ts', revision: 'head', text: 'mode\n' });
  });

  it('preserves malicious newline inventory as an explicit incomplete path; never interprets it', async () => {
    const { repo: path } = await changed();
    await put(path, 'src/evil\n--output=stolen.ts', 'source\n'); await commit(path);
    await expect(captureSnapshot(request(path))).rejects.toMatchObject({ code: 20, omissions: expect.arrayContaining([expect.objectContaining({ path: 'src/evil\n--output=stolen.ts', reason: 'unsafe path', changed: true })]) });
  });

  it('rejects missing objects and mismatched checked-out candidate without fallback or lazy fetch', async () => {
    const { repo: path, head } = await changed();
    await expect(captureSnapshot({ ...request(path), headRef: 'base' })).rejects.toMatchObject({ code: 21 });
    const blob = await fixtureGit(path, 'rev-parse', `${head}:src/a.ts`);
    await rm(join(path, '.git', 'objects', blob.slice(0, 2), blob.slice(2)));
    await fixtureGit(path, 'config', 'remote.origin.url', 'ext::false');
    await fixtureGit(path, 'config', 'remote.origin.promisor', 'true');
    await expect(captureSnapshot(request(path))).rejects.toBeInstanceOf(SnapshotError);
  });

  it('rejects corrupt blob contents even when a loose object retains the pinned filename', async () => {
    const { repo: path, head } = await changed();
    const oid = await fixtureGit(path, 'rev-parse', `${head}:src/a.ts`);
    const objectPath = join(path, '.git', 'objects', oid.slice(0, 2), oid.slice(2));
    const wrong = Buffer.from('export const enabled = wrong;\n');
    await chmod(objectPath, 0o600);
    await writeFile(objectPath, deflateSync(Buffer.concat([Buffer.from(`blob ${wrong.length}\0`), wrong])));
    await expect(captureSnapshot(request(path))).rejects.toThrow('blob identity mismatch');
  });

  it('supports real SHA-256 object repositories without mismatched identity lengths', async () => {
    const fixture = await gitFixture({ 'a.ts': 'before\n' }, 'sha256'); roots.push(fixture.repo);
    await put(fixture.repo, 'a.ts', 'after\n'); await commit(fixture.repo);
    const { snapshot } = await captureSnapshot(request(fixture.repo));
    expect(snapshot.identity.objectFormat).toBe('sha256');
    expect(snapshot.identity.head).toHaveLength(64);
    const reportBody = body(); reportBody.identity.snapshot = snapshot.identity;
    expect(reportExit(sealReport(reportBody))).toBe(0);
  });

  it('validates quotes against pinned changed head lines and explicit base-side deleted lines', async () => {
    const { repo: path } = await changed();
    const captured = await captureSnapshot(request(path));
    const candidate = { ...finding(), path: 'src/a.ts', start: 1, end: 1, quote: 'export const enabled = false;' };
    expect(captured.validateFinding(candidate)).toEqual(candidate);
    expect(captured.validateFinding({ ...candidate, revision: 'base', quote: 'export const enabled = true;' }).revision).toBe('base');
    expect(() => captured.validateFinding({ ...candidate, quote: 'forged' })).toThrow();
    expect(() => captured.validateFinding({ ...candidate, path: 'src/a.test.ts', quote: 'export const test = "valid behavior";' })).toThrow();
  });
});

describe('same exclusions across initial context, reads, searches and evidence', () => {
  it.each([
    ['.env.production', 'PASSWORD=synthetic-private-value\n', 'private'],
    ['src/key.ts', 'export const token = "sk-ant-abcdefghijklmnopqrstuvwxyz012345";\n', 'secret'],
    ['src/binary.ts', 'a\0b', 'binary'],
    ['src/lfs.ts', 'version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 100\n', 'LFS'],
    ['src/api.ts', '// Code generated by synthetic generator. DO NOT EDIT.\nexport const api = 1;\n', 'generated'],
    ['generated/api.ts', 'export const generated = true;\n', 'generated'],
    ['vendor/lib.ts', 'export const vendor = true;\n', 'vendor'],
    ['notes.csv', 'private,data\n', 'private'],
  ])('changed %s is incomplete with explicit reason', async (name, text, reason) => {
    const { repo: path } = await changed(); await put(path, name, text); await commit(path);
    await expect(captureSnapshot(request(path))).rejects.toMatchObject({ code: 20, omissions: expect.arrayContaining([expect.objectContaining({ path: name, reason: expect.stringContaining(reason), semantic: true })]) });
  });

  it('never exposes unchanged denied blobs in transport, read/search or findings', async () => {
    const secret = 'sk-ant-abcdefghijklmnopqrstuvwxyz012345';
    const { repo: path } = await changed({ 'src/a.ts': 'old\n', 'src/a.test.ts': 'test\n', 'src/secret.ts': `const credential = '${secret}';\n`, '.env': 'private\n', 'vendor/private.ts': 'const needle = 1;\n' });
    const captured = await captureSnapshot(request(path));
    expect(JSON.stringify(captured.snapshot.payload)).not.toContain(secret);
    for (const name of ['src/secret.ts', '.env', 'vendor/private.ts']) {
      expect(() => captured.tools.read_git('head', name, 1, 1)).toThrow();
      expect(() => captured.validateFinding({ ...finding(), path: name, start: 1, end: 1, quote: 'irrelevant' })).toThrow();
    }
    expect(captured.tools.search_git('head', secret, '').hits).toEqual([]);
    expect(captured.tools.search_git('base', 'needle', '').hits).toEqual([]);
  });

  it('never follows a committed symlink or submodule contents; changed unsupported modes are incomplete', async () => {
    const { repo: path, base } = await changed();
    await symlink('/definitely-private-host-file', join(path, 'linked.ts'));
    await commit(path);
    await expect(captureSnapshot(request(path))).rejects.toMatchObject({ omissions: expect.arrayContaining([expect.objectContaining({ path: 'linked.ts', reason: 'symlink object' })]) });
    await fixtureGit(path, 'rm', '--', 'linked.ts'); await commit(path);
    await fixtureGit(path, 'update-index', '--add', '--cacheinfo', `160000,${base},nested`);
    await fixtureGit(path, 'commit', '--quiet', '-m', 'synthetic gitlink');
    await expect(captureSnapshot(request(path))).rejects.toMatchObject({ omissions: expect.arrayContaining([expect.objectContaining({ path: 'nested', reason: 'submodule or unsupported mode' })]) });
  });

  it('rejects root lockfile without its own manifest despite nested manifest coverage', async () => {
    const { repo: path } = await repo({ 'a/package.json': '{}\n', 'a/pnpm-lock.yaml': 'old\n', 'yarn.lock': 'old\n' });
    await put(path, 'a/pnpm-lock.yaml', 'new\n');
    await put(path, 'yarn.lock', 'new\n');
    await commit(path);
    await expect(captureSnapshot(request(path))).rejects.toThrow('manifest context');
  });

  it('requires ecosystem-matching manifest rather than unrelated package metadata', async () => {
    const { repo: path } = await repo({ 'package.json': '{}\n', 'Cargo.lock': 'old\n' });
    await put(path, 'Cargo.lock', 'new\n');
    await commit(path);
    await expect(captureSnapshot(request(path))).rejects.toThrow('manifest context');
  });

  it('includes distinct matching manifest context for each changed lockfile', async () => {
    const { repo: path } = await repo({ 'package.json': '{}\n', 'yarn.lock': 'old\n', 'a/Cargo.toml': '[package]\n', 'a/Cargo.lock': 'old\n' });
    await put(path, 'yarn.lock', 'new\n');
    await put(path, 'a/Cargo.lock', 'new\n');
    await commit(path);
    const captured = await captureSnapshot(request(path));
    expect(captured.snapshot.payload.context.map(item => item.path)).toEqual(expect.arrayContaining(['package.json', 'a/Cargo.toml']));
  });

  it('keeps changed lock summaries and manifest context, never lock payload', async () => {
    const { repo: path } = await repo({ 'package.json': '{"name":"synthetic"}\n', 'pnpm-lock.yaml': 'old-lock-payload\n' });
    await put(path, 'pnpm-lock.yaml', 'new-lock-payload\n'); await commit(path);
    const captured = await captureSnapshot(request(path));
    expect(captured.snapshot.payload.inventory[0]?.summary).toContain('Lock payload excluded');
    expect(captured.snapshot.payload.context).toContainEqual({ path: 'package.json', revision: 'head', text: '{"name":"synthetic"}\n' });
    expect(JSON.stringify(captured.snapshot.payload)).not.toContain('new-lock-payload');
    expect(captured.snapshot.payload.omissions.every(item => !item.semantic)).toBe(true);
    expect(() => captured.tools.read_git('head', 'pnpm-lock.yaml', 1, 1)).toThrow();
    expect(captured.tools.search_git('head', 'lock-payload', '').hits).toEqual([]);
  });

  it('rejects staged gitlink changes without inspecting submodule checkout contents', async () => {
    const { repo: path, base } = await changed();
    await fixtureGit(path, 'update-index', '--add', '--cacheinfo', `160000,${base},nested`);
    await expect(captureSnapshot(request(path))).rejects.toMatchObject({ code: 21 });
  });

  it('secret detector covers common credentials and does not claim exhaustive export protection', () => {
    for (const sample of ['-----BEGIN PRIVATE KEY-----', 'ghp_abcdefghijklmnopqrstuvwxyz', 'api_key="abcdefghijklmnop"', 'https://user:password@host.invalid']) expect(containsSecret(sample)).toBe(true);
    expect(containsSecret('export const enabled = true;')).toBe(false);
  });
});

describe('actual pre-dispatch bounds and command isolation', () => {
  it('does not run repository filters, external diff, textconv, fsmonitor, hooks or inherited Git environment', async () => {
    const { repo: path } = await changed();
    const sentinel = join(path, '.git', 'EXECUTED');
    const script = join(path, '.git', 'evil.sh');
    await writeFile(script, `#!/bin/sh\nprintf compromised > '${sentinel}'\nexit 1\n`, { mode: 0o755 });
    await put(path, '.gitattributes', '*.ts diff=evil filter=evil\n');
    await commit(path, 'attributes');
    // Arm adversarial config only after fixture setup has finished.
    for (const [key, value] of [['diff.external', script], ['diff.evil.textconv', script], ['filter.evil.clean', script], ['filter.evil.process', script], ['core.fsmonitor', script], ['core.hooksPath', join(path, '.git')]] as const) await fixtureGit(path, 'config', key, value);
    // Force stat refresh: a normal status would invoke clean filter.
    const source = await readFile(join(path, 'src/a.ts')); await writeFile(join(path, 'src/a.ts'), source);
    vi.stubEnv('GIT_EXTERNAL_DIFF', script); vi.stubEnv('GIT_CONFIG_COUNT', '1'); vi.stubEnv('GIT_CONFIG_KEY_0', 'core.fsmonitor'); vi.stubEnv('GIT_CONFIG_VALUE_0', script);
    await captureSnapshot(request(path));
    await expect(lstat(sentinel)).rejects.toMatchObject({ code: 'ENOENT' });
  });

  it('rejects >60 changed files and complete diff >128KiB, not sliced payloads', async () => {
    const { repo: path } = await repo();
    for (let i = 0; i < 61; i++) await put(path, `src/f-${i}.ts`, `export const n = ${i};\n`);
    await commit(path);
    await expect(captureSnapshot(request(path))).rejects.toThrow('Changed-file limit');
    const other = await repo({ 'a.ts': 'a'.repeat(70_000) + '\n' });
    await put(other.repo, 'a.ts', 'b'.repeat(70_000) + '\n'); await commit(other.repo);
    await expect(captureSnapshot(request(other.repo))).rejects.toThrow('Full diff byte limit');
  });

  it('forces complete text diff even when attributes mark semantic source binary', async () => {
    const { repo: path } = await repo({ '.gitattributes': '*.ts -diff\n', 'a.ts': 'before\n' });
    await put(path, 'a.ts', 'after\n'); await commit(path);
    const { snapshot } = await captureSnapshot(request(path));
    expect(snapshot.payload.diff[0]?.patch).toContain('-before\n+after');
  });

  it('counts serialized UTF-8 request bytes including inventory/context and rejects oversized blobs', async () => {
    const { repo: path } = await repo({ 'a.ts': 'é'.repeat(9000) + '\n' });
    await put(path, 'a.ts', '界'.repeat(9000) + '\n'); await commit(path);
    await expect(captureSnapshot(request(path))).rejects.toThrow('request payload limit');
    const other = await changed(); await put(other.repo, 'huge.ts', 'x'.repeat(131_073)); await commit(other.repo);
    await expect(captureSnapshot(request(other.repo))).rejects.toMatchObject({ omissions: expect.arrayContaining([expect.objectContaining({ path: 'huge.ts', reason: 'blob byte limit' })]) });
  });

  it('bounds reads/search by lines, UTF-8 bytes, hits and paths; never silently slices a read', async () => {
    const { repo: path } = await changed({ 'src/a.ts': 'before\n', 'src/many.ts': 'needle\n'.repeat(201), 'src/long.ts': '界'.repeat(3000) + '\n', 'src-other/test.ts': 'needle\n' });
    const { tools } = await captureSnapshot(request(path));
    expect(() => tools.read_git('head', 'src/many.ts', 1, 201)).toThrow('line bound');
    expect(() => tools.read_git('head', 'src/long.ts', 1, 1)).toThrow('byte bound');
    expect(() => tools.read_git('head', 'src/a.ts', 2, 1)).toThrow();
    expect(() => tools.read_git('head', '../host', 1, 1)).toThrow();
    expect(() => tools.read_git('head', '/etc/passwd', 1, 1)).toThrow();
    expect(() => tools.read_git('head', 'src/a.ts', 1, 99)).toThrow();
    const result = tools.search_git('head', 'needle', 'src');
    expect(result.hits).toHaveLength(50); expect(result.truncated).toBe(true);
    expect(result.hits.some(hit => hit.path === 'src-other/test.ts')).toBe(false);
    expect(Buffer.byteLength(JSON.stringify(result))).toBeLessThanOrEqual(8192);
    const longHit = tools.search_git('head', '界', 'src/long.ts');
    expect(longHit.hits).toEqual([]);
    expect(longHit.truncated).toBe(true);
    expect(Buffer.byteLength(JSON.stringify(longHit))).toBeLessThanOrEqual(8192);
    expect(tools.search_git('head', '.*', '').hits).toEqual([]);
    expect(() => tools.search_git('head', 'needle', '../')).toThrow();
    expect(() => tools.search_git('head', 'needle', '/')).toThrow();
  });

  it('rejects secrets in goal and unavailable checkouts before constructing source payloads', async () => {
    const { repo: path } = await changed();
    await expect(captureSnapshot({ ...request(path), goal: 'api_key=abcdefghijklmnop' })).rejects.toThrow('secret in user goal');
    await expect(captureSnapshot(request(join(path, 'missing')))).rejects.toMatchObject({ code: 30 });
  });

  it('applies smaller validated policy bounds to the actual capture/tools', async () => {
    const { repo: path } = await changed();
    await expect(captureSnapshot({ ...request(path), policy: { ...request(path).policy, payloadBytes: 10 } })).rejects.toThrow('payload limit');
    await expect(captureSnapshot({ ...request(path), policy: { ...request(path).policy, maxTreeEntries: 1 } })).rejects.toThrow('tree exceeds');
    await expect(captureSnapshot({ ...request(path), policy: { ...request(path).policy, maxScanBytes: 1 } })).rejects.toThrow('scan byte limit');
    const { tools } = await captureSnapshot({ ...request(path), policy: { ...request(path).policy, readBytes: 8, searchBytes: 8 } });
    expect(() => tools.read_git('head', 'src/a.ts', 1, 1)).toThrow('byte bound');
    expect(() => tools.search_git('head', 'enabled', '')).toThrow('Search byte bound');
  });
});
