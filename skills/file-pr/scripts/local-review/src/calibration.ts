import { execFile } from 'node:child_process';
import { createHash } from 'node:crypto';
import { constants } from 'node:fs';
import { mkdir, mkdtemp, open, readFile, realpath, rm, writeFile } from 'node:fs/promises';
import { dirname, join, relative, resolve } from 'node:path';
import { promisify } from 'node:util';
import { Type, type Static } from 'typebox';
import { DEFAULT_POLICY, ReviewError, atomicPrivateWrite, hash, hashBytes, privateRoot, safePath, validate, validateReport, type ReviewReport, type ReviewRequest } from './contracts.js';

const execute = promisify(execFile);
const text = Type.String({ minLength: 1, maxLength: 4096 });
const digest = Type.String({ pattern: '^[a-f0-9]{64}$' });
const sha = Type.String({ pattern: '^[a-f0-9]{40}$' });
const CaseSchema = Type.Object({ id: text, before: Type.Record(Type.String(), Type.String()), after: Type.Record(Type.String(), Type.String()) }, { additionalProperties: false });
const GoldSchema = Type.Object({ id: text, actionable: Type.Boolean(), severity: Type.Union([text, Type.Null()]), path: text, trigger: text, impact: text, required: Type.Boolean() }, { additionalProperties: false });
export const CORPUS_HASH = 'da451dcf22472bb2c543fa43f49bc23ebc8d9be80237071181ee629f9f21931b';
export const GOLD_HASH = 'aa330352b3f8fc098d1512e1311d318cde482767ed573af307cb7261c7bc55da';
const PreparedSchema = Type.Object({ schema: Type.Literal(1), id: Type.String({ pattern: '^[a-zA-Z0-9_-]{1,40}$' }), createdAt: Type.Number(), runtimeHash: digest, skillHash: digest, corpusHash: Type.Literal(CORPUS_HASH), goldHash: Type.Literal(GOLD_HASH),
  cases: Type.Array(Type.Object({ id: text, repo: text, base: sha, head: sha, attemptId: text }, { additionalProperties: false }), { minItems: 12, maxItems: 12 }) }, { additionalProperties: false });
const CollectionSchema = Type.Object({ schema: Type.Literal(1), preparedHash: digest, status: Type.Union([Type.Literal('running'), Type.Literal('complete'), Type.Literal('blocked')]), startedAt: Type.Number(), maxCostUsd: Type.Number(), maxRequests: Type.Integer(), deadlineAt: Type.Number(),
  activeCase: Type.Union([text, Type.Null()]), reservedUsd: Type.Number(), reason: Type.Union([text, Type.Null()]),
  results: Type.Array(Type.Object({ id: text, reportFile: text, reportDigest: digest, wallMs: Type.Number(), costUsd: Type.Union([Type.Number(), Type.Null()]), requests: Type.Integer() }, { additionalProperties: false }), { maxItems: 12 }) }, { additionalProperties: false });
export const CalibrationBudgetSchema = Type.Object({ by: Type.Literal('user'), preparedHash: digest, expiresAt: Type.Number({ minimum: 1 }), maxCostUsd: Type.Number({ exclusiveMinimum: 0 }), maxRequests: Type.Integer({ minimum: 1, maximum: 72 }), maxDurationMs: Type.Number({ exclusiveMinimum: 0, maximum: 1440000 }) }, { additionalProperties: false });
const JudgmentsSchema = Type.Object({ schema: Type.Literal(1), runId: text, assessor: text, cases: Type.Array(Type.Object({ id: text, triageMs: Type.Union([Type.Number({ minimum: 0 }), Type.Null()]),
  findings: Type.Array(Type.Object({ id: text, disposition: Type.Union([Type.Literal('supported'), Type.Literal('dismissed')]), matchesSeed: Type.Boolean(), evidence: text }, { additionalProperties: false }), { maxItems: 16 }) }, { additionalProperties: false }), { minItems: 12, maxItems: 12 }) }, { additionalProperties: false });
export type PreparedCalibration = Static<typeof PreparedSchema>;
export type CalibrationJudgments = Static<typeof JudgmentsSchema>;
export type CalibrationLimits = { maxCostUsd: number; maxRequests: number; maxDurationMs: number; deadlineAt: number; builderModel: string; runtimeHash: string; skillHash: string };

/** Private operator artifacts only; never follow a symlink or read an arbitrary large transcript. */
export async function readCalibrationJson(path: string): Promise<unknown> {
  const parent = await realpath(dirname(path));
  if (parent !== resolve(dirname(path))) throw new ReviewError(30, 'Artifact parent must be a canonical private directory');
  const file = await open(path, constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const info = await file.stat();
    if (!info.isFile() || info.size > 1_048_576 || (info.mode & 0o777) !== 0o600 || (process.getuid && info.uid !== process.getuid())) throw new ReviewError(30, 'Invalid private calibration artifact');
    return JSON.parse(await file.readFile('utf8')) as unknown;
  } finally { await file.close(); }
}
export async function loadCorpus() {
  const casesBytes = await readFile(new URL('../test/calibration/cases.json', import.meta.url));
  const goldBytes = await readFile(new URL('../test/calibration/gold.json', import.meta.url));
  if (hashBytes(casesBytes) !== CORPUS_HASH || hashBytes(goldBytes) !== GOLD_HASH) throw new ReviewError(30, 'Frozen calibration corpus changed');
  const cases = validate(Type.Array(CaseSchema), JSON.parse(casesBytes.toString()));
  const gold = validate(Type.Array(GoldSchema), JSON.parse(goldBytes.toString()));
  if (cases.length !== 12 || gold.length !== 12 || new Set(cases.map(item => item.id)).size !== 12 || gold.filter(item => item.actionable).length !== 8) throw new ReviewError(30, 'Invalid calibration cohort');
  for (const item of cases) for (const path of [...Object.keys(item.before), ...Object.keys(item.after)]) if (!safePath(path)) throw new ReviewError(30, 'Unsafe corpus path');
  return { cases, gold };
}
async function git(repo: string, ...args: string[]) {
  const { stdout } = await execute('/usr/bin/git', ['-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false', '-c', 'protocol.allow=never', ...args], { cwd: repo, timeout: 10000, maxBuffer: 65536,
    env: { PATH: '/usr/bin:/bin', HOME: '/dev/null', GIT_CONFIG_NOSYSTEM: '1', GIT_CONFIG_GLOBAL: '/dev/null', GIT_NO_LAZY_FETCH: '1', GIT_NO_REPLACE_OBJECTS: '1', GIT_AUTHOR_NAME: 'Calibration', GIT_AUTHOR_EMAIL: 'calibration@example.invalid', GIT_COMMITTER_NAME: 'Calibration', GIT_COMMITTER_EMAIL: 'calibration@example.invalid', GIT_TERMINAL_PROMPT: '0' } });
  return stdout.trim();
}

/** Materialize only frozen source. Gold labels, revealing IDs and grading prose stay outside repos. */
export async function prepareCalibration(root: string, id: string, runtimeHash: string, skillHash: string) {
  const directory = await privateRoot(root); const { cases } = await loadCorpus();
  validate(Type.Object({ id: PreparedSchema.properties.id, runtimeHash: digest, skillHash: digest }, { additionalProperties: false }), { id, runtimeHash, skillHash });
  const repositories = join(directory, 'repos');
  // Exclusive creation also blocks partial preparations. Never overwrite or auto-recover them.
  await mkdir(repositories, { mode: 0o700 });
  const entries: PreparedCalibration['cases'] = [];
  for (const [index, item] of cases.entries()) {
    const repo = await mkdtemp(join(repositories, 'case-'));
    await git(repo, 'init', '--quiet', '--initial-branch=review', '--object-format=sha1');
    for (const [path, source] of Object.entries(item.before)) { await mkdir(dirname(join(repo, path)), { recursive: true }); await writeFile(join(repo, path), source); }
    await git(repo, 'add', '--all'); await git(repo, 'commit', '--quiet', '-m', 'Before change');
    const base = await git(repo, 'rev-parse', 'HEAD'); await git(repo, 'branch', 'base');
    for (const path of Object.keys(item.before)) if (!(path in item.after)) await rm(join(repo, path));
    for (const [path, source] of Object.entries(item.after)) { await mkdir(dirname(join(repo, path)), { recursive: true }); await writeFile(join(repo, path), source); }
    await git(repo, 'add', '--all'); await git(repo, 'commit', '--quiet', '-m', 'Candidate change');
    entries.push({ id: item.id, repo, base, head: await git(repo, 'rev-parse', 'HEAD'), attemptId: `${id}-${index}` });
  }
  const manifest = validate(PreparedSchema, { schema: 1, id, createdAt: Date.now(), runtimeHash, skillHash, corpusHash: CORPUS_HASH, goldHash: GOLD_HASH, cases: entries });
  await atomicPrivateWrite(directory, 'prepared.json', JSON.stringify(manifest));
  return manifest;
}
export async function loadPrepared(root: string) {
  const directory = await privateRoot(root);
  const manifest = validate(PreparedSchema, await readCalibrationJson(join(directory, 'prepared.json')));
  if (new Set(manifest.cases.map(item => item.id)).size !== 12) throw new ReviewError(30, 'Duplicate prepared case');
  const corpus = await loadCorpus();
  if (manifest.cases.some(item => !corpus.cases.some(source => source.id === item.id))) throw new ReviewError(30, 'Prepared cohort mismatch');
  for (const item of manifest.cases) if (relative(join(directory, 'repos'), item.repo).startsWith('..') || await realpath(item.repo) !== item.repo) throw new ReviewError(30, 'Prepared repository escapes owned root');
  return manifest;
}

async function verifyFrozenSource(item: PreparedCalibration['cases'][number]) {
  const source = (await loadCorpus()).cases.find(entry => entry.id === item.id)!;
  for (const [revision, files] of [[item.base, source.before], [item.head, source.after]] as const) {
    const paths = (await git(item.repo, 'ls-tree', '-r', '-z', '--name-only', revision)).split('\0').filter(Boolean).sort();
    if (hash(paths) !== hash(Object.keys(files).sort())) throw new ReviewError(21, 'Calibration source inventory differs from frozen corpus');
    for (const [path, text] of Object.entries(files)) {
      const oid = createHash('sha1').update(`blob ${Buffer.byteLength(text)}\0`).update(text).digest('hex');
      if (await git(item.repo, 'rev-parse', `${revision}:${path}`) !== oid) throw new ReviewError(21, 'Calibration source differs from frozen corpus');
    }
  }
}
function validateSample(report: ReviewReport, item: PreparedCalibration['cases'][number], prepared: PreparedCalibration) {
  if (report.body.identity.runtimeHash !== prepared.runtimeHash || report.body.identity.snapshot.repo !== item.repo || report.body.identity.snapshot.head !== item.head || report.body.identity.snapshot.base !== item.base || report.body.attemptId !== item.attemptId || report.body.round !== 1) throw new ReviewError(21, 'Calibration report identity mismatch');
}

function completeLiveSample(report: ReviewReport) {
  if (report.body.execution?.mode !== 'live' || !report.body.identity.policy.live || report.body.identity.authority?.purpose !== 'calibration' || report.body.status !== 'complete') return false;
  const generations = new Set<string>();
  return Object.values(report.body.lenses).every(lens => {
    if (lens.usage.state !== 'known' || lens.calls?.length !== lens.usage.requests || lens.identities?.length !== lens.usage.requests) return false;
    if (lens.calls.reduce((sum, call) => sum + call.costUsd, 0) !== lens.usage.costUsd || lens.calls.reduce((sum, call) => sum + call.inputTokens, 0) !== lens.usage.inputTokens || lens.calls.reduce((sum, call) => sum + call.outputTokens, 0) !== lens.usage.outputTokens || lens.calls.reduce((sum, call) => sum + call.cacheTokens, 0) !== lens.usage.cacheTokens) return false;
    return lens.calls.every((call, index) => {
      if (generations.has(call.generationId) || call.reportedModel !== lens.identities![index]!.returned) return false;
      generations.add(call.generationId); return true;
    });
  });
}

/** Collect once. Reservations precede callbacks; interrupted/uncertain runs never auto-resume. */
export async function collectCalibration(root: string, limits: CalibrationLimits, runReview: (request: ReviewRequest) => Promise<ReviewReport>) {
  const directory = await privateRoot(root); const prepared = await loadPrepared(directory);
  if (prepared.runtimeHash !== limits.runtimeHash || prepared.skillHash !== limits.skillHash) throw new ReviewError(21, 'Calibration implementation changed; prepare a new cohort');
  if (!Number.isFinite(limits.deadlineAt) || !Number.isFinite(limits.maxCostUsd) || limits.maxCostUsd <= 0 || limits.maxCostUsd > 12 * DEFAULT_POLICY.schedulingCapUsd || !Number.isInteger(limits.maxRequests) || limits.maxRequests < 1 || limits.maxRequests > 72 || !Number.isFinite(limits.maxDurationMs) || limits.maxDurationMs <= 0 || limits.maxDurationMs > 12 * DEFAULT_POLICY.roundDeadlineMs) throw new ReviewError(30, 'Invalid aggregate calibration limits');
  const owner = await open(join(directory, 'collection.lock'), constants.O_CREAT | constants.O_EXCL | constants.O_WRONLY | constants.O_NOFOLLOW, 0o600);
  const state: Static<typeof CollectionSchema> = { schema: 1, preparedHash: hash(prepared), status: 'running', startedAt: Date.now(), maxCostUsd: limits.maxCostUsd, maxRequests: limits.maxRequests, deadlineAt: Math.min(limits.deadlineAt, Date.now() + limits.maxDurationMs), activeCase: null, reservedUsd: 0, reason: null, results: [] };
  const save = () => atomicPrivateWrite(directory, 'collection.json', JSON.stringify(state));
  let admitted = false;
  try {
    try { await readCalibrationJson(join(directory, 'collection.json')); throw new ReviewError(20, 'Existing calibration run requires explicit reconciliation'); }
    catch (error) { if (!(error instanceof Error && 'code' in error && error.code === 'ENOENT')) throw error; }
    await save(); admitted = true;
    for (const item of prepared.cases) {
      const spent = state.results.reduce((sum, entry) => sum + (entry.costUsd ?? 0), 0);
      const requests = state.results.reduce((sum, entry) => sum + entry.requests, 0);
      if (spent + DEFAULT_POLICY.schedulingCapUsd > limits.maxCostUsd || requests + 2 * DEFAULT_POLICY.requestsPerLens > limits.maxRequests || Date.now() + DEFAULT_POLICY.roundDeadlineMs > state.deadlineAt) throw new ReviewError(20, 'Aggregate calibration admission budget exhausted');
      if (await git(item.repo, 'rev-parse', 'HEAD') !== item.head || await git(item.repo, 'rev-parse', 'base') !== item.base || await git(item.repo, 'status', '--porcelain', '--untracked-files=all')) throw new ReviewError(21, 'Prepared calibration source changed');
      await verifyFrozenSource(item);
      state.activeCase = item.id; state.reservedUsd = DEFAULT_POLICY.schedulingCapUsd; await save();
      if (Date.now() + DEFAULT_POLICY.roundDeadlineMs > state.deadlineAt) throw new ReviewError(20, 'Aggregate calibration authority expires before full round');
      const started = Date.now();
      const report = validateReport(await runReview({ repo: item.repo, baseRef: 'base', headRef: 'HEAD', goal: 'Review committed change for introduced defects', builderModel: limits.builderModel, attemptId: item.attemptId, policy: { ...DEFAULT_POLICY } }));
      validateSample(report, item, prepared);
      const requestCount = Object.values(report.body.lenses).reduce((sum, lens) => sum + lens.usage.requests, 0);
      const known = Object.values(report.body.lenses).every(lens => lens.usage.state === 'known');
      const costUsd = known ? Object.values(report.body.lenses).reduce((sum, lens) => sum + (lens.usage.state === 'known' ? lens.usage.costUsd : 0), 0) : null;
      const reportFile = `sample-${state.results.length}.json`; await atomicPrivateWrite(directory, reportFile, JSON.stringify(report));
      state.results.push({ id: item.id, reportFile, reportDigest: report.receipt.reportDigest, wallMs: Date.now() - started, costUsd, requests: requestCount });
      if (!completeLiveSample(report) || costUsd === null || costUsd > state.reservedUsd || requestCount > 2 * DEFAULT_POLICY.requestsPerLens) throw new ReviewError(20, 'Non-live, incomplete or uncertain calibration sample; stop and reconcile');
      state.activeCase = null; state.reservedUsd = 0; await save();
    }
    state.status = 'complete'; await save(); return state;
  } catch (error) {
    if (admitted) {
      state.status = 'blocked'; state.reason = error instanceof ReviewError ? error.message : 'Calibration interrupted; effects or billing may be unknown';
      await save();
    }
    throw error;
  } finally { await owner.close(); await rm(join(directory, 'collection.lock'), { force: true }); }
}

/** Human/parent judgments supply defect truth. Never infer correctness from quotes or gold wording. */
export async function gradeCalibration(root: string, judgmentsPath: string) {
  const directory = await privateRoot(root); const prepared = await loadPrepared(directory); const { gold } = await loadCorpus();
  const state = validate(CollectionSchema, await readCalibrationJson(join(directory, 'collection.json')));
  const judgments = validate(JudgmentsSchema, await readCalibrationJson(judgmentsPath));
  if (state.preparedHash !== hash(prepared) || judgments.runId !== prepared.id || new Set(judgments.cases.map(item => item.id)).size !== 12 || judgments.cases.some(item => !prepared.cases.some(entry => entry.id === item.id))) throw new ReviewError(21, 'Calibration judgments belong to another cohort');
  const rows = await Promise.all(prepared.cases.map(async item => {
    const sample = state.results.find(entry => entry.id === item.id); const judgment = judgments.cases.find(entry => entry.id === item.id)!; const label = gold.find(entry => entry.id === item.id)!;
    if (!sample) return { id: item.id, complete: false, detected: false, correctnessDetected: false, falsePositives: 0, rawCandidates: 0, roundMs: null, triageMs: judgment.triageMs, costUsd: null };
    if (!/^sample-\d+\.json$/.test(sample.reportFile)) throw new ReviewError(30, 'Unsafe calibration report reference');
    const report = validateReport(await readCalibrationJson(join(directory, sample.reportFile)));
    validateSample(report, item, prepared);
    const observedCost = Object.values(report.body.lenses).every(lens => lens.usage.state === 'known') ? Object.values(report.body.lenses).reduce((sum, lens) => sum + (lens.usage.state === 'known' ? lens.usage.costUsd : 0), 0) : null;
    if (report.receipt.reportDigest !== sample.reportDigest || observedCost !== sample.costUsd || Object.values(report.body.lenses).reduce((sum, lens) => sum + lens.usage.requests, 0) !== sample.requests) throw new ReviewError(21, 'Calibration sample drifted');
    const findings = Object.values(report.body.lenses).flatMap(lens => lens.findings);
    if (judgment.findings.length !== findings.length || new Set(judgment.findings.map(entry => entry.id)).size !== findings.length || judgment.findings.some(entry => !findings.some(finding => finding.id === entry.id))) throw new ReviewError(20, 'Every raw candidate needs one evidence-backed judgment');
    const supported = findings.filter(finding => finding.severity !== 'P3' && finding.classification === 'introduced' && judgment.findings.find(entry => entry.id === finding.id)?.disposition === 'supported');
    const matches = supported.filter(finding => judgment.findings.find(entry => entry.id === finding.id)?.matchesSeed);
    if (judgment.findings.some(entry => entry.matchesSeed && (!label.actionable || entry.disposition !== 'supported' || !matches.some(finding => finding.id === entry.id && finding.path === label.path)))) throw new ReviewError(20, 'Seed match lacks supported anchored defect judgment');
    const complete = completeLiveSample(report);
    return { id: item.id, complete, detected: complete && matches.length > 0, correctnessDetected: complete && matches.some(finding => finding.lens === 'correctness'), falsePositives: !complete || label.actionable ? 0 : new Set(supported.map(finding => hash({ path: finding.path, start: finding.start, cause: finding.cause.trim().toLowerCase().replace(/\s+/g, ' ') }))).size, rawCandidates: findings.length, roundMs: report.body.endedAt - report.body.startedAt, triageMs: judgment.triageMs, costUsd: sample.costUsd };
  }));
  const detected = rows.filter(row => row.detected).length; const falsePositives = rows.reduce((sum, row) => sum + row.falsePositives, 0);
  const requiredDetected = gold.filter(label => label.required).every(label => rows.some(row => row.id === label.id && row.detected));
  const times = rows.flatMap(row => row.roundMs === null ? [] : [row.roundMs]).sort((a, b) => a - b);
  const p50Ms = times.length ? (times[Math.floor((times.length - 1) / 2)]! + times[Math.floor(times.length / 2)]!) / 2 : null;
  const costUsd = rows.every(row => row.costUsd !== null) ? rows.reduce((sum, row) => sum + (row.costUsd ?? 0), 0) : null;
  const qualityMet = detected >= 6 && requiredDetected && falsePositives <= 1;
  const timingMet = p50Ms !== null && p50Ms <= 45000 && times.every(time => time <= DEFAULT_POLICY.roundDeadlineMs);
  const spendTargetMet = rows.every(row => row.costUsd !== null && row.costUsd <= 0.10);
  const eligible = state.status === 'complete' && rows.every(row => row.complete) && qualityMet && timingMet && spendTargetMet;
  const grade = { schema: 1, runId: prepared.id, preparedHash: hash(prepared), runtimeHash: prepared.runtimeHash, skillHash: prepared.skillHash, corpusHash: CORPUS_HASH, goldHash: GOLD_HASH, assessor: judgments.assessor, judgmentsHash: hash(judgments), collectionHash: hash(state), rows,
    detected, seeded: 8, correctnessDetected: rows.filter(row => row.correctnessDetected).length, falsePositives, cleanControls: 4, requiredDetected, p50Ms, latencyTargetMet: p50Ms !== null && p50Ms <= 45000, costUsd, coldStartupMs: null, warmStartupMs: null, modelOnlyMs: null, qualityMet, timingMet, spendTargetMet, eligible, rolloutApproved: false };
  await atomicPrivateWrite(directory, 'grade.json', JSON.stringify(grade)); return grade;
}
