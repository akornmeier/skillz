import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { describe, expect, it } from 'vitest';
import { fixtureBoundary } from './gate-fixture.js';

const A = 'a'.repeat(40);
const B = 'b'.repeat(40);

describe('phase-1 operation-log fixture self-checks (not skill execution)', () => {
  it('keeps original skill byte-for-byte; baseline snapshot held outside discovery by parent', async () => {
    const skill = await readFile(new URL('../../../SKILL.md', import.meta.url));
    expect(createHash('sha256').update(skill).digest('hex')).toBe('16f0bdb766426af949e57acec74328b3365ddd2851684bd36b10421b8c59848b');
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
