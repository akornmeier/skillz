import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from 'vitest';
import { Type } from 'typebox';
import { mkdtemp, readFile, realpath, rm, stat } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { DEFAULT_POLICY, atomicPrivateWrite, hash, sealReport, validate, validateReport, type Finding } from '../src/contracts.js';
import { collectCalibration, gradeCalibration, loadCorpus, loadPrepared, prepareCalibration, readCalibrationJson, type PreparedCalibration } from '../src/calibration.js';
import { checkQualificationRecords, qualifyCalibration, skillBundleHash } from '../src/qualification.js';
import { calibrationCli, type CalibrationHost } from '../src/calibration-cli.js';
import { body } from './fixtures.js';

let root: string; let prepared: PreparedCalibration;
const runtimeHash = hash('synthetic-runtime'); const skillHash = hash('synthetic-skill');
const limits = () => ({ maxCostUsd: 12 * DEFAULT_POLICY.schedulingCapUsd, maxRequests: 72, maxDurationMs: 12 * DEFAULT_POLICY.roundDeadlineMs, deadlineAt: Date.now() + 12 * DEFAULT_POLICY.roundDeadlineMs, builderModel: 'openai/fixture-builder', runtimeHash, skillHash });
beforeAll(async () => { root = await mkdtemp(join(await realpath(tmpdir()), 'file-pr-calibration-')); prepared = await prepareCalibration(root, 'unit-cohort', runtimeHash, skillHash); });
afterAll(async () => { if (root) await rm(root, { recursive: true, force: true }); });
afterEach(async () => {
  for (const name of ['collection.json', 'collection.lock', 'grade.json', 'judgments.json', 'records.json', 'qualification.json', ...Array.from({ length: 12 }, (_, index) => `sample-${index}.json`)]) await rm(join(root, name), { force: true });
  await rm(join(root, 'evidence'), { recursive: true, force: true });
  vi.restoreAllMocks();
});

async function artifacts(options: { omitRequired?: boolean; falsePositives?: number; mode?: 'live' | 'simulated' } = {}) {
  const corpus = await loadCorpus(); const results = []; const judgments = [];
  for (const [index, item] of prepared.cases.entries()) {
    const source = corpus.cases.find(entry => entry.id === item.id)!; const label = corpus.gold.find(entry => entry.id === item.id)!;
    const draft = body();
    draft.identity.runtimeHash = runtimeHash;
    draft.identity.policy.live = options.mode === 'live';
    if (options.mode === 'live') draft.identity.authority = { approvalDigest: hash('synthetic-approval'), admissionDigest: hash('synthetic-admission'), purpose: 'calibration' };
    Object.assign(draft.identity.snapshot, { repo: item.repo, gitCommonDir: join(item.repo, '.git'), base: item.base, mergeBase: item.base, head: item.head });
    Object.assign(draft, { reportId: `sample-${index}`, attemptId: item.attemptId });
    const findings: Finding[] = [];
    if ((label.actionable && !(options.omitRequired && label.required)) || (!label.actionable && index < 8 + (options.falsePositives ?? 0))) {
      const path = label.path; const lines = source.after[path]!.split('\n'); const before = source.before[path]!.split('\n');
      const line = lines.findIndex((text, offset) => text !== before[offset]) + 1;
      findings.push({ id: `finding-${index}`, lens: 'correctness', severity: 'P2', path, revision: 'head', start: line, end: line, quote: lines[line - 1]!, cause: label.impact, trigger: label.trigger, impact: label.impact, classification: 'introduced', uncertainty: null });
    }
    draft.lenses.correctness.findings = findings;
    for (const lens of Object.values(draft.lenses)) {
      lens.identities = [draft.identity.model]; lens.checkedPaths = Object.keys(source.after);
      if (lens.usage.state === 'known') {
        lens.usage.costUsd = 0.001;
        if (options.mode === 'live') lens.calls = [{ generationId: `synthetic-${index}-${lens.lens}`, requestedUpstream: 'google-vertex/global', reportedProvider: 'Google', reportedModel: draft.identity.model.returned, inputTokens: lens.usage.inputTokens, outputTokens: lens.usage.outputTokens, cacheTokens: lens.usage.cacheTokens, costUsd: lens.usage.costUsd, routeDigest: hash('synthetic-route') }];
      }
    }
    draft.execution = { mode: options.mode ?? 'simulated', goal: 'Structural fixture, not real model evidence', builderModel: 'openai/fixture-builder', provenance: findings.map(finding => ({ canonicalId: finding.id, findingIds: [finding.id] })) };
    const report = sealReport(draft); await atomicPrivateWrite(root, `sample-${index}.json`, JSON.stringify(report));
    results.push({ id: item.id, reportFile: `sample-${index}.json`, reportDigest: report.receipt.reportDigest, wallMs: 1, costUsd: 0.002, requests: 2 });
    judgments.push({ id: item.id, triageMs: null, findings: findings.map(finding => ({ id: finding.id, disposition: 'supported', matchesSeed: label.actionable, evidence: `Synthetic grading fixture: ${finding.path}:${finding.start}; ${label.trigger}` })) });
  }
  await atomicPrivateWrite(root, 'collection.json', JSON.stringify({ schema: 1, preparedHash: hash(prepared), status: 'complete', startedAt: 1, maxCostUsd: limits().maxCostUsd, maxRequests: 72, deadlineAt: 10000000, activeCase: null, reservedUsd: 0, reason: null, results }));
  await atomicPrivateWrite(root, 'judgments.json', JSON.stringify({ schema: 1, runId: prepared.id, assessor: 'synthetic unit test, not paid qualification', cases: judgments }));
  return { results, judgments };
}

describe('calibration preparation and bounded execution, no provider calls', () => {
  it('prepares twelve opaque immutable repos with labels outside source', async () => {
    expect(await loadPrepared(root)).toEqual(prepared); expect(prepared.cases).toHaveLength(12);
    expect(prepared.cases.every(item => !item.repo.includes(item.id))).toBe(true);
    expect(await readFile(join(prepared.cases[0]!.repo, 'api.ts'), 'utf8')).toContain('displayName');
    await expect(prepareCalibration(root, 'unit-cohort', runtimeHash, skillHash)).rejects.toMatchObject({ code: 'EEXIST' });
  });
  it.each(['_trial', '-trial'])('rejects unrunnable calibration ID %s before creating repositories', async id => {
    const destination = join(root, `invalid${id}`);
    await expect(prepareCalibration(destination, id, runtimeHash, skillHash)).rejects.toMatchObject({ code: 20 });
    await expect(stat(join(destination, 'repos'))).rejects.toMatchObject({ code: 'ENOENT' });
  });
  it('rejects drifted implementation before review callback', async () => {
    let calls = 0; await expect(collectCalibration(root, { ...limits(), runtimeHash: hash('changed') }, async () => { calls++; throw new Error('no call'); })).rejects.toMatchObject({ code: 21 });
    expect(calls).toBe(0);
  });
  it('rejects a relabeled prepared source cohort before any reviewer effect', async () => {
    const changed = structuredClone(prepared);
    [changed.cases[0]!.id, changed.cases[1]!.id] = [changed.cases[1]!.id, changed.cases[0]!.id];
    await atomicPrivateWrite(root, 'prepared.json', JSON.stringify(changed));
    let calls = 0;
    try { await expect(collectCalibration(root, limits(), async () => { calls++; throw new Error('No effect'); })).rejects.toMatchObject({ code: 21 }); }
    finally { await atomicPrivateWrite(root, 'prepared.json', JSON.stringify(prepared)); }
    expect(calls).toBe(0);
  });
  it('requires conservative aggregate cost/request/time admission', async () => {
    for (const override of [{ maxCostUsd: DEFAULT_POLICY.schedulingCapUsd / 2 }, { maxRequests: 1 }, { maxDurationMs: 1 }]) {
      let calls = 0;
      await expect(collectCalibration(root, { ...limits(), ...override }, async () => { calls++; throw new Error('no call'); })).rejects.toMatchObject({ code: 20 });
      expect(calls).toBe(0); await rm(join(root, 'collection.json'));
    }
  });
  it('persists reservation before effect and blocks interrupted rerun without replacing evidence', async () => {
    let calls = 0;
    await expect(collectCalibration(root, limits(), async () => {
      calls++; expect(await readCalibrationJson(join(root, 'collection.json'))).toMatchObject({ activeCase: prepared.cases[0]!.id, reservedUsd: DEFAULT_POLICY.schedulingCapUsd });
      throw new Error('Synthetic uncertain provider effect');
    })).rejects.toThrow('Synthetic uncertain');
    const before = await readFile(join(root, 'collection.json'), 'utf8'); expect(JSON.parse(before)).toMatchObject({ status: 'blocked', reservedUsd: DEFAULT_POLICY.schedulingCapUsd });
    await expect(collectCalibration(root, limits(), async () => { calls++; throw new Error('no retry'); })).rejects.toMatchObject({ code: 20 });
    expect(await readFile(join(root, 'collection.json'), 'utf8')).toBe(before); expect(calls).toBe(1);
  });
});

describe('evidence-backed grading, never simulated release approval', () => {
  it('computes both-lens versus correctness metrics on native-evidence-shaped unit fixtures', async () => {
    await artifacts({ mode: 'live' }); const grade = await gradeCalibration(root, join(root, 'judgments.json'));
    expect(grade).toMatchObject({ detected: 8, correctnessDetected: 8, seeded: 8, requests: 24, inputTokens: 480, outputTokens: 720, cacheTokens: 0, falsePositives: 0, cleanControls: 4, requiredDetected: true, qualityMet: true, eligible: true, rolloutApproved: false, coldStartupMs: null, modelOnlyMs: null });
    expect(grade.rows.reduce((sum, row) => sum + row.rawCandidates, 0)).toBe(8);
  });
  it('mandatory cross-file/error-path misses fail despite six remaining seeded catches', async () => {
    await artifacts({ mode: 'live', omitRequired: true }); const grade = await gradeCalibration(root, join(root, 'judgments.json'));
    expect(grade.detected).toBe(6); expect(grade.requiredDetected).toBe(false); expect(grade.qualityMet).toBe(false);
  });
  it('two actionable clean-control false positives fail quality floor', async () => {
    await artifacts({ mode: 'live', falsePositives: 2 }); const grade = await gradeCalibration(root, join(root, 'judgments.json'));
    expect(grade.falsePositives).toBe(2); expect(grade.qualityMet).toBe(false);
  });
  it('keeps simulated candidates out of real detection numerators and promotion', async () => {
    await artifacts(); const grade = await gradeCalibration(root, join(root, 'judgments.json'));
    expect(grade.detected).toBe(0); expect(grade.eligible).toBe(false); expect(grade.rows.reduce((sum, row) => sum + row.rawCandidates, 0)).toBe(8);
  });
  it('rejects a live label without native billing/authority evidence', async () => {
    const { results } = await artifacts();
    for (const result of results) {
      const input = validate(Type.Object({ body: Type.Object({}, { additionalProperties: true }) }, { additionalProperties: true }), await readCalibrationJson(join(root, result.reportFile)));
      const report = sealReport({ ...input.body, execution: { mode: 'live', goal: 'Structural unit fixture', builderModel: 'openai/fixture', provenance: [] } });
      await atomicPrivateWrite(root, result.reportFile, JSON.stringify(report)); result.reportDigest = report.receipt.reportDigest;
    }
    const state = await readCalibrationJson(join(root, 'collection.json')); if (!state || typeof state !== 'object') throw new Error('Invalid fixture state');
    await atomicPrivateWrite(root, 'collection.json', JSON.stringify({ ...state, results }));
    expect((await gradeCalibration(root, join(root, 'judgments.json'))).eligible).toBe(false);
  });
  it('requires explicit judgment for every raw allegation', async () => {
    const { judgments } = await artifacts(); judgments[0]!.findings = [];
    await atomicPrivateWrite(root, 'judgments.json', JSON.stringify({ schema: 1, runId: prepared.id, assessor: 'fixture', cases: judgments }));
    await expect(gradeCalibration(root, join(root, 'judgments.json'))).rejects.toMatchObject({ code: 20 });
  });
  it('rejects collection cost tampering against authoritative report observations', async () => {
    const { results } = await artifacts(); results[0]!.costUsd = 0;
    const collection = await readCalibrationJson(join(root, 'collection.json'));
    if (!collection || typeof collection !== 'object' || Array.isArray(collection)) throw new Error('Invalid fixture collection');
    await atomicPrivateWrite(root, 'collection.json', JSON.stringify({ ...collection, results }));
    await expect(gradeCalibration(root, join(root, 'judgments.json'))).rejects.toMatchObject({ code: 21 });
  });
  it('keeps incomplete cases visible and out of promotion', async () => {
    await artifacts(); const collection = await readCalibrationJson(join(root, 'collection.json'));
    if (!collection || typeof collection !== 'object' || Array.isArray(collection)) throw new Error('Invalid fixture collection');
    await atomicPrivateWrite(root, 'collection.json', JSON.stringify({ ...collection, status: 'blocked', results: [] }));
    const grade = await gradeCalibration(root, join(root, 'judgments.json'));
    expect(grade.rows).toHaveLength(12); expect(grade.eligible).toBe(false); expect(grade.costUsd).toBeNull(); expect(grade.inputTokens).toBeNull(); expect(grade.requests).toBeNull();
  });
  it('refuses release qualification from simulated calibration before reading profile artifacts', async () => {
    await artifacts();
    await expect(qualifyCalibration(root, join(root, 'judgments.json'), '/not/read/records.json', runtimeHash)).rejects.toMatchObject({ code: 21 });
  });
});

async function recordArtifacts(bundleHash = skillHash) {
  const definitions = validate(Type.Object({ cases: Type.Array(Type.Object({ id: Type.String(), expectedBehavior: Type.Array(Type.String()), forbiddenBehavior: Type.Array(Type.String()) }, { additionalProperties: true })) }, { additionalProperties: true }), JSON.parse(await readFile(new URL('../../../evals/evals.json', import.meta.url), 'utf8')));
  const files: string[] = [];
  await atomicPrivateWrite(join(root, 'evidence'), 'transcript.txt.md', 'Synthetic coverage fixture only. No real harness execution.');
  for (const harness of ['pi', 'claude-code']) for (const profile of ['fast/economical', 'balanced/default', 'highest-reasoning']) for (const item of definitions.cases) {
    const name = `record-${files.length}.json`;
    await atomicPrivateWrite(join(root, 'evidence'), name, JSON.stringify({ schema: 1, skill: 'file-pr', skillRevision: 'synthetic', caseId: item.id, profile, provider: 'fixture', model: 'fixture', thinking: 'off', piVersion: '1.3.0', fixtureRevision: 'synthetic', outcome: 'pass', toolConfiguration: { harness, skillBundleHash: bundleHash, runtimeHash }, loadedFiles: ['SKILL.md'],
      assertions: [...item.expectedBehavior.map(text => ({ kind: 'expected', text, outcome: 'pass', evidence: ['transcript.txt.md'] })), ...item.forbiddenBehavior.map(text => ({ kind: 'forbidden', text, outcome: 'pass', evidence: ['transcript.txt.md'] }))], evidence: ['transcript.txt.md'] }));
    files.push(`evidence/${name}`);
  }
  await atomicPrivateWrite(root, 'records.json', JSON.stringify({ files })); return files;
}

describe('both-harness qualification artifact contract, not actual harness quality', () => {
  it('requires complete case/profile coverage for both Pi and Claude Code with present evidence', async () => {
    const files = await recordArtifacts(); const coverage = await checkQualificationRecords(join(root, 'records.json'), skillHash, runtimeHash);
    expect(coverage.records).toBe(files.length); expect(coverage.harnesses).toEqual(['pi', 'claude-code']); expect(coverage.profiles).toHaveLength(3);
  });
  it('successful synthetic grade and complete matrix still emit an unapproved signoff draft', async () => {
    const original = prepared; prepared = { ...prepared, skillHash: await skillBundleHash() };
    await atomicPrivateWrite(root, 'prepared.json', JSON.stringify(prepared));
    try {
      await artifacts({ mode: 'live' }); const files = await recordArtifacts(prepared.skillHash);
      const draft = await qualifyCalibration(root, join(root, 'judgments.json'), join(root, 'records.json'), runtimeHash);
      expect(draft).toMatchObject({ approved: false, by: null, status: 'awaiting-user-signoff', records: files.length, runtimeHash });
    } finally { prepared = original; await atomicPrivateWrite(root, 'prepared.json', JSON.stringify(prepared)); }
  });
  it('rejects an omitted profile/harness record', async () => {
    const files = await recordArtifacts(); await atomicPrivateWrite(root, 'records.json', JSON.stringify({ files: files.slice(1) }));
    await expect(checkQualificationRecords(join(root, 'records.json'), skillHash, runtimeHash)).rejects.toMatchObject({ code: 20 });
  });
  it('rejects duplicate records even when total count matches', async () => {
    const files = await recordArtifacts(); files[files.length - 1] = files[0]!; await atomicPrivateWrite(root, 'records.json', JSON.stringify({ files }));
    await expect(checkQualificationRecords(join(root, 'records.json'), skillHash, runtimeHash)).rejects.toMatchObject({ code: 21 });
  });
  it('rejects stale skill identity and empty primary evidence', async () => {
    await recordArtifacts(); await expect(checkQualificationRecords(join(root, 'records.json'), hash('stale'), runtimeHash)).rejects.toMatchObject({ code: 21 });
    await atomicPrivateWrite(join(root, 'evidence'), 'transcript.txt.md', '');
    await expect(checkQualificationRecords(join(root, 'records.json'), skillHash, runtimeHash)).rejects.toMatchObject({ code: 30 });
  });
  it('rejects absent or stale runtime identity despite unchanged skill instructions', async () => {
    const files = await recordArtifacts();
    await expect(checkQualificationRecords(join(root, 'records.json'), skillHash, hash('new-runtime'))).rejects.toMatchObject({ code: 21 });
    const record = validate(Type.Object({ toolConfiguration: Type.Record(Type.String(), Type.Unknown()) }, { additionalProperties: true }), await readCalibrationJson(join(root, files[0]!)));
    const configuration = { ...record.toolConfiguration }; delete configuration.runtimeHash;
    await atomicPrivateWrite(join(root, 'evidence'), 'record-0.json', JSON.stringify({ ...record, toolConfiguration: configuration }));
    await expect(checkQualificationRecords(join(root, 'records.json'), skillHash, runtimeHash)).rejects.toMatchObject({ code: 20 });
  });
  it('rejects profile evidence path traversal without reading outside root', async () => {
    const files = await recordArtifacts(); files[0] = '../not-readable.json'; await atomicPrivateWrite(root, 'records.json', JSON.stringify({ files }));
    await expect(checkQualificationRecords(join(root, 'records.json'), skillHash, runtimeHash)).rejects.toMatchObject({ code: 30 });
  });
});

describe('portable calibration CLI', () => {
  function host(): CalibrationHost {
    return { async runtimeHash() { throw new Error('Must not inspect runtime'); }, draftApproval() { return { status: 'DRAFT', sourceExport: false, keyFileRead: false }; }, async loadApproval() { throw new Error('Must not read authority'); }, async review() { throw new Error('Must not dispatch'); } };
  }
  it('help and every dry-run avoid authority/key reads, dispatch and artifact creation', async () => {
    expect(await calibrationCli(['--help'], host())).toHaveProperty('usage');
    for (const args of [ ['prepare', '--root', '/not/created', '--id', 'demo'], ['draft', '--root', '/not/read'], ['run', '--root', '/not/read', '--approval', '/not/read', '--builder-model', 'openai/fixture'], ['grade', '--root', '/not/read', '--judgments', '/not/read'], ['qualify', '--root', '/not/read', '--judgments', '/not/read', '--records', '/not/read'] ]) {
      expect(await calibrationCli([...args, '--dry-run'], host())).toMatchObject({ dryRun: true, keyRead: false, generation: false, authorization: false });
    }
  });
  it('draft populates exact twelve scopes but never grants export/key permission', async () => {
    expect(await calibrationCli(['draft', '--root', root], host())).toMatchObject({ status: 'DRAFT', purpose: 'calibration', sourceExport: false, keyFileRead: false, scopes: prepared.cases.map(item => ({ repo: item.repo, attemptId: item.attemptId, heads: [item.head] })) });
  });
  it('draft/missing aggregate approval blocks run before any review callback', async () => {
    const stub = host(); stub.loadApproval = async () => ({ status: 'DRAFT', purpose: 'calibration', expiresAt: Date.now() + 10000 });
    await expect(calibrationCli(['run', '--root', root, '--approval', '/synthetic/approval', '--builder-model', 'openai/fixture'], stub)).rejects.toMatchObject({ code: 20 });
    await expect(calibrationCli(['run', '--secret', 'DO_NOT_PRINT'], host())).rejects.not.toThrow('DO_NOT_PRINT');
  });
  it('collects twelve native-evidence-shaped callback fixtures and settles aggregate holds', async () => {
    await artifacts({ mode: 'live' }); await rm(join(root, 'collection.json'));
    let calls = 0;
    const state = await collectCalibration(root, limits(), async request => {
      const index = prepared.cases.findIndex(item => item.attemptId === request.attemptId); calls++;
      expect(await readCalibrationJson(join(root, 'collection.json'))).toMatchObject({ activeCase: prepared.cases[index]!.id, reservedUsd: DEFAULT_POLICY.schedulingCapUsd });
      return validateReport(await readCalibrationJson(join(root, `sample-${index}.json`)));
    });
    expect(calls).toBe(12); expect(state).toMatchObject({ status: 'complete', activeCase: null, reservedUsd: 0 });
    expect(state.results).toHaveLength(12); expect(state.results.reduce((sum, item) => sum + item.costUsd!, 0)).toBeCloseTo(0.024);
  });
  it('does not restart aggregate authority lifetime after asynchronous setup', async () => {
    const current = { ...prepared, skillHash: await skillBundleHash() }; await atomicPrivateWrite(root, 'prepared.json', JSON.stringify(current));
    let clock = Date.now(); vi.spyOn(Date, 'now').mockImplementation(() => clock); let calls = 0;
    const stub = host();
    stub.loadApproval = async () => ({ status: 'approved', purpose: 'calibration', expiresAt: clock + 3600000, calibrationBudget: { by: 'user', preparedHash: hash(current), expiresAt: clock + 5000, maxCostUsd: limits().maxCostUsd, maxRequests: 72, maxDurationMs: 1440000 } });
    stub.runtimeHash = async () => { clock += 6000; return runtimeHash; };
    stub.review = async () => { calls++; throw new Error('Expired aggregate authority reached review'); };
    try { await expect(calibrationCli(['run', '--root', root, '--approval', '/synthetic/approval', '--builder-model', 'openai/fixture'], stub)).rejects.toMatchObject({ code: 20 }); }
    finally { await atomicPrivateWrite(root, 'prepared.json', JSON.stringify(prepared)); }
    expect(calls).toBe(0);
  });
});
