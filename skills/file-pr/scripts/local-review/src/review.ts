import { constants } from 'node:fs';
import { open, readFile, rm } from 'node:fs/promises';
import { randomUUID } from 'node:crypto';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  DEFAULT_POLICY, ReviewError, actionable, defaultStateRoot, hash, hashBytes, loadReport,
  privateRoot, reportExit, reusableReport, saveAttempt, saveReport, sealReport, validateAttempt,
  validateReport, validateRequest, validateTriage,
  type AttemptState, type LensResult, type Policy, type ReceiptIdentity, type ReviewRequest, type ReviewReport,
} from './contracts.js';
import { captureSnapshot, FILTER_VERSION, TOOL_VERSION, SOURCE_TOOL_SCHEMAS } from './snapshot.js';
import { runLens, MODEL, PROMPT, LENS_PROMPTS, type AttemptBudget, type FixtureTransport, type Lens } from './runtime.js';
import { loadApproval, readApprovedKey, validateAuthority } from './approval.js';
import { createLiveTransport, preflight, type LiveTransport } from './openrouter.js';

const packageRoot = dirname(dirname(fileURLToPath(import.meta.url)));
/** Bind the code actually executing (source or emitted JS), never a caller-provided version label. */
export async function implementationIdentity() {
  const extension = import.meta.url.endsWith('.ts') ? 'ts' : 'js';
  const directory = dirname(fileURLToPath(import.meta.url));
  const names = ['contracts', 'snapshot', 'runtime', 'runtime-child', 'review', 'cli', 'approval', 'openrouter', 'calibration', 'calibration-cli', 'qualification'];
  const sources = await Promise.all(names.map(async name => [name, hashBytes(await readFile(join(directory, `${name}.${extension}`)))]));
  const sdkManifestBytes = await readFile(new URL('../package.json', import.meta.resolve('@earendil-works/pi-coding-agent')));
  const sdkManifest = JSON.parse(sdkManifestBytes.toString('utf8')) as { version?: unknown };
  if (sdkManifest.version !== '1.3.0') throw new ReviewError(30, 'Installed SDK identity mismatch');
  const manifest = JSON.parse(await readFile(join(packageRoot, 'package.json'), 'utf8')) as { version?: unknown; dependencies?: Record<string, unknown> };
  if (manifest.version !== '0.1.0' || manifest.dependencies?.['@earendil-works/pi-coding-agent'] !== '1.3.0') throw new ReviewError(30, 'Unsupported runtime package');
  const lockHash = hashBytes(await readFile(join(packageRoot, 'pnpm-lock.yaml')));
  return { packageVersion: '0.1.0' as const, sdkVersion: '1.3.0' as const, nodeVersion: process.version,
    lockHash, runtimeHash: hash({ sources, manifest, lockHash, sdkManifestHash: hashBytes(sdkManifestBytes) }),
    promptHash: hash({ PROMPT, LENS_PROMPTS }), toolPolicyHash: hash({ TOOL_VERSION, SOURCE_TOOL_SCHEMAS }), filterPolicyHash: hash(FILTER_VERSION) };
}
export async function receiptIdentity(source: Awaited<ReturnType<typeof captureSnapshot>>, request: ReviewRequest, authority?: ReceiptIdentity['authority']): Promise<ReceiptIdentity> {
  return { snapshot: source.snapshot.identity, model: { ...MODEL }, ...await implementationIdentity(), policy: request.policy,
    ...(authority ? { authority } : {}),
    reviewSettingsHash: hash({ goal: request.goal, builderModel: request.builderModel, policy: request.policy, execution: authority ? 'live' : 'simulated' }) };
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

/** Shared by review and verification; never reclaim a crashed owner's lock automatically. */
async function lockAttempt(root: string, attemptId: string) {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$/.test(attemptId)) throw new ReviewError(30, 'Unsafe attempt ID');
  const directory = await privateRoot(root); const lockPath = join(directory, `${attemptId}.lock`);
  let lock;
  try { lock = await open(lockPath, constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL | constants.O_NOFOLLOW, 0o600); }
  catch { throw new ReviewError(20, 'Attempt locked; do not automatically resume or reclaim'); }
  const owner = randomUUID();
  try { await lock.writeFile(owner); await lock.sync(); }
  catch (error) { await lock.close(); await rm(lockPath, { force: true }); throw error; }
  return { directory, owner, async close() { await lock.close(); await rm(lockPath, { force: true }); } };
}
/** Exclusive ownership is never auto-reclaimed. A crash needs explicit budget reconciliation. */
export async function ownAttempt(root: string, attemptId: string, policy: Policy = { ...DEFAULT_POLICY }) {
  const ownership = await lockAttempt(root, attemptId); const { directory, owner } = ownership;
  let state: AttemptState;
  try {
    try { state = validateAttempt(await readPrivateJson(join(directory, `${attemptId}.attempt.json`))); }
    catch (error) { if (!missing(error)) throw error; state = { schemaVersion: 1, attemptId, owner, rounds: [], reservations: [] }; }
    if (state.attemptId !== attemptId || state.rounds.some(round => round.status !== 'settled') || state.reservations.some(item => item.state !== 'settled')) throw new ReviewError(20, 'Interrupted/uncertain attempt; reconcile before explicit new attempt');
    state.owner = owner; await saveAttempt(directory, state);
  } catch (error) { await ownership.close(); throw error; }
  // Both lenses serialize durable reservations before any HTTP/fixture effect.
  let writes = Promise.resolve(); let persistenceFailed = false;
  function mutate<T>(fn: () => T): Promise<T> {
    const operation = writes.then(async () => {
      if (persistenceFailed) throw new ReviewError(20, 'Attempt persistence failed; dispatch disabled');
      const value = fn();
      try { await saveAttempt(directory, state); } catch (error) { persistenceFailed = true; throw error; }
      return value;
    });
    writes = operation.then(() => {}, () => {}); return operation;
  }
  let round = 0;
  const budget: AttemptBudget = {
    reserve: (lens, usd = 0) => mutate(() => {
      if (state.reservations.some(item => item.state === 'uncertain') || !Number.isFinite(usd) || usd < 0 || (policy.live && usd <= 0)
        || state.reservations.reduce((sum, item) => sum + (item.state === 'settled' ? item.observation?.costUsd ?? item.reservedUsd : item.reservedUsd), 0) + usd > policy.schedulingCapUsd + Number.EPSILON) throw new ReviewError(20, 'Scheduling cap or uncertain billing blocks dispatch');
      if (!round || state.reservations.length >= policy.attemptRequests || state.reservations.filter(item => item.round === round && item.lens === lens).length >= policy.requestsPerLens) throw new ReviewError(20, 'Attempt reservation budget exhausted');
      const id = randomUUID();
      state.reservations.push({ id, round, lens, state: 'reserved', reservedUsd: usd }); return id;
    }),
    settle: (id, observation) => mutate(() => {
      const item = state.reservations.find(item => item.id === id); if (!item || item.state !== 'reserved') throw new ReviewError(20, 'Unknown reservation');
      if (observation) item.observation = observation;
      item.state = (policy.live && !observation) || (observation && observation.costUsd > item.reservedUsd) ? 'uncertain' : 'settled';
    }).then(() => {
      if (state.reservations.find(item => item.id === id)?.state === 'uncertain') throw new ReviewError(20, 'Actual cost exceeded reservation; billing uncertain');
    }),
    uncertain: (id, evidence) => mutate(() => { const item = state.reservations.find(item => item.id === id); if (!item) throw new ReviewError(20, 'Unknown reservation'); item.state = 'uncertain'; if (evidence) item.rejectedEvidence = evidence; }),
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
    async close() { await writes; await ownership.close(); },
  };
}
function lensResult(result: Awaited<ReturnType<typeof runLens>>, lens: Lens): LensResult {
  return { lens, status: result.status, findings: result.findings, checkedPaths: result.checkedPaths, omissions: result.omissions,
    reason: result.reason, usage: result.usage, startedAt: result.startedAt, endedAt: result.endedAt, identities: result.identities, calls: result.calls ?? [], rejectedCalls: result.rejectedCalls ?? [], observedModels: result.observedModels ?? [], contextGaps: result.contextGaps ?? [] };
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
  if (validateRequest(input).policy.live) throw new ReviewError(30, 'Explicit live approval API required');
  return reviewInternal(input, root, fixtures);
}
/** Callable by Node clients (including Claude Code and Pi); no native harness workflow required. */
export async function reviewLive(request: ReviewRequest, stateRoot: string, approvalPath: string, expectedApprovalDigest?: string) {
  return reviewInternal({ ...request, policy: { ...request.policy, live: true } }, stateRoot, undefined, approvalPath, expectedApprovalDigest);
}
async function reviewInternal(input: unknown, root: string, fixtures?: Record<Lens, FixtureTransport>, approvalPath?: string, expectedApprovalDigest?: string) {
  const request = validateRequest(input); const startedAt = Date.now();
  const deadlineAt = startedAt + request.policy.roundDeadlineMs;
  const approval = approvalPath ? await loadApproval(approvalPath) : undefined;
  if (expectedApprovalDigest && (!approval || hash(approval) !== expectedApprovalDigest)) throw new ReviewError(30, 'Collection approval changed or revoked');
  if (request.policy.live && !approval) throw new ReviewError(30, 'Explicit approval required');
  const source = await captureSnapshot(request, deadlineAt);
  let identity = await receiptIdentity(source, request);
  let live: LiveTransport | undefined;
  let admission: Awaited<ReturnType<typeof preflight>> | undefined;
  if (approval) {
    validateAuthority(approval, request, source.snapshot.identity, identity.runtimeHash);
    admission = await preflight(approval, request.policy, AbortSignal.timeout(Math.max(1, deadlineAt - Date.now())));
    identity = await receiptIdentity(source, request, { approvalDigest: hash(approval), admissionDigest: admission.admissionDigest, purpose: approval.purpose });
  }
  const attempt = await ownAttempt(root, request.attemptId, request.policy);
  try {
    const prior = attempt.state.rounds.find(round => round.identityDigest === hash(identity));
    if (prior?.reportId) {
      const report = await loadReport(attempt.directory, `${prior.reportId}.json`);
      if (!reusableReport(report, identity)) throw new ReviewError(20, 'Incomplete identity cannot be reused or rerun');
      return { report, reused: true, exit: reportExit(report), paths: { json: join(attempt.directory, `${prior.reportId}.json`), markdown: join(attempt.directory, `${prior.reportId}.md`) } };
    }
    const round = await attempt.begin(hash(identity));
    if (approval && admission) {
      const confirmAuthority = async () => {
        if (!approvalPath || hash(await loadApproval(approvalPath)) !== hash(approval)) throw new ReviewError(30, 'Approval changed or revoked before dispatch');
        validateAuthority(approval, request, source.snapshot.identity, identity.runtimeHash);
      };
      await confirmAuthority();
      live = createLiveTransport(approval, request.policy, admission, await readApprovedKey(approval, request, source.snapshot.identity, identity.runtimeHash), fetch, confirmAuthority);
    }
    const remainingMs = request.policy.roundDeadlineMs - (Date.now() - startedAt);
    if (remainingMs <= 0) throw new ReviewError(20, 'Round deadline exhausted before dispatch');
    const controller = new AbortController(); const deadline = setTimeout(() => controller.abort(), remainingMs);
    let correctness: LensResult; let risk: LensResult;
    try {
      const run = async (lens: Lens) => {
        try {
          const result = lensResult(await runLens(source, lens, controller.signal, attempt.budget, live ?? fixtures?.[lens], request.policy), lens);
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
      execution: { mode: approval ? 'live' : 'simulated', goal: request.goal, builderModel: request.builderModel, provenance: deduplicate(lenses) },
      omissions: source.snapshot.omissions.filter(item => item.changed), startedAt, endedAt: Date.now() });
    const paths = await saveReport(attempt.directory, report); await attempt.finish(report);
    return { report, reused: false, exit: reportExit(report), paths };
  } finally { await attempt.close(); }
}

type CurrentSource = Pick<ReviewRequest, 'repo' | 'baseRef' | 'headRef'>;
/** Hold attempt ownership throughout verification against the authoritative store, never the report's directory. */
export async function verify(input: unknown, triageInput: unknown, current: CurrentSource, approvalPath?: string, stateRoot = defaultStateRoot()) {
  const report = validateReport(input);
  if (report.body.execution?.mode !== 'live') return verifyReport(report, triageInput, current, approvalPath);
  if (!approvalPath) throw new ReviewError(30, 'Current approval required for live verification');
  const ownership = await lockAttempt(stateRoot, report.body.attemptId);
  try {
    let state: AttemptState;
    try { state = validateAttempt(await readPrivateJson(join(ownership.directory, `${report.body.attemptId}.attempt.json`))); }
    catch { throw new ReviewError(20, 'Missing or invalid authoritative attempt state'); }
    const round = state.rounds.at(-1);
    if (state.attemptId !== report.body.attemptId || !round || state.rounds.some(item => item.status !== 'settled')
      || state.reservations.some(item => item.state !== 'settled')) throw new ReviewError(20, 'Active or uncertain attempt cannot authorize upload');
    if (round.round !== report.body.round || round.reportId !== report.body.reportId || round.identityDigest !== report.receipt.identityDigest) throw new ReviewError(21, 'Stale report: not the current settled round');
    const saved = validateReport(await readPrivateJson(join(ownership.directory, `${report.body.reportId}.json`)));
    if (saved.receipt.reportDigest !== report.receipt.reportDigest) throw new ReviewError(20, 'Report differs from authoritative stored evidence');
    for (const [lens, result] of Object.entries(report.body.lenses)) {
      const reservations = state.reservations.filter(item => item.round === round.round && item.lens === lens);
      const calls = result.calls ?? [];
      if (reservations.length !== calls.length || reservations.some((item, index) => !item.observation || hash(item.observation) !== hash(calls[index]))) throw new ReviewError(20, 'Report billing differs from authoritative settlement');
    }
    // Finish source/runtime/authority freshness last, after all durable evidence reads.
    await verifyReport(report, triageInput, current, approvalPath);
    return 0;
  } finally { await ownership.close(); }
}
/** Re-capture actual source and implementation. Pinned OIDs never replace current intended refs. */
async function verifyReport(report: ReviewReport, triageInput: unknown, current: CurrentSource, approvalPath?: string) {
  if (!report.body.execution) throw new ReviewError(30, 'Missing runtime provenance');
  const request = validateRequest({ ...current, goal: report.body.execution.goal, builderModel: report.body.execution.builderModel, attemptId: report.body.attemptId, policy: report.body.execution.mode === 'live' ? report.body.identity.policy : { ...DEFAULT_POLICY } });
  let source: Awaited<ReturnType<typeof captureSnapshot>>;
  try { source = await captureSnapshot(request); }
  catch (error) { if (error instanceof ReviewError && error.code === 20) throw new ReviewError(21, 'Current source cannot reproduce reviewed snapshot'); throw error; }
  let identity = await receiptIdentity(source, request);
  if (report.body.execution.mode === 'live') {
    if (!approvalPath) throw new ReviewError(30, 'Current approval required for live verification');
    const approval = await loadApproval(approvalPath);
    validateAuthority(approval, request, source.snapshot.identity, identity.runtimeHash);
    if (approval.purpose !== 'filing') throw new ReviewError(30, 'Calibration cannot authorize upload');
    const admission = await preflight(approval, request.policy, AbortSignal.timeout(request.policy.roundDeadlineMs));
    identity = await receiptIdentity(source, request, { approvalDigest: hash(approval), admissionDigest: admission.admissionDigest, purpose: approval.purpose });
  }
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
  if (report.body.execution.mode !== 'live' || !identity.authority || identity.authority.purpose !== 'filing') throw new ReviewError(30, 'Simulated evidence cannot authorize real review or upload');
  const generations = new Set<string>();
  for (const lens of Object.values(report.body.lenses)) {
    if (lens.usage.state !== 'known' || lens.calls?.length !== lens.usage.requests || lens.rejectedCalls?.length) throw new ReviewError(20, 'Missing authoritative live billing evidence');
    if (lens.calls.some(call => call.cacheTokens !== 0)) throw new ReviewError(20, 'Unexpected cached-token usage');
    if (lens.calls.reduce((sum, call) => sum + call.costUsd, 0) !== lens.usage.costUsd
      || lens.calls.reduce((sum, call) => sum + call.inputTokens, 0) !== lens.usage.inputTokens
      || lens.calls.reduce((sum, call) => sum + call.outputTokens, 0) !== lens.usage.outputTokens
      || lens.calls.reduce((sum, call) => sum + call.cacheTokens, 0) !== lens.usage.cacheTokens) throw new ReviewError(20, 'Live billing evidence mismatch');
    for (const [index, call] of lens.calls.entries()) {
      if (generations.has(call.generationId) || call.reportedModel !== lens.identities?.[index]?.returned) throw new ReviewError(20, 'Duplicate generation or returned model mismatch');
      generations.add(call.generationId);
    }
  }
  // Metadata fetch must not open a freshness window for changed source/runtime/authority.
  if (!approvalPath) throw new ReviewError(30, 'Current approval required');
  const finalSource = await captureSnapshot(request);
  const finalIdentity = await receiptIdentity(finalSource, request, identity.authority);
  const finalApproval = await loadApproval(approvalPath);
  validateAuthority(finalApproval, request, finalSource.snapshot.identity, finalIdentity.runtimeHash);
  if (hash(finalApproval) !== identity.authority.approvalDigest) throw new ReviewError(21, 'Approval changed during verification');
  validateReport(report, finalIdentity);
  return 0;
}
export async function verifyFiles(reportPath: string, triagePath: string, current: CurrentSource, approvalPath?: string, stateRoot?: string) {
  return verify(await readPrivateJson(reportPath), await readPrivateJson(triagePath), current, approvalPath, stateRoot);
}
