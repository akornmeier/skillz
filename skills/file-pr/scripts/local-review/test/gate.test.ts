import { createHash } from 'node:crypto';
import { mkdtemp, readFile, realpath, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterEach, describe, expect, it } from 'vitest';
import { DEFAULT_POLICY, ReviewError, type Finding } from '../src/contracts.js';
import { review, verify } from '../src/review.js';
import type { FixtureTransport, Lens } from '../src/runtime.js';
import { fixtureBoundary } from './gate-fixture.js';
import { commit, fixtureGit, gitFixture, put } from './git-fixture.js';
import { checkFixtureReceipt, dismissedTriage, publishingFixture } from './publishing-fixture.js';

const A = 'a'.repeat(40);
const B = 'b'.repeat(40);

describe('procedural gate contract (not LLM skill qualification)', () => {
  it('routes to existing review procedure and preserves PR conventions', async () => {
    const skill = await readFile(new URL('../../../SKILL.md', import.meta.url), 'utf8');
    const workflow = await readFile(new URL('../../../workflows/local-review.md', import.meta.url), 'utf8');
    expect(skill).toContain('[local-review.md](workflows/local-review.md)');
    expect(skill).toContain('Do not invent measurements');
    expect(skill).toContain('babysit-pr');
    expect(skill).toContain('ready-for-review');
    expect(skill).toContain('model and harness attribution');
    expect(workflow.toLowerCase()).toContain('simulated evidence');
    expect(workflow).toContain('no automatic force-push');
  });

  it('preserves profiles and three original cases, freezes eight gate scenarios', async () => {
    const definitions: unknown = JSON.parse(await readFile(new URL('../../../evals/evals.json', import.meta.url), 'utf8'));
    expect(definitions).toMatchObject({ schema: 1, requiredProfiles: ['fast/economical', 'balanced/default', 'highest-reasoning'] });
    if (!definitions || typeof definitions !== 'object' || !('cases' in definitions) || !('requiredProfiles' in definitions) || !Array.isArray(definitions.cases)) throw new Error('Missing baseline cases');
    const cases: unknown[] = definitions.cases;
    const baseline = JSON.stringify({ requiredProfiles: definitions.requiredProfiles, cases: cases.slice(0, 3) });
    expect(createHash('sha256').update(baseline).digest('hex')).toBe('a24635ead3a21c5a75889bf3de9aff5896f48da3056b0eeb5be1e0e2820468a8');
    expect(definitions).toMatchObject({ cases: [
      { id: 'file-pr-existing' }, { id: 'file-pr-empty-or-unrelated-diff' }, { id: 'file-pr-repository-conventions' },
      { id: 'file-pr-finding-fix-review' }, { id: 'file-pr-false-positive' }, { id: 'file-pr-unchanged-pr' },
      { id: 'file-pr-stale-dirty' }, { id: 'file-pr-provider-unavailable' }, { id: 'file-pr-incomplete-oversized' },
      { id: 'file-pr-max-rounds' }, { id: 'file-pr-explicit-bypass' },
    ] });
  });

  it('distinguishes lookup/fetch/metadata from writes; unchanged lookup has zero reviews', () => {
    const fixture = fixtureBoundary();
    for (const kind of ['lookup', 'fetch', 'metadata'] as const) expect(fixture.record({ kind })).toBe('recorded');
    expect(fixture.log.filter(entry => entry.kind === 'review')).toHaveLength(0);
    expect(fixture.record({ kind: 'push', head: A })).toBe('denied');
    expect(fixture.record({ kind: 'pr-write', head: A })).toBe('denied');
  });

  it('requires review/fix/full review/verify before stub upload', () => {
    const fixture = fixtureBoundary();
    fixture.record({ kind: 'review', head: A, outcome: 'candidates' });
    expect(fixture.record({ kind: 'verify', head: A })).toBe('denied');
    fixture.record({ kind: 'fix', head: B });
    expect(fixture.record({ kind: 'verify', head: B })).toBe('denied');
    fixture.record({ kind: 'review', head: B, outcome: 'clean' });
    expect(fixture.record({ kind: 'push', head: B })).toBe('denied');
    expect(fixture.record({ kind: 'verify', head: B })).toBe('passed');
    expect(fixture.record({ kind: 'push', head: B })).toBe('passed');
    expect(fixture.record({ kind: 'pr-write', head: B })).toBe('passed');
    expect(fixture.log.map(entry => entry.kind)).toEqual(['review', 'verify', 'fix', 'verify', 'review', 'push', 'verify', 'push', 'pr-write']);
  });

  it('allows evidence-backed dismissal without another review', () => {
    const fixture = fixtureBoundary();
    fixture.record({ kind: 'review', head: A, outcome: 'candidates' });
    expect(fixture.record({ kind: 'dismiss', evidence: '' })).toBe('denied');
    fixture.record({ kind: 'dismiss', evidence: 'source.ts:4 guard and focused test contradict allegation' });
    expect(fixture.record({ kind: 'verify', head: A })).toBe('passed');
    expect(fixture.log.filter(entry => entry.kind === 'review')).toHaveLength(1);
  });

  it.each(['clean', 'candidates', 'incomplete', 'setup-error'] as const)('blocks stale and dirty %s results', outcome => {
    const fixture = fixtureBoundary();
    fixture.record({ kind: 'review', head: A, outcome });
    expect(fixture.record({ kind: 'verify', head: B })).toBe('denied');
    expect(fixture.record({ kind: 'verify', head: A, dirty: true })).toBe('denied');
    expect(fixture.record({ kind: 'push', head: A })).toBe('denied');
  });

  it('denies third round and cannot reuse previous verification', () => {
    const fixture = fixtureBoundary();
    fixture.record({ kind: 'review', head: A, outcome: 'clean' });
    fixture.record({ kind: 'verify', head: A });
    fixture.record({ kind: 'review', head: A, outcome: 'candidates' });
    expect(fixture.record({ kind: 'review', head: A, outcome: 'clean' })).toBe('denied');
    expect(fixture.record({ kind: 'verify', head: A })).toBe('denied');
    expect(fixture.record({ kind: 'push', head: A })).toBe('denied');
  });

  it('keeps explicit bypass distinct from passed; missing approval never works', () => {
    const fixture = fixtureBoundary();
    fixture.record({ kind: 'review', head: A, outcome: 'setup-error' });
    expect(fixture.record({ kind: 'waiver', head: A, reason: 'provider unavailable', userApproved: false })).toBe('denied');
    expect(fixture.record({ kind: 'push', head: A })).toBe('denied');
    fixture.record({ kind: 'waiver', head: A, reason: 'provider unavailable', userApproved: true });
    expect(fixture.record({ kind: 'verify', head: A })).toBe('bypassed');
    expect(fixture.record({ kind: 'pr-write', head: A })).toBe('bypassed');
  });
});

const roots: string[] = [];
afterEach(async () => { await Promise.all(roots.splice(0).map(path => rm(path, { recursive: true, force: true }))); });
async function integrationFixture() {
  const { repo } = await gitFixture(); roots.push(repo);
  await put(repo, 'src/a.ts', 'export const enabled = false;\n'); await commit(repo);
  const root = await mkdtemp(join(await realpath(tmpdir()), 'file-pr-gate-')); roots.push(root);
  const request = { repo, baseRef: 'base', headRef: 'HEAD', goal: 'Disable fixture toggle', builderModel: 'openai/gpt-6', attemptId: 'gate-attempt', policy: { ...DEFAULT_POLICY } };
  const head = await fixtureGit(repo, 'rev-parse', 'HEAD');
  return { root, request, head, current: { repo, baseRef: 'base', headRef: 'HEAD' }, stub: await publishingFixture(root, head) };
}
function fakeProvider(finding = false, onEffect?: () => void): Record<Lens, FixtureTransport> {
  const lensFixture = (lens: Lens): FixtureTransport => {
    const allegation: Finding = { id: 'toggle', lens, severity: 'P2', path: 'src/a.ts', revision: 'head', start: 1, end: 1,
      quote: 'export const enabled = false;', cause: 'Toggle disables expected behavior', trigger: 'Caller uses toggle', impact: 'Behavior unavailable', classification: 'introduced', uncertainty: null };
    return { kind: 'fixture', steps: [{ text: JSON.stringify({ findings: finding ? [allegation] : [], checkedPaths: ['src/a.ts'], omissions: [], requiredUnavailable: [] }) }], onEvent(event) { if (event.kind === 'effect') onEffect?.(); } };
  };
  return { correctness: lensFixture('correctness'), 'contracts-risk': lensFixture('contracts-risk') };
}

describe('real synthetic review/verify with executable publishing stubs', () => {
  it('clean one-round path reaches only fixture authority after real verifier rejects simulation', async () => {
    const { root, request, head, current, stub } = await integrationFixture(); let effects = 0;
    await stub.invoke('lookup');
    const result = await review(request, root, fakeProvider(false, () => effects++));
    expect(result.exit).toBe(0); expect(result.report.body.round).toBe(1); expect(effects).toBe(2);
    expect((await stub.invoke('push')).exit).toBe(1);
    await expect(verify(result.report, dismissedTriage(result.report), current)).rejects.toMatchObject({ code: 30 });
    await checkFixtureReceipt(result.report, dismissedTriage(result.report), current);
    await stub.authorize(head, 'fixture-only');
    expect((await stub.invoke('push')).exit).toBe(0); expect((await stub.invoke('pr-write')).exit).toBe(0);
    expect(await stub.events()).toEqual([
      { operation: 'lookup', head, status: 'read-only' }, { operation: 'push', head, status: 'denied' },
      { operation: 'push', head, status: 'fixture-only' }, { operation: 'pr-write', head, status: 'fixture-only' },
    ]);
  });

  it('P2 candidate requires fix/commit/full second review before stub upload; third snapshot stops', async () => {
    const { root, request, current, stub } = await integrationFixture(); const order: string[] = [];
    order.push('review'); const first = await review(request, root, fakeProvider(true)); expect(first.exit).toBe(10);
    const unresolved = dismissedTriage(first.report);
    for (const disposition of unresolved.dispositions) Object.assign(disposition, { status: 'unresolved', reason: 'Supported defect' });
    await expect(checkFixtureReceipt(first.report, unresolved, current)).rejects.toMatchObject({ code: 20 });
    expect((await stub.invoke('push')).exit).toBe(1);
    order.push('fix'); await put(request.repo, 'src/a.ts', 'export const enabled = true; // Fixed\n'); const fixed = await commit(request.repo);
    await expect(checkFixtureReceipt(first.report, dismissedTriage(first.report), current)).rejects.toMatchObject({ code: 21 });
    order.push('review'); const second = await review(request, root, fakeProvider());
    expect(second.report.body.round).toBe(2); expect(second.report.body.identity.snapshot.head).toBe(fixed);
    order.push('verify'); await checkFixtureReceipt(second.report, dismissedTriage(second.report), current);
    await stub.authorize(fixed, 'fixture-only'); order.push('push'); expect((await stub.invoke('push', fixed)).exit).toBe(0);
    order.push('pr-write'); expect((await stub.invoke('pr-write', fixed)).exit).toBe(0);
    expect(order).toEqual(['review', 'fix', 'review', 'verify', 'push', 'pr-write']);
    await put(request.repo, 'src/a.ts', 'export const enabled = 3;\n'); const third = await commit(request.repo);
    await expect(review(request, root, fakeProvider())).rejects.toMatchObject({ code: 20 });
    expect((await stub.invoke('push', third)).exit).toBe(1);
  });

  it('evidence-backed false-positive triage reuses unchanged report without another model effect', async () => {
    const { root, request, head, current, stub } = await integrationFixture(); let effects = 0;
    const first = await review(request, root, fakeProvider(true, () => effects++));
    await checkFixtureReceipt(first.report, dismissedTriage(first.report), current);
    const reused = await review(request, root, fakeProvider(false, () => effects++));
    expect(reused.reused).toBe(true); expect(effects).toBe(2);
    await stub.authorize(head, 'fixture-only'); expect((await stub.invoke('push')).exit).toBe(0);
  });

  it('unchanged existing PR lookup needs no inference or write', async () => {
    const { head, stub } = await integrationFixture();
    expect((await stub.invoke('lookup')).output).toEqual({ exists: true, head });
    expect(await stub.events()).toEqual([{ operation: 'lookup', head, status: 'read-only' }]);
  });

  it.each(['provider', 'dirty', 'stale'] as const)('%s blocker cannot reach stub publishing', async blocker => {
    const { root, request, current, stub } = await integrationFixture();
    const result = await review(request, root, blocker === 'provider' ? undefined : fakeProvider());
    if (blocker === 'provider') expect(result.exit).toBe(30);
    else if (blocker === 'dirty') await put(request.repo, 'untracked.ts', 'private edit\n');
    else { await put(request.repo, 'src/a.ts', 'export const enabled = 2;\n'); await commit(request.repo); }
    await expect(checkFixtureReceipt(result.report, dismissedTriage(result.report), current)).rejects.toBeInstanceOf(ReviewError);
    expect((await stub.invoke('push')).exit).toBe(1); expect((await stub.invoke('pr-write')).exit).toBe(1);
    expect((await stub.events()).every(event => event.status === 'denied')).toBe(true);
  });

  it('explicit user waiver stays bypassed, never a passed review or altered receipt', async () => {
    const { root, request, head, stub } = await integrationFixture(); const result = await review(request, root);
    const original = JSON.stringify(result.report); expect(result.exit).toBe(30);
    await expect(stub.authorize(head, 'bypassed')).rejects.toThrow('user approval');
    expect((await stub.invoke('push')).exit).toBe(1);
    await stub.authorize(head, 'bypassed', true);
    expect((await stub.invoke('push')).exit).toBe(0); expect((await stub.invoke('pr-write')).exit).toBe(0);
    expect((await stub.events()).filter(event => event.status === 'bypassed')).toHaveLength(2);
    expect(JSON.stringify(result.report)).toBe(original);
  });
});
