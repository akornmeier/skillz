import { afterEach, describe, expect, it, vi } from 'vitest';
import { access, mkdtemp, readFile, realpath, rm, stat, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { DEFAULT_POLICY, ReviewError, hash, sealReport, validateAttempt, validateReport, type Finding, type ReviewReport } from '../src/contracts.js';
import { MODEL, type FixtureTransport, type Lens, type RuntimeEvent } from '../src/runtime.js';
import { implementationIdentity, ownAttempt, review, verify } from '../src/review.js';
import { cli } from '../src/cli.js';
import { commit, fixtureGit, gitFixture, put } from './git-fixture.js';

vi.mock('node:fs/promises', async importOriginal => {
  const original = await importOriginal<typeof import('node:fs/promises')>();
  return { ...original, readFile: vi.fn(original.readFile) };
});

const roots: string[] = [];
afterEach(async () => { await Promise.all(roots.splice(0).map(root => rm(root, { recursive: true, force: true }))); });
const output = (findings: Finding[] = []) => JSON.stringify({ findings, checkedPaths: ['src/a.ts'], omissions: [], requiredUnavailable: [] });
function fixtures(onEvent?: FixtureTransport['onEvent'], findings: Finding[] = []): Record<Lens, FixtureTransport> {
  const fixture = (lens: Lens): FixtureTransport => ({ kind: 'fixture', steps: [{ text: output(findings.map(finding => ({ ...finding, lens }))) }], ...(onEvent ? { onEvent } : {}) });
  return { correctness: fixture('correctness'), 'contracts-risk': fixture('contracts-risk') };
}
async function setup() {
  const { repo } = await gitFixture(); roots.push(repo);
  await put(repo, 'src/a.ts', 'export const enabled = false;\n'); await commit(repo);
  const root = await mkdtemp(join(await realpath(tmpdir()), 'file-pr-state-')); roots.push(root);
  const request = { repo, baseRef: 'base', headRef: 'HEAD', goal: 'Check changed toggle', builderModel: 'openai/gpt-6', attemptId: 'review-test', policy: { ...DEFAULT_POLICY } };
  return { root, request, current: { repo, baseRef: 'base', headRef: 'HEAD' } };
}
function finding(lens: Lens = 'correctness'): Finding {
  return { id: 'toggle', lens, severity: 'P2', path: 'src/a.ts', revision: 'head', start: 1, end: 1, quote: 'export const enabled = false;', cause: 'Toggle disables required behavior', trigger: 'Caller enables feature', impact: 'Feature remains disabled', classification: 'introduced', uncertainty: null };
}
function triage(report: ReviewReport) {
  return { schemaVersion: 1, reportId: report.body.reportId, attemptId: report.body.attemptId, identityDigest: report.receipt.identityDigest,
    dispositions: Object.values(report.body.lenses).flatMap(lens => lens.findings.map(finding => ({ findingId: finding.id, status: 'dismissed', evidence: [{ kind: 'source', reference: `${report.body.identity.snapshot.head}:src/a.ts:1`, observation: 'Disabled toggle is required by approved goal' }] }))) };
}
async function code(promise: Promise<unknown>, expected: number, message?: string) {
  try { await promise; throw new Error('Expected rejection'); } catch (error) { expect(error).toBeInstanceOf(ReviewError); expect((error as ReviewError).code).toBe(expected); if (message) expect((error as Error).message).toContain(message); }
}
describe('offline parallel review, attempt ledger and current-source receipt', () => {
  it('lockfile-only dependency changes invalidate runtime qualification identity', async () => {
    const initial = await implementationIdentity();
    const original = await vi.importActual<typeof import('node:fs/promises')>('node:fs/promises');
    vi.mocked(readFile).mockImplementation(async (...args) => String(args[0]).endsWith('/pnpm-lock.yaml')
      ? Buffer.from('synthetic changed dependency graph') : original.readFile(...args));
    try {
      const changed = await implementationIdentity();
      expect(changed.lockHash).not.toBe(initial.lockHash);
      expect(changed.runtimeHash).not.toBe(initial.runtimeHash);
    } finally { vi.mocked(readFile).mockImplementation(original.readFile); }
  });
  it('barrier proves lenses overlap, independent fresh context, no extra judge calls', async () => {
    const { root, request } = await setup(); const events: RuntimeEvent[] = []; let release!: () => void;
    const barrier = new Promise<void>(resolve => { release = resolve; }); let arrived = 0;
    const result = await review(request, root, fixtures(async event => {
      events.push(event); if (event.kind === 'request') { if (++arrived === 2) release(); await barrier; }
    }));
    expect(result.exit).toBe(0); expect(arrived).toBe(2); expect(new Set(events.filter(event => event.kind === 'request').map(event => event.pid)).size).toBe(2);
    for (const event of events.filter(event => event.kind === 'request')) {
      const text = JSON.stringify(event.data); expect(text).toContain(`Lens: ${event.lens}`); expect(text).not.toContain('builder reasoning');
    }
    expect(events.filter(event => event.kind === 'effect')).toHaveLength(2); expect(result.report.body.execution?.mode).toBe('simulated');
    expect(Object.values(result.report.body.lenses).every(lens => lens.identities?.[0]?.returned === MODEL.returned)).toBe(true);
  });
  it('publishes private minimized atomic JSON and Markdown, retains both identities/usage', async () => {
    const { root, request } = await setup(); const result = await review(request, root, fixtures());
    expect((await stat(root)).mode & 0o777).toBe(0o700);
    for (const path of Object.values(result.paths)) expect((await stat(path)).mode & 0o777).toBe(0o600);
    expect(validateReport(JSON.parse(await readFile(result.paths.json, 'utf8')))).toEqual(result.report);
    const markdown = await readFile(result.paths.markdown, 'utf8'); expect(markdown).toContain('SIMULATED'); expect(markdown).toContain('Not push authorization');
    expect(await readFile(result.paths.json, 'utf8')).not.toContain('full transcript');
  });
  it('same completed identity reuses exact report with zero new effects', async () => {
    const { root, request } = await setup(); const first = await review(request, root, fixtures());
    const second = await review(request, root, fixtures(() => { throw new Error('Must not dispatch'); }));
    expect(second.reused).toBe(true); expect(second.report).toEqual(first.report);
  });
  it('quote rejection is incomplete, never zero-finding pass or same-identity rerun', async () => {
    const { root, request } = await setup(); const bad = finding(); bad.quote = 'invented quote';
    const result = await review(request, root, fixtures(undefined, [bad]));
    expect(result.exit).toBe(20); expect(result.report.body.status).toBe('incomplete');
    await code(review(request, root, fixtures()), 20);
  });
  it('deduplicates same location/cause while preserving both lens allegations and provenance', async () => {
    const { root, request } = await setup(); const result = await review(request, root, fixtures(undefined, [finding()]));
    expect(result.exit).toBe(10); expect(result.report.body.execution?.provenance).toHaveLength(1);
    expect(result.report.body.execution?.provenance[0]?.findingIds).toHaveLength(2);
    expect(result.report.body.lenses.correctness.findings[0]?.id).not.toBe(result.report.body.lenses['contracts-risk'].findings[0]?.id);
  });
  it('rejects unanchored correct quote from unchanged source', async () => {
    const { root, request } = await setup(); const bad = { ...finding(), path: 'src/a.test.ts', quote: 'export const test = "valid behavior";' };
    const result = await review(request, root, fixtures(undefined, [bad])); expect(result.exit).toBe(20);
  });
  it('records unavailable required context, never treats it as clean', async () => {
    const { root, request } = await setup(); const fake = fixtures(); fake.correctness.steps = [{ text: JSON.stringify({ findings: [], checkedPaths: ['src/a.ts'], omissions: [], requiredUnavailable: ['Caller schema excluded'] }) }];
    const result = await review(request, root, fake); expect(result.exit).toBe(20);
    expect(result.report.body.lenses.correctness.contextGaps).toEqual(['Caller schema excluded']);
  });
  it('missing usage blocks automatic rerun even at a different head', async () => {
    const { root, request } = await setup(); const fake = fixtures(); fake.correctness.steps = [{ text: output(), missingUsage: true }];
    const result = await review(request, root, fake); expect(result.exit).toBe(20);
    await put(request.repo, 'src/a.ts', 'export const enabled = 2;\n'); await commit(request.repo);
    await code(review(request, root, fixtures()), 20, 'Interrupted/uncertain');
  });
  it('unchecked changed path prevents complete coverage', async () => {
    const { root, request } = await setup(); await put(request.repo, 'src/other.ts', 'export const other = 1;\n'); await commit(request.repo);
    const result = await review(request, root, fixtures()); expect(result.exit).toBe(20);
  });
  it('exclusive attempt lock collides before effects; does not auto-reclaim stale locks', async () => {
    const { root, request } = await setup(); const held = await ownAttempt(root, request.attemptId);
    try { await code(review(request, root, fixtures(() => { throw new Error('No dispatch'); })), 20, 'locked'); }
    finally { await held.close(); }
    const lockPath = join(root, `${request.attemptId}.lock`); await writeFile(lockPath, 'dead owner', { mode: 0o600 });
    await code(review(request, root, fixtures()), 20, 'locked'); await access(lockPath);
  });
  it('crash after durable round reservation cannot auto-resume', async () => {
    const { root, request } = await setup(); const held = await ownAttempt(root, request.attemptId); await held.begin(hash('crash-before-report')); await held.close();
    await code(review(request, root, fixtures()), 20, 'Interrupted/uncertain');
  });
  it('transport crash records uncertain reservation and prevents rerun under changed head', async () => {
    const { root, request } = await setup(); const fake = fixtures(); fake.correctness.steps = [{ crash: true }];
    const result = await review(request, root, fake); expect(result.exit).toBe(20);
    const ledger = validateAttempt(JSON.parse(await readFile(join(root, `${request.attemptId}.attempt.json`), 'utf8')));
    expect(ledger.reservations.some(item => item.state === 'uncertain')).toBe(true); expect(ledger.rounds[0]?.status).toBe('uncertain');
    await put(request.repo, 'src/a.ts', 'export const enabled = 2;\n'); await commit(request.repo);
    await code(review(request, root, fixtures()), 20, 'Interrupted/uncertain');
  });
  it('two full-diff rounds reserve at most twelve requests, then stop', async () => {
    const { root, request } = await setup(); const events: RuntimeEvent[] = [];
    const fake = fixtures(event => { events.push(event); });
    for (const fixture of Object.values(fake)) fixture.steps = [{ calls: [{ name: 'read_git', args: { revision: 'head', path: 'src/a.ts', start: 1, end: 1 } }] }, { calls: [{ name: 'search_git', args: { revision: 'head', literal: 'enabled', pathPrefix: 'src' } }] }, { text: output() }];
    expect((await review(request, root, fake)).exit).toBe(0);
    await put(request.repo, 'src/fix.ts', 'export const fix = 1;\n'); await commit(request.repo);
    for (const fixture of Object.values(fake)) fixture.steps = [...fixture.steps.slice(0, 2), { text: JSON.stringify({ findings: [], checkedPaths: ['src/a.ts', 'src/fix.ts'], omissions: [], requiredUnavailable: [] }) }];
    const second = await review(request, root, fake); expect(second.report.body.round).toBe(2); expect(second.exit).toBe(0);
    const payload = JSON.stringify(events.filter(event => event.kind === 'request').at(-1)?.data);
    expect(payload).toContain('src/a.ts'); expect(payload).toContain('src/fix.ts');
    expect(events.filter(event => event.kind === 'effect')).toHaveLength(12);
    await put(request.repo, 'src/fix.ts', 'export const fix = 2;\n'); await commit(request.repo);
    await code(review(request, root, fake), 20, 'Two-round');
    expect(events.filter(event => event.kind === 'effect')).toHaveLength(12);
  });
  it('rejects stale HEAD and dirty tracked/untracked input using actual capture', async () => {
    const { root, request, current } = await setup(); const { report } = await review(request, root, fixtures());
    await put(request.repo, 'src/a.ts', 'export const enabled = 2;\n');
    await code(verify(report, triage(report), current), 21, 'Dirty');
    await commit(request.repo); await code(verify(report, triage(report), current), 21, 'Stale');
    await put(request.repo, 'untracked.ts', 'new source\n'); await code(verify(report, triage(report), current), 21, 'Dirty');
  });
  it('rechecks moving intended base ref, not supplied pinned report IDs', async () => {
    const { root, request, current } = await setup(); const { report } = await review(request, root, fixtures());
    await fixtureGit(request.repo, 'branch', '-f', 'base', 'HEAD');
    await code(verify(report, triage(report), current), 21, 'Current source');
  });
  it('rejects changed runtime source by recapturing actual hashes', async () => {
    const { root, request, current } = await setup(); const { report } = await review(request, root, fixtures());
    const runtimePath = new URL('../src/runtime-child.ts', import.meta.url); const original = await readFile(runtimePath, 'utf8');
    try { await writeFile(runtimePath, `${original}\n// Synthetic runtime drift verification\n`); await code(verify(report, triage(report), current), 21, 'Stale'); }
    finally { await writeFile(runtimePath, original); }
  });
  it('does not trust supplied prompt/policy identities, even re-sealed report', async () => {
    const { root, request, current } = await setup(); const { report } = await review(request, root, fixtures());
    for (const change of ['prompt', 'policy'] as const) {
      const body = structuredClone(report.body);
      if (change === 'prompt') body.identity.promptHash = hash('pretend prompt'); else body.identity.policy.requestsPerLens = 1;
      await code(verify(sealReport(body), triage(sealReport(body)), current), 21, 'Stale');
    }
  });
  it('checks actual candidate evidence and all triage dispositions before simulated denial', async () => {
    const { root, request, current } = await setup(); const { report } = await review(request, root, fixtures(undefined, [finding()]));
    const valid = triage(report);
    await code(verify(report, { ...valid, dispositions: [] }, current), 20, 'Missing');
    await code(verify(report, { ...valid, dispositions: valid.dispositions.map(item => ({ ...item, evidence: [] })) }, current), 20, 'Invalid');
    await code(verify(report, { ...valid, dispositions: valid.dispositions.map(item => ({ findingId: item.findingId, status: 'unresolved', reason: 'Still open', evidence: item.evidence })) }, current), 20, 'Unresolved');
    await code(verify(report, { ...valid, dispositions: valid.dispositions.map(item => ({ ...item, status: 'fixed', commit: report.body.identity.snapshot.head })) }, current), 21, 'new full-diff');
    await code(verify(report, valid, current), 30, 'Simulated evidence');
  });
  it('incomplete and unavailable transports never authorize', async () => {
    const { root, request, current } = await setup(); const result = await review(request, root);
    expect(result.exit).toBe(30); expect(result.report.body.status).toBe('setup-error');
    await code(verify(result.report, triage(result.report), current), 20, 'Incomplete');
  });
  it('CLI help/dry-run JSON and exit meanings are offline safe; rejects raw diagnostics', async () => {
    const { request } = await setup(); const help = await cli(['--help']); expect(help.exit).toBe(0); expect(JSON.stringify(help.output)).toContain('30');
    const dry = await cli(['review', '--repo', request.repo, '--base', 'base', '--head', 'HEAD', '--goal', request.goal, '--builder-model', request.builderModel, '--attempt', request.attemptId, '--dry-run']);
    expect(dry.exit).toBe(0); expect(dry.output).toMatchObject({ dryRun: true, authorization: false, live: false });
    const bad = await cli(['review', '--secret-key', 'DO_NOT_PRINT']); expect(bad.exit).toBe(30); expect(JSON.stringify(bad)).not.toContain('DO_NOT_PRINT');
    const verifyDry = await cli(['verify', '--report', '/not/read', '--triage', '/not/read', '--repo', request.repo, '--base', 'base', '--head', 'HEAD', '--dry-run']); expect(verifyDry.exit).toBe(0);
  });
});
