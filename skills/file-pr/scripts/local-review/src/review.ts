import { constants } from 'node:fs';
import { open, readFile, rm } from 'node:fs/promises';
import { randomUUID } from 'node:crypto';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  DEFAULT_POLICY, ReviewError, actionable, hash, hashBytes, loadReport,
  privateRoot, reportExit, reusableReport, saveAttempt, saveReport, sealReport, validateAttempt,
  validateReport, validateRequest, validateTriage,
  type AttemptState, type LensResult, type Policy, type ReceiptIdentity, type ReviewRequest, type ReviewReport,
} from './contracts.js';
import { captureSnapshot, FILTER_VERSION, TOOL_VERSION, SOURCE_TOOL_SCHEMAS } from './snapshot.js';
import { runLens, MODEL, PROMPT, LENS_PROMPTS, type AttemptBudget, type FixtureTransport, type Lens } from './runtime.js';

const packageRoot = dirname(dirname(fileURLToPath(import.meta.url)));
/** Bind the code actually executing (source or emitted JS), never a caller-provided version label. */
export async function implementationIdentity() {
  const extension = import.meta.url.endsWith('.ts') ? 'ts' : 'js';
  const directory = dirname(fileURLToPath(import.meta.url));
  const names = ['contracts', 'snapshot', 'runtime', 'runtime-child', 'review', 'cli'];
  const sources = await Promise.all(names.map(async name => [name, hashBytes(await readFile(join(directory, `${name}.${extension}`)))]));
  const sdkManifestBytes = await readFile(new URL('../package.json', import.meta.resolve('@earendil-works/pi-coding-agent')));
  const sdkManifest = JSON.parse(sdkManifestBytes.toString('utf8')) as { version?: unknown };
  if (sdkManifest.version !== '1.3.0') throw new ReviewError(30, 'Installed SDK identity mismatch');
  const manifest = JSON.parse(await readFile(join(packageRoot, 'package.json'), 'utf8')) as { version?: unknown; dependencies?: Record<string, unknown> };
  if (manifest.version !== '0.1.0' || manifest.dependencies?.['@earendil-works/pi-coding-agent'] !== '1.3.0') throw new ReviewError(30, 'Unsupported runtime package');
  return { packageVersion: '0.1.0' as const, sdkVersion: '1.3.0' as const, nodeVersion: process.version,
    lockHash: hashBytes(await readFile(join(packageRoot, 'pnpm-lock.yaml'))), runtimeHash: hash({ sources, manifest, sdkManifestHash: hashBytes(sdkManifestBytes) }),
    promptHash: hash({ PROMPT, LENS_PROMPTS }), toolPolicyHash: hash({ TOOL_VERSION, SOURCE_TOOL_SCHEMAS }), filterPolicyHash: hash(FILTER_VERSION) };
}
export async function receiptIdentity(source: Awaited<ReturnType<typeof captureSnapshot>>, request: ReviewRequest): Promise<ReceiptIdentity> {
  return { snapshot: source.snapshot.identity, model: { ...MODEL }, ...await implementationIdentity(), policy: request.policy,
    reviewSettingsHash: hash({ goal: request.goal, builderModel: request.builderModel, policy: request.policy, execution: 'simulated' }) };
}
async function readPrivateJson(path: string): Promise<unknown> {
  const file = await open(path, constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const info = await file.stat();
    if (!info.isFile() || info.size > 1048576 || (info.mode & 0o777) !== 0o600 || (process.getuid && info.uid !== process.getuid())) throw new ReviewError(30, 'Unsafe state file');
    try { return JSON.parse(await file.readFile('utf8')) as unknown; } catch { throw new ReviewError(20, 'Corrupt state JSON'); }
  } finally { await file.close(); }
}
function missing(error: unknown): boolean { return error instanceof Error && 'code' in error && error.code === 'ENOENT'; }

/** Exclusive ownership is never auto-reclaimed. A crash needs explicit budget reconciliation. */
export async function ownAttempt(root: string, attemptId: string, policy: Policy = { ...DEFAULT_POLICY }) {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$/.test(attemptId)) throw new ReviewError(30, 'Unsafe attempt ID');
  const directory = await privateRoot(root); const lockPath = join(directory, `${attemptId}.lock`);
  let lock;
  try { lock = await open(lockPath, constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL | constants.O_NOFOLLOW, 0o600); }
  catch { throw new ReviewError(20, 'Attempt locked; do not automatically resume or reclaim'); }
  const owner = randomUUID();
  try { await lock.writeFile(owner); await lock.sync(); }
  catch (error) { await lock.close(); await rm(lockPath, { force: true }); throw error; }
  let state: AttemptState;
  try {
    try { state = validateAttempt(await readPrivateJson(join(directory, `${attemptId}.attempt.json`))); }
    catch (error) { if (!missing(error)) throw error; state = { schemaVersion: 1, attemptId, owner, rounds: [], reservations: [] }; }
    if (state.attemptId !== attemptId || state.rounds.some(round => round.status !== 'settled') || state.reservations.some(item => item.state !== 'settled')) throw new ReviewError(20, 'Interrupted/uncertain attempt; reconcile before explicit new attempt');
    state.owner = owner; await saveAttempt(directory, state);
  } catch (error) { await lock.close(); await rm(lockPath, { force: true }); throw error; }
  // Both lenses serialize durable reservations before any fixture effect.
  let writes = Promise.resolve();
  function mutate<T>(fn: () => T): Promise<T> {
    const operation = writes.then(async () => { const value = fn(); await saveAttempt(directory, state); return value; });
    writes = operation.then(() => {}, () => {}); return operation;
  }
  let round = 0;
  const budget: AttemptBudget = {
    reserve: lens => mutate(() => {
      if (!round || state.reservations.length >= policy.attemptRequests || state.reservations.filter(item => item.round === round && item.lens === lens).length >= policy.requestsPerLens) throw new ReviewError(20, 'Attempt reservation budget exhausted');
      const id = randomUUID();
      // Simulated transport has no billable charge. No unverified live rate assumption is used.
      state.reservations.push({ id, round, lens, state: 'reserved', reservedUsd: 0 }); return id;
    }),
    settle: id => mutate(() => { const item = state.reservations.find(item => item.id === id); if (!item || item.state !== 'reserved') throw new ReviewError(20, 'Unknown reservation'); item.state = 'settled'; }),
    uncertain: id => mutate(() => { const item = state.reservations.find(item => item.id === id); if (!item) throw new ReviewError(20, 'Unknown reservation'); item.state = 'uncertain'; }),
  };
  return {
    directory, budget, get state() { return structuredClone(state); },
    async begin(identityDigest: string) { return mutate(() => {
      if (state.rounds.length >= policy.maxRounds) throw new ReviewError(20, 'Two-round attempt limit exhausted');
      if (state.rounds.some(item => item.identityDigest === identityDigest)) throw new ReviewError(20, 'Same incomplete identity cannot automatically rerun');
      round = state.rounds.length + 1; state.rounds.push({ round, identityDigest, status: 'reserved', reportId: null }); return round;
    }); },
    async finish(report: ReviewReport) { await mutate(() => {
      const item = state.rounds.find(item => item.round === round); if (!item) throw new ReviewError(20, 'Missing round');
      item.status = state.reservations.some(entry => entry.state !== 'settled') ? 'uncertain' : 'settled'; item.reportId = report.body.reportId;
    }); },
    async close() { await writes; await lock.close(); await rm(lockPath, { force: true }); },
  };
}
function lensResult(result: Awaited<ReturnType<typeof runLens>>, lens: Lens): LensResult {
  return { lens, status: result.status, findings: result.findings, checkedPaths: result.checkedPaths, omissions: result.omissions,
    reason: result.reason, usage: result.usage, startedAt: result.startedAt, endedAt: result.endedAt, identities: result.identities, observedModels: result.observedModels ?? [], contextGaps: result.contextGaps ?? [] };
}
/** Keep original allegations under each lens; dedupe view retains every finding's provenance. */
export function deduplicate(lenses: Record<Lens, LensResult>) {
  const groups = new Map<string, { canonicalId: string; findingIds: string[] }>();
  for (const lens of Object.values(lenses)) for (const finding of lens.findings) {
    const key = hash({ path: finding.path, revision: finding.revision, start: finding.start, end: finding.end, cause: finding.cause.trim().toLowerCase().replace(/\s+/g, ' ') });
    let group = groups.get(key); if (!group) { group = { canonicalId: finding.id, findingIds: [] }; groups.set(key, group); } group.findingIds.push(finding.id);
  }
  return [...groups.values()];
}
export async function review(input: unknown, root: string, fixtures?: Record<Lens, FixtureTransport>) {
  const request = validateRequest(input); const startedAt = Date.now();
  const deadlineAt = startedAt + request.policy.roundDeadlineMs;
  const source = await captureSnapshot(request, deadlineAt); const identity = await receiptIdentity(source, request);
  const attempt = await ownAttempt(root, request.attemptId, request.policy);
  try {
    const prior = attempt.state.rounds.find(round => round.identityDigest === hash(identity));
    if (prior?.reportId) {
      const report = await loadReport(attempt.directory, `${prior.reportId}.json`);
      if (!reusableReport(report, identity)) throw new ReviewError(20, 'Incomplete identity cannot be reused or rerun');
      return { report, reused: true, exit: reportExit(report), paths: { json: join(attempt.directory, `${prior.reportId}.json`), markdown: join(attempt.directory, `${prior.reportId}.md`) } };
    }
    const round = await attempt.begin(hash(identity));
    const remainingMs = request.policy.roundDeadlineMs - (Date.now() - startedAt);
    if (remainingMs <= 0) throw new ReviewError(20, 'Round deadline exhausted before dispatch');
    const controller = new AbortController(); const deadline = setTimeout(() => controller.abort(), remainingMs);
    let correctness: LensResult; let risk: LensResult;
    try {
      const run = async (lens: Lens) => {
        try {
          const result = lensResult(await runLens(source, lens, controller.signal, attempt.budget, fixtures?.[lens], request.policy), lens);
          if (result.status !== 'complete') controller.abort(); return result;
        } catch (error) { controller.abort(); throw error; }
      };
      // Ownership outlives every worker, including failures while persisting uncertainty.
      const [first, second] = await Promise.allSettled([run('correctness'), run('contracts-risk')]);
      if (first.status === 'rejected' || second.status === 'rejected') throw new ReviewError(20, 'Worker or review persistence failed; inspect uncertain attempt before retry');
      correctness = first.value; risk = second.value;
    } finally { controller.abort(); clearTimeout(deadline); }
    const lenses = { correctness, 'contracts-risk': risk };
    // IDs from independent lenses may collide. Namespace them while retaining lens provenance.
    for (const [lens, result] of Object.entries(lenses)) for (const finding of result.findings) finding.id = `${lens === 'correctness' ? 'c' : 'r'}-${hash({ id: finding.id, finding }).slice(0, 24)}`;
    const status = Object.values(lenses).every(result => result.status === 'complete') ? 'complete' : Object.values(lenses).some(result => result.status === 'setup-error') ? 'setup-error' : 'incomplete';
    const report = sealReport({ schemaVersion: 1, reportId: randomUUID(), attemptId: request.attemptId, round, identity, status, lenses,
      execution: { mode: 'simulated', goal: request.goal, builderModel: request.builderModel, provenance: deduplicate(lenses) },
      omissions: source.snapshot.omissions.filter(item => item.changed), startedAt, endedAt: Date.now() });
    const paths = await saveReport(attempt.directory, report); await attempt.finish(report);
    return { report, reused: false, exit: reportExit(report), paths };
  } finally { await attempt.close(); }
}

/** Re-capture actual source and implementation. Pinned OIDs never replace current intended refs. */
export async function verify(input: unknown, triageInput: unknown, current: { repo: string; baseRef: string; headRef: string }) {
  const report = validateReport(input);
  if (!report.body.execution) throw new ReviewError(30, 'Missing runtime provenance');
  const request = validateRequest({ ...current, goal: report.body.execution.goal, builderModel: report.body.execution.builderModel, attemptId: report.body.attemptId, policy: { ...DEFAULT_POLICY } });
  let source: Awaited<ReturnType<typeof captureSnapshot>>;
  try { source = await captureSnapshot(request); }
  catch (error) { if (error instanceof ReviewError && error.code === 20) throw new ReviewError(21, 'Current source cannot reproduce reviewed snapshot'); throw error; }
  const identity = await receiptIdentity(source, request);
  validateReport(report, identity);
  if (report.body.status !== 'complete') throw new ReviewError(20, 'Incomplete review');
  const triage = validateTriage(triageInput, report);
  for (const result of Object.values(report.body.lenses)) {
    if (!result.identities?.length || result.identities.length !== result.usage.requests) throw new ReviewError(20, 'Missing per-request model identity');
    for (const finding of result.findings) {
      source.validateFinding(finding);
      const disposition = triage.dispositions.find(item => item.findingId === finding.id);
      if (disposition?.status === 'fixed') throw new ReviewError(21, 'Fix requires new full-diff report at current head');
      if (actionable(finding) && (!disposition || disposition.status === 'unresolved')) throw new ReviewError(20, 'Unresolved actionable finding');
    }
  }
  // Offline fixtures test orchestration, not independent real-model review. Never authorize upload.
  throw new ReviewError(30, 'Simulated evidence cannot authorize real review or upload');
}
export async function verifyFiles(reportPath: string, triagePath: string, current: { repo: string; baseRef: string; headRef: string }) {
  return verify(await readPrivateJson(reportPath), await readPrivateJson(triagePath), current);
}
