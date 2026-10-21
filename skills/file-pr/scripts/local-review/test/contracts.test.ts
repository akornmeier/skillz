import { mkdtemp, mkdir, readFile, realpath, rm, stat, symlink, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterEach, describe, expect, it } from 'vitest';
import {
  DEFAULT_POLICY, EXIT, FindingSchema, PolicySchema, ReviewReportSchema, ReviewRequestSchema,
  actionable, atomicPrivateWrite, canonicalJson, hash, loadReport, parseJson, reportExit,
  reusableReport, saveAttempt, saveReport, sealReport, validate, validateAttempt, validateFindingEvidence, validateReport,
  validateRequest, validateTriage,
} from '../src/contracts.js';
import { body, finding, identity, report, request, SHA_B } from './fixtures.js';

const roots: string[] = [];
async function temporary() { const path = await mkdtemp(join(await realpath(tmpdir()), 'file-pr-contract-')); roots.push(path); return path; }
afterEach(async () => { await Promise.all(roots.splice(0).map(path => rm(path, { recursive: true, force: true }))); });

describe('strict schemas and evidence', () => {
  it('round-trips valid schema-derived report and canonical identity', () => {
    const original = report();
    expect(validateReport(parseJson(ReviewReportSchema, JSON.stringify(original)))).toEqual(original);
    expect(hash({ b: 2, a: 1 })).toBe(hash({ a: 1, b: 2 }));
    expect(canonicalJson({ b: [2, 1], a: 1 })).toBe('{"a":1,"b":[2,1]}');
    expect(reportExit(original)).toBe(EXIT.complete);
  });
  it('rejects malformed JSON, extra/missing fields and invalid statuses', () => {
    expect(() => parseJson(ReviewRequestSchema, '{')).toThrow('Malformed JSON');
    expect(() => validate(ReviewRequestSchema, { ...request(), command: 'git push' })).toThrow();
    expect(() => validate(ReviewRequestSchema, { repo: 'x' })).toThrow();
    expect(() => validate(FindingSchema, { ...finding(), severity: 'P4' })).toThrow();
    expect(() => sealReport({ ...body(), status: 'passed' })).toThrow();
    expect(() => sealReport({ ...body(), transcript: 'unminimized data' })).toThrow();
  });
  it('bounds every policy before consumers use it; live cannot activate', () => {
    expect(validate(PolicySchema, DEFAULT_POLICY)).toEqual(DEFAULT_POLICY);
    for (const [key, value] of Object.entries(DEFAULT_POLICY)) {
      const invalid = typeof value === 'number' ? 1_000_000_000 : true;
      expect(() => validate(PolicySchema, { ...DEFAULT_POLICY, [key]: invalid }), key).toThrow();
    }
    expect(() => validate(PolicySchema, { ...DEFAULT_POLICY, requestsPerLens: 0 })).toThrow();
  });
  it('rejects unsafe refs and non-independent/unknown builder', () => {
    for (const baseRef of ['--help', 'a^{tree}', 'a..b', 'a:b', 'a@{0}', 'a\nHEAD']) expect(() => validateRequest({ ...request(), baseRef })).toThrow();
    for (const builderModel of ['anthropic/claude-haiku-5.5', 'unknown']) expect(() => validateRequest({ ...request(), builderModel })).toThrow();
    expect(validateRequest(request())).toEqual(request());
  });
  it('validates exact quotes, ordered spans, safe paths and changed-line anchors', () => {
    const source = 'if (valid) {\nreturn false;\n}';
    expect(validateFindingEvidence(finding(), source, [{ start: 2, end: 2 }])).toEqual(finding());
    for (const change of [{ quote: 'return true;' }, { start: 3, end: 2 }, { end: 99 }, { path: '../secret' }, { path: 'src/a\n.ts' }, { classification: 'uncertain' }]) {
      expect(() => validateFindingEvidence({ ...finding(), ...change }, source, [{ start: 2, end: 2 }])).toThrow();
    }
    expect(() => validateFindingEvidence(finding(), source, [{ start: 3, end: 3 }])).toThrow();
    expect(validateFindingEvidence({ ...finding(), revision: 'base' }, source, [{ start: 2, end: 2 }]).revision).toBe('base');
  });
  it('never discards P2; P3 alone is nonblocking; pre-existing still requires parent triage', () => {
    const b = body();
    b.lenses.correctness.findings = [finding()];
    expect(actionable(finding())).toBe(true);
    expect(reportExit(sealReport(b))).toBe(10);
    b.lenses.correctness.findings[0] = { ...finding(), severity: 'P3' };
    expect(reportExit(sealReport(b))).toBe(0);
    b.lenses.correctness.findings[0] = { ...finding(), classification: 'pre-existing' };
    expect(reportExit(sealReport(b))).toBe(10);
  });
  it('rejects omitted/mislabeled lenses, 9 candidates, duplicate IDs and invalid timings', () => {
    const b = body();
    expect(() => sealReport({ ...b, lenses: { correctness: b.lenses.correctness } })).toThrow();
    b.lenses['contracts-risk'].lens = 'correctness';
    expect(() => sealReport(b)).toThrow();
    const c = body();
    c.lenses.correctness.findings = Array.from({ length: 9 }, (_, i) => ({ ...finding(), id: `f-${i}` }));
    expect(() => sealReport(c)).toThrow();
    c.lenses.correctness.findings = [finding(), finding()];
    expect(() => sealReport(c)).toThrow();
    expect(() => sealReport({ ...body(), endedAt: 0 })).toThrow();
    const empty = body(); empty.lenses.correctness.checkedPaths = [];
    expect(() => sealReport(empty)).toThrow('checked paths');
    empty.lenses.correctness.checkedPaths = ['src/a.ts']; empty.lenses.correctness.usage.requests = 0;
    expect(() => sealReport(empty)).toThrow('observed requests');
  });
  it('rejects wrong returned model/route and policy tampering', () => {
    const b = body();
    expect(() => sealReport({ ...b, identity: { ...b.identity, model: { ...b.identity.model, returned: 'claude-sonnet' } } })).toThrow();
    expect(() => sealReport({ ...b, identity: { ...b.identity, model: { ...b.identity.model, endpoint: 'https://other.test' } } })).toThrow();
    const r = report();
    r.body.identity.policy.toolsPerLens = 7;
    expect(() => validateReport(r)).toThrow('Tampered');
  });
  it('rejects changed receipt identities, tampered content and partial receipt', () => {
    for (const key of ['promptHash', 'toolPolicyHash', 'filterPolicyHash', 'lockHash', 'runtimeHash', 'reviewSettingsHash'] as const) {
      expect(() => validateReport(report(), { ...identity(), [key]: hash('changed') })).toThrow('Stale');
    }
    const changed = identity(); changed.snapshot.head = 'c'.repeat(40);
    expect(() => validateReport(report(), changed)).toThrow('Stale');
    expect(() => validateReport({ ...report(), receipt: {} })).toThrow();
    const r = report(); r.body.lenses.correctness.checkedPaths = ['elsewhere.ts'];
    expect(() => validateReport(r)).toThrow('Tampered');
  });
  it('cannot seal incomplete coverage or uncertainty as complete, nor reuse unfinished attempts', () => {
    const b = body(); b.lenses.correctness.status = 'incomplete'; b.lenses.correctness.reason = 'missing source';
    expect(() => sealReport(b)).toThrow();
    b.status = 'incomplete';
    expect(reportExit(sealReport(b))).toBe(20);
    expect(reusableReport(sealReport(b), identity())).toBe(false);
    expect(reusableReport(report(), identity())).toBe(true);
    const c = body(); c.omissions = [{ path: 'src/a.ts', revision: 'head', reason: 'secret', changed: true, semantic: true }];
    expect(() => sealReport(c)).toThrow('Omitted');
    const d = body(); d.lenses.correctness.usage = { state: 'uncertain', requests: 1, reason: 'interrupted' };
    expect(() => sealReport(d)).toThrow();
    d.lenses.correctness.usage = { state: 'unavailable', requests: 1, reason: 'No observed accounting after dispatch' };
    expect(() => sealReport(d)).toThrow();
    d.status = 'incomplete';
    expect(reusableReport(sealReport(d), identity())).toBe(false);
  });
  it('requires every disposition to bind ID and source/test evidence, never bare fixed', () => {
    const b = body(); b.lenses.correctness.findings = [finding()]; const r = sealReport(b);
    const triage = { schemaVersion: 1, reportId: b.reportId, attemptId: b.attemptId, identityDigest: r.receipt.identityDigest, dispositions: [{ findingId: 'finding-1', status: 'fixed', commit: SHA_B, evidence: [{ kind: 'test', reference: 'pnpm test focused', observation: 'Executed and passed' }] }] };
    expect(validateTriage(triage, r)).toEqual(triage);
    expect(() => validateTriage({ ...triage, dispositions: [] }, r)).toThrow('Missing');
    expect(() => validateTriage({ ...triage, dispositions: [{ findingId: 'finding-1', status: 'fixed' }] }, r)).toThrow();
    expect(() => validateTriage({ ...triage, dispositions: [{ ...triage.dispositions[0], evidence: [] }] }, r)).toThrow();
    expect(() => validateTriage({ ...triage, dispositions: [{ ...triage.dispositions[0], findingId: 'unknown' }] }, r)).toThrow();
    expect(() => validateTriage({ ...triage, reportId: 'another' }, r)).toThrow('another');
  });
});

describe('private, atomic minimized state outside checkouts', () => {
  it('rejects partial ledger settlement, extra requests and oversized reservations', () => {
    const state = { schemaVersion: 1, attemptId: 'a1', owner: 'process1', rounds: [{ round: 1, identityDigest: hash('id'), status: 'settled', reportId: null }], reservations: [] };
    expect(() => validateAttempt(state)).toThrow('Unsettled');
    const reserved = { ...state, rounds: [{ ...state.rounds[0], status: 'reserved' }], reservations: Array.from({ length: 4 }, (_, index) => ({ id: `r${index}`, round: 1, lens: 'correctness', state: 'reserved', reservedUsd: 0.01 })) };
    expect(() => validateAttempt(reserved)).toThrow('bound');
    expect(() => validateAttempt({ ...reserved, reservations: reserved.reservations.slice(0, 2).map(item => ({ ...item, reservedUsd: 0.08 })) })).toThrow('cap');
  });
  it('writes 0700 directories/0600 JSON and Markdown, round-trips without transcript/source', async () => {
    const root = join(await temporary(), 'private', 'reports');
    const paths = await saveReport(root, report());
    expect((await stat(root)).mode & 0o777).toBe(0o700);
    for (const path of Object.values(paths)) expect((await stat(path)).mode & 0o777).toBe(0o600);
    expect(await loadReport(root, 'fixture-report.json')).toEqual(report());
    expect(await readFile(paths.markdown, 'utf8')).toContain('Not push authorization');
    await atomicPrivateWrite(root, 'fixture-report.md', 'replacement');
    expect(await readFile(paths.markdown, 'utf8')).toBe('replacement');
  });
  it('rejects checkout roots, symlink components and path escapes', async () => {
    const root = await temporary();
    await mkdir(join(root, 'repo', '.git'), { recursive: true });
    await expect(saveReport(join(root, 'repo', 'state'), report())).rejects.toThrow('outside Git');
    await symlink(join(root, 'repo'), join(root, 'linked'));
    await expect(saveReport(join(root, 'linked', 'state'), report())).rejects.toThrow('Unsafe state');
    await expect(atomicPrivateWrite(root, '../escape.json', '{}')).rejects.toThrow('Unsafe state name');
    await expect(loadReport(root, '../escape.json')).rejects.toThrow();
  });
  it('rejects partial or loose-mode stored reports and leaves interrupted state nonclean', async () => {
    const root = await temporary();
    await writeFile(join(root, 'partial.json'), '{', { mode: 0o600 });
    await expect(loadReport(root, 'partial.json')).rejects.toThrow();
    await writeFile(join(root, 'loose.json'), JSON.stringify(report()), { mode: 0o644 });
    await expect(loadReport(root, 'loose.json')).rejects.toThrow('Unsafe report');
    const path = await saveAttempt(root, { schemaVersion: 1, attemptId: 'a1', owner: 'process1', rounds: [{ round: 1, identityDigest: hash('id'), status: 'uncertain', reportId: null }], reservations: [{ id: 'request1', round: 1, lens: 'correctness', state: 'uncertain', reservedUsd: 0.01 }] });
    expect(JSON.parse(await readFile(path, 'utf8'))).toMatchObject({ rounds: [{ status: 'uncertain' }] });
    await expect(saveAttempt(root, { schemaVersion: 1, attemptId: 'a1', owner: 'p1', rounds: [], reservations: [], transcript: 'forbidden' })).rejects.toThrow();
  });
});
