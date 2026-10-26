import { afterEach, describe, expect, it, vi } from 'vitest';
import { mkdtemp, readFile, realpath, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { draftApproval, loadApproval, type Approval } from '../src/approval.js';
import { prepareCalibration } from '../src/calibration.js';
import { calibrationCli } from '../src/calibration-cli.js';
import { skillBundleHash } from '../src/qualification.js';
import { DEFAULT_POLICY, hash, sealReport, validateAttempt, type CallObservation, type ReviewReport } from '../src/contracts.js';
import { implementationIdentity, ownAttempt, reviewLive, verify } from '../src/review.js';
import { cli } from '../src/cli.js';
import { captureSnapshot } from '../src/snapshot.js';
import * as snapshots from '../src/snapshot.js';
import * as approvals from '../src/approval.js';
import * as contracts from '../src/contracts.js';
import { commit, fixtureGit, gitFixture, put } from './git-fixture.js';

const dispatchRace = vi.hoisted(() => ({ delayExit: false, failedPid: undefined as number | undefined, failureObserved: false, pids: [] as number[] }));
vi.mock('node:child_process', async importOriginal => {
  const original = await importOriginal<typeof import('node:child_process')>();
  return { ...original, fork(...args: Parameters<typeof original.fork>) {
    const child = original.fork(...args); if (!dispatchRace.delayExit) return child;
    if (child.pid) dispatchRace.pids.push(child.pid);
    const kill = child.kill.bind(child); let held = false;
    child.on('message', (message: unknown) => {
      if (message && typeof message === 'object' && 'kind' in message && message.kind === 'request' && JSON.stringify(message).includes('Lens: correctness')) dispatchRace.failedPid = child.pid;
    });
    child.kill = signal => {
      if (child.pid === dispatchRace.failedPid) {
        if (!held) { held = true; dispatchRace.failureObserved = true; setTimeout(() => kill(signal), 180); }
        return true;
      }
      return kill(signal);
    };
    return child;
  } };
});
const roots: string[] = [];
afterEach(async () => { dispatchRace.delayExit = false; dispatchRace.failedPid = undefined; dispatchRace.failureObserved = false; dispatchRace.pids = []; vi.restoreAllMocks(); vi.unstubAllGlobals(); await Promise.all(roots.splice(0).map(root => rm(root, { recursive: true, force: true }))); });
async function setup(purpose: Approval['purpose'] = 'calibration', overrides: Partial<typeof DEFAULT_POLICY> = {}) {
  const { repo } = await gitFixture(); roots.push(repo); await put(repo, 'src/a.ts', 'export const enabled = false;\n'); const head = await commit(repo);
  const root = await mkdtemp(join(await realpath(tmpdir()), 'file-pr-live-')); roots.push(root);
  const keyPath = join(root, 'key'); await writeFile(keyPath, 'synthetic-key-not-real-0000', { mode: 0o600 });
  const request = { repo, baseRef: 'base', headRef: 'HEAD', goal: 'Check toggle', builderModel: 'openai/gpt-6', attemptId: 'live-test', policy: { ...DEFAULT_POLICY, ...overrides, live: true } };
  const runtime = await implementationIdentity();
  const approval: Approval = { ...draftApproval(), status: 'approved', purpose, approvedBy: 'synthetic operator', expiresAt: Date.now() + 60000, requestedUpstream: 'google-vertex/global', reportedProvider: 'Google',
    sourceExport: true, keyFileRead: true, keyPath, privacy: { zdr: true, dataCollection: 'deny', consent: true, accountLoggingDisabled: true }, limits: request.policy,
    ...(purpose === 'calibration' ? { calibrationBudget: { by: 'user' as const, preparedHash: hash('synthetic-prepared'), expiresAt: Date.now() + 50000, maxCostUsd: 1.02, maxRequests: 6, maxDurationMs: 120000 } } : {}),
    scopes: [{ repo, baseRef: 'base', attemptId: request.attemptId, heads: [head] }],
    rollout: purpose === 'filing' ? { by: 'user', signoff: 'synthetic test only', evidence: ['synthetic qualification'], runtimeHash: runtime.runtimeHash } : null };
  const approvalPath = join(root, 'approval.json'); await writeFile(approvalPath, JSON.stringify(approval), { mode: 0o600 });
  return { root, stateRoot: join(root, 'state'), request, approval, approvalPath, current: { repo, baseRef: 'base', headRef: 'HEAD' } };
}
const output = JSON.stringify({ findings: [], checkedPaths: ['src/a.ts'], omissions: [], requiredUnavailable: [] });
function reply(id: number, content = output, cost = .00001) {
  return { id: `gen-synthetic-${id}`, model: 'anthropic/claude-haiku-5.5-20261007', provider: 'Google', choices: [{ index: 0, finish_reason: 'stop', message: { role: 'assistant', content } }], usage: { prompt_tokens: 100, completion_tokens: 20, total_tokens: 120, cost, prompt_tokens_details: { cached_tokens: 0 } },
    openrouter_metadata: { requested: 'anthropic/claude-haiku-5.5', strategy: 'direct', attempt: 1, endpoints: { total: 1, available: [{ provider: 'Google', model: 'anthropic/claude-haiku-5.5-20261007', selected: true }] }, pipeline: [] } };
}
function intercept(onPost?: (id: number, init: RequestInit) => Promise<Response>) {
  let posts = 0; const bodies: string[] = [];
  const fetcher = vi.fn<typeof fetch>(async (url, init) => {
    const path = String(url);
    if (!path.startsWith('https://openrouter.ai/api/v1/')) throw new Error('Unexpected network');
    if (path.endsWith('/chat/completions')) { posts++; bodies.push(String(init?.body)); return onPost ? onPost(posts, init!) : Response.json(reply(posts)); }
    expect(init?.headers).toBeUndefined();
    if (path.endsWith('/endpoints')) return Response.json({ data: { id: 'anthropic/claude-haiku-5.5', endpoints: [{ tag: 'google-vertex/global', provider_name: 'Google', model_id: 'anthropic/claude-haiku-5.5', status: 0, context_length: 1000000, max_completion_tokens: 128000, supports_implicit_caching: false, supported_parameters: ['tools', 'tool_choice', 'max_tokens', 'reasoning', 'include_reasoning'], pricing: { prompt: '0.0000001', completion: '0.0000005', overrides: [{ min_prompt_tokens: 100000, prompt: '0.0000005', completion: '0.0000025' }] } }] } });
    if (path.endsWith('/endpoints/zdr')) return Response.json({ data: [{ model_id: 'anthropic/claude-haiku-5.5', tag: 'google-vertex/global', provider_name: 'Google' }] });
    if (path.endsWith('/models')) return Response.json({ data: [{ id: 'anthropic/claude-haiku-5.5', canonical_slug: 'anthropic/claude-haiku-5.5-20261007', context_length: 1000000 }] });
    throw new Error('Unexpected network');
  });
  vi.stubGlobal('fetch', fetcher); return { fetcher, bodies, get posts() { return posts; } };
}
async function wait(ready: () => boolean | Promise<boolean>) {
  for (let index = 0; index < 1000; index++) { if (await ready()) return; await new Promise(resolve => setTimeout(resolve, 1)); }
  throw new Error('Synthetic ordering barrier timed out');
}
function triage(report: ReviewReport) { return { schemaVersion: 1, reportId: report.body.reportId, attemptId: report.body.attemptId, identityDigest: report.receipt.identityDigest, dispositions: [] }; }
async function ledger(env: Awaited<ReturnType<typeof setup>>) { return validateAttempt(JSON.parse(await readFile(join(env.stateRoot, `${env.request.attemptId}.attempt.json`), 'utf8'))); }

describe('live HTTP through actual isolated SDK children, no real credentials or network', () => {
  it('live filing traverses real SDK children, reserves before HTTP, settles native usage and can verify0 only with filing authority', async () => {
    const env = await setup('filing');
    const http = intercept(async id => {
      const state = await ledger(env);
      expect(state.reservations.filter(item => item.state === 'reserved').length).toBeGreaterThan(0);
      expect(state.reservations.every(item => item.reservedUsd === .5075)).toBe(true);
      return Response.json(reply(id));
    });
    const result = await reviewLive(env.request, env.stateRoot, env.approvalPath);
    expect(result.exit, JSON.stringify(result.report.body.lenses)).toBe(0); expect(http.posts).toBe(2);
    expect(result.report.body.execution?.mode).toBe('live'); expect(result.report.body.identity.authority?.approvalDigest).toBe(hash(env.approval));
    expect(Object.values(result.report.body.lenses).every(lens => lens.calls?.[0]?.requestedUpstream === 'google-vertex/global')).toBe(true);
    const state = await ledger(env); expect(state.reservations.every(item => item.state === 'settled' && item.observation?.costUsd === .00001)).toBe(true);
    expect(JSON.stringify(result)).not.toContain('synthetic-key-not-real');
    expect(await verify(result.report, triage(result.report), env.current, env.approvalPath, env.stateRoot)).toBe(0);
    await expect(verify(result.report, triage(result.report), env.current)).rejects.toThrow('approval');
    const stale = structuredClone(result.report.body); stale.identity.runtimeHash = 'b'.repeat(64);
    await expect(verify(sealReport(stale), triage(sealReport(stale)), env.current, env.approvalPath, env.stateRoot)).rejects.toThrow('Stale');
    await put(env.request.repo, 'dirty.ts', 'uncommitted');
    await expect(verify(result.report, triage(result.report), env.current, env.approvalPath, env.stateRoot)).rejects.toMatchObject({ code: 21 });
  });
  it('transport failure closes sibling dispatch before delayed worker exit', async () => {
    const env = await setup('filing'); dispatchRace.delayExit = true; let riskRequests = 0; let postsAfterFailure = 0;
    intercept(async (id, init) => {
      if (String(init.body).includes('Lens: correctness')) {
        await wait(async () => (await ledger(env)).reservations.some(item => item.lens === 'contracts-risk' && item.state === 'settled'));
        return new Response('{}', { status: 503 });
      }
      riskRequests++;
      if (dispatchRace.failureObserved) postsAfterFailure++;
      if (riskRequests === 2) await wait(() => dispatchRace.failureObserved);
      if (riskRequests < 3) return Response.json({ ...reply(id), choices: [{ index: 0, finish_reason: 'tool_calls', message: { role: 'assistant', content: null,
        tool_calls: [{ id: 'read-' + id, type: 'function', function: { name: 'read_git', arguments: JSON.stringify({ revision: 'head', path: 'src/a.ts', start: 1, end: 1 }) } }] } }] });
      return Response.json(reply(id));
    });
    const result = await reviewLive(env.request, env.stateRoot, env.approvalPath);
    expect(result.exit).toBe(20); expect(dispatchRace.failureObserved).toBe(true); expect(postsAfterFailure).toBe(0);
    expect((await ledger(env)).reservations.some(item => item.state === 'uncertain')).toBe(true);
    expect(dispatchRace.pids).toHaveLength(2); for (const pid of dispatchRace.pids) expect(() => process.kill(pid, 0)).toThrow();
    await expect(verify(result.report, triage(result.report), env.current, env.approvalPath, env.stateRoot)).rejects.toMatchObject({ code: 20 });
  });
  it('HTTP error headers close sibling admission while the error body stalls', async () => {
    const env = await setup('filing'); let errorSent = false; let riskRequests = 0;
    intercept(async (id, init) => {
      if (String(init.body).includes('Lens: correctness')) {
        // Fail only once the sibling has a second request in flight, so its next reservation follows the error headers.
        await wait(async () => (await ledger(env)).reservations.filter(item => item.lens === 'contracts-risk').length === 2);
        errorSent = true; return new Response(new ReadableStream({ start() {} }), { status: 503 });
      }
      riskRequests++;
      if (riskRequests === 2) { await wait(() => errorSent); await new Promise(resolve => setTimeout(resolve, 50)); }
      if (riskRequests < 3) return Response.json({ ...reply(id), choices: [{ index: 0, finish_reason: 'tool_calls', message: { role: 'assistant', content: null,
        tool_calls: [{ id: 'read-' + id, type: 'function', function: { name: 'read_git', arguments: JSON.stringify({ revision: 'head', path: 'src/a.ts', start: 1, end: 1 }) } }] } }] });
      return Response.json(reply(id));
    });
    const started = Date.now(); const result = await reviewLive(env.request, env.stateRoot, env.approvalPath);
    expect(result.exit).toBe(20); expect(errorSent).toBe(true); expect(riskRequests).toBe(2);
    expect(Date.now() - started).toBeLessThan(env.request.policy.roundDeadlineMs);
    expect((await ledger(env)).reservations.some(item => item.state === 'uncertain')).toBe(true);
  });
  it.each(['missing', 'reserved', 'active-lock', 'observation'] as const)('verification rejects %s authoritative attempt state', async kind => {
    const env = await setup('filing'); intercept(); const result = await reviewLive(env.request, env.stateRoot, env.approvalPath);
    const state = await ledger(env); const path = join(env.stateRoot, env.request.attemptId + '.attempt.json');
    if (kind === 'missing') await rm(path);
    else if (kind === 'active-lock') await writeFile(join(env.stateRoot, env.request.attemptId + '.lock'), state.owner, { mode: 0o600 });
    else {
      if (kind === 'reserved') { state.rounds[0]!.status = 'reserved'; state.rounds[0]!.reportId = null; }
      else state.reservations[0]!.observation!.costUsd = .00002;
      await writeFile(path, JSON.stringify(state));
    }
    await expect(verify(result.report, triage(result.report), env.current, env.approvalPath, env.stateRoot)).rejects.toMatchObject({ code: 20 });
  });
  it('older clean report cannot authorize after a newer round has uncertain billing', async () => {
    const env = await setup('filing'); let fail = false;
    intercept(async id => fail ? new Response('{}', { status: 503 }) : Response.json(reply(id)));
    const first = await reviewLive(env.request, env.stateRoot, env.approvalPath); expect(first.exit).toBe(0); fail = true;
    const second = await reviewLive({ ...env.request, goal: 'Second goal' }, env.stateRoot, env.approvalPath);
    expect(second.exit).toBe(20); expect((await ledger(env)).rounds.at(-1)?.status).toBe('uncertain');
    await expect(verify(first.report, triage(first.report), env.current, env.approvalPath, env.stateRoot)).rejects.toMatchObject({ code: 20 });
  });
  it('only the latest settled round can authorize even when both rounds are clean', async () => {
    const env = await setup('filing'); intercept();
    const first = await reviewLive(env.request, env.stateRoot, env.approvalPath);
    const second = await reviewLive({ ...env.request, goal: 'Second goal' }, env.stateRoot, env.approvalPath); expect(second.exit).toBe(0);
    expect(await verify(second.report, triage(second.report), env.current, env.approvalPath, env.stateRoot)).toBe(0);
    await expect(verify(first.report, triage(first.report), env.current, env.approvalPath, env.stateRoot)).rejects.toMatchObject({ code: 21 });
  });
  it('verification excludes concurrent attempt owners throughout source capture', async () => {
    const env = await setup('filing'); intercept(); const result = await reviewLive(env.request, env.stateRoot, env.approvalPath);
    const capture = snapshots.captureSnapshot;
    vi.spyOn(snapshots, 'captureSnapshot').mockImplementationOnce(async (...args) => {
      const source = await capture(...args);
      const competingOwner = await ownAttempt(env.stateRoot, env.request.attemptId, env.request.policy).then(async owner => { await owner.close(); return true; }, () => false);
      expect(competingOwner).toBe(false); return source;
    });
    expect(await verify(result.report, triage(result.report), env.current, env.approvalPath, env.stateRoot)).toBe(0);
  });
  it('CLI verification uses its authoritative store, not a copied report directory', async () => {
    const env = await setup('filing'); intercept(); const result = await reviewLive(env.request, env.stateRoot, env.approvalPath);
    const backup = await mkdtemp(join(env.root, 'backup-')); const reportPath = join(backup, result.report.body.reportId + '.json'); const triagePath = join(backup, 'triage.json');
    const ledgerPath = join(env.stateRoot, env.request.attemptId + '.attempt.json');
    await writeFile(reportPath, JSON.stringify(result.report), { mode: 0o600 }); await writeFile(triagePath, JSON.stringify(triage(result.report)), { mode: 0o600 });
    await writeFile(join(backup, env.request.attemptId + '.attempt.json'), await readFile(ledgerPath), { mode: 0o600 });
    vi.spyOn(contracts, 'defaultStateRoot').mockReturnValue(env.stateRoot);
    const args = ['verify', '--report', reportPath, '--triage', triagePath, '--repo', env.request.repo, '--base', 'base', '--head', 'HEAD', '--approval', env.approvalPath];
    expect((await cli(args)).exit).toBe(0); await rm(ledgerPath); expect((await cli(args)).exit).toBe(20);
  });
  it('implicit cached tokens retain uncertainty and cannot authorize upload', async () => {
    const env = await setup('filing');
    intercept(async id => { const response = reply(id); response.usage.prompt_tokens_details.cached_tokens = 50; return Response.json(response); });
    const result = await reviewLive(env.request, env.stateRoot, env.approvalPath);
    expect(result.exit).toBe(20);
    expect((await ledger(env)).reservations.some(item => item.state === 'uncertain')).toBe(true);
    expect(Object.values(result.report.body.lenses).some(lens => lens.rejectedCalls?.some(call => call.cacheTokens === 50))).toBe(true);
    await expect(verify(result.report, triage(result.report), env.current, env.approvalPath, env.stateRoot)).rejects.toMatchObject({ code: 20 });
  });
  it('optional unchanged context cannot crowd required source out of the HTTP request', async () => {
    const env = await setup('filing');
    const text = `export const text = ${JSON.stringify('"'.repeat(750))};\n`;
    for (let index = 0; index < 9; index++) await put(env.request.repo, `src/context-${index}.test.ts`, text);
    const base = await commit(env.request.repo); await fixtureGit(env.request.repo, 'branch', '--force', 'base', base);
    await put(env.request.repo, 'src/a.ts', 'export const enabled = true;\n'); const head = await commit(env.request.repo);
    env.approval.scopes[0]!.heads = [head]; await writeFile(env.approvalPath, JSON.stringify(env.approval));
    const captured = await captureSnapshot(env.request);
    expect(captured.snapshot.payload.diff[0]?.patch).toContain('-export const enabled = false;\n+export const enabled = true;');
    expect(captured.tools.read_git('head', 'src/context-0.test.ts', 1, 2).text).toBe(text);
    const http = intercept(); const result = await reviewLive(env.request, env.stateRoot, env.approvalPath);
    expect(result.exit, JSON.stringify(result.report.body.lenses)).toBe(0); expect(http.posts).toBe(2);
    expect(http.bodies.every(body => Buffer.byteLength(body) <= env.request.policy.payloadBytes)).toBe(true);
  });
  it('ordinary review rejects approval replaced with calibration authority after purpose check', async () => {
    const env = await setup('filing'); const http = intercept(); const load = approvals.loadApproval; let reads = 0;
    vi.spyOn(contracts, 'defaultStateRoot').mockReturnValue(env.stateRoot);
    vi.spyOn(approvals, 'loadApproval').mockImplementation(async path => {
      const approved = await load(path);
      if (++reads === 1) await writeFile(path, JSON.stringify({ ...env.approval, purpose: 'calibration', rollout: null,
        calibrationBudget: { by: 'user', preparedHash: hash('synthetic-prepared'), expiresAt: Date.now() + 50000, maxCostUsd: 1.02, maxRequests: 6, maxDurationMs: 120000 } }));
      return approved;
    });
    const result = await cli(['review', '--repo', env.request.repo, '--base', 'base', '--head', 'HEAD', '--goal', env.request.goal,
      '--builder-model', env.request.builderModel, '--attempt', env.request.attemptId, '--approval', env.approvalPath]);
    expect(result.exit).toBe(30); expect(reads).toBe(2); expect(http.fetcher).not.toHaveBeenCalled();
  });
  it('approval revoked during final source capture cannot authorize upload', async () => {
    const env = await setup('filing'); intercept();
    const result = await reviewLive(env.request, env.stateRoot, env.approvalPath);
    let captures = 0; const capture = snapshots.captureSnapshot;
    vi.spyOn(snapshots, 'captureSnapshot').mockImplementation(async (...args) => {
      const source = await capture(...args);
      if (++captures === 2) await writeFile(env.approvalPath, JSON.stringify({ ...env.approval, sourceExport: false }));
      return source;
    });
    await expect(verify(result.report, triage(result.report), env.current, env.approvalPath, env.stateRoot)).rejects.toMatchObject({ code: 30 });
    expect(captures).toBe(2);
  });
  it('calibration may run, but never verifies for upload; expired/changed approval never verifies', async () => {
    const env = await setup(); const http = intercept(); const result = await reviewLive(env.request, env.stateRoot, env.approvalPath);
    expect(result.exit, JSON.stringify(result.report.body.lenses)).toBe(0);
    await expect(verify(result.report, triage(result.report), env.current, env.approvalPath, env.stateRoot)).rejects.toThrow('Calibration');
    await writeFile(env.approvalPath, JSON.stringify({ ...env.approval, expiresAt: 1 }));
    await expect(verify(result.report, triage(result.report), env.current, env.approvalPath, env.stateRoot)).rejects.toThrow('expiry');
    expect(http.posts).toBe(2);
  });
  it('approval expiring or being revoked during verification metadata fetch cannot verify0', async () => {
    const env = await setup('filing'); const http = intercept();
    const result = await reviewLive(env.request, env.stateRoot, env.approvalPath); expect(result.exit).toBe(0);
    http.fetcher.mockImplementationOnce(async () => {
      await writeFile(env.approvalPath, JSON.stringify({ ...env.approval, expiresAt: 1 }));
      return Response.json({ data: [{ id: env.approval.model, canonical_slug: env.approval.canonicalModel, context_length: 1000000 }] });
    });
    await expect(verify(result.report, triage(result.report), env.current, env.approvalPath, env.stateRoot)).rejects.toThrow('expiry');
  });
  it.each(['expiry', 'cost'] as const)('aggregate %s revocation between cases blocks the next paid effect', async change => {
    const env = await setup(); const runtime = await implementationIdentity();
    const root = join(env.root, 'cohort'); const prepared = await prepareCalibration(root, 'revocation', runtime.runtimeHash, await skillBundleHash());
    env.approval.expiresAt = Date.now() + 3600000;
    env.approval.scopes = prepared.cases.map(item => ({ repo: item.repo, baseRef: 'base', attemptId: item.attemptId, heads: [item.head] }));
    env.approval.calibrationBudget = { by: 'user', preparedHash: hash(prepared), expiresAt: Date.now() + 1800000, maxCostUsd: 12.24, maxRequests: 72, maxDurationMs: 1440000 };
    await writeFile(env.approvalPath, JSON.stringify(env.approval));
    let checkedPaths: string[] = []; let cases = 0;
    const http = intercept(async id => Response.json(reply(id, JSON.stringify({ findings: [], checkedPaths, omissions: [], requiredUnavailable: [] }))));
    await expect(calibrationCli(['run', '--root', root, '--approval', env.approvalPath, '--builder-model', 'openai/fixture-builder'], {
      runtimeHash: async () => runtime.runtimeHash, draftApproval, loadApproval,
      review: async (request, approvalPath, _expectedDigest?: string) => {
        cases++; checkedPaths = (await captureSnapshot(request)).snapshot.payload.inventory.map(item => item.path);
        const result = await reviewLive(request, env.stateRoot, approvalPath, _expectedDigest);
        expect(result.exit).toBe(0);
        if (cases > 1) throw new Error('Second case generated after aggregate revocation');
        if (change === 'expiry') env.approval.calibrationBudget!.expiresAt = 1;
        else env.approval.calibrationBudget!.maxCostUsd = 1.01;
        await writeFile(env.approvalPath, JSON.stringify(env.approval)); return result.report;
      },
    })).rejects.toMatchObject({ code: 30 });
    expect(cases).toBe(2); expect(http.posts).toBe(2);
  });
  it('approval revoked during review preflight stops before key read or generation', async () => {
    const env = await setup(); const http = intercept();
    http.fetcher.mockImplementationOnce(async () => {
      await writeFile(env.approvalPath, JSON.stringify({ ...env.approval, sourceExport: false }));
      return Response.json({ data: [{ id: env.approval.model, canonical_slug: env.approval.canonicalModel, context_length: 1000000 }] });
    });
    await expect(reviewLive(env.request, env.stateRoot, env.approvalPath)).rejects.toMatchObject({ code: 30 });
    expect(http.posts).toBe(0);
  });
  it('missing/wrong-scope authority never reaches metadata, key read or HTTP', async () => {
    const env = await setup(); const http = intercept();
    await expect(reviewLive(env.request, env.stateRoot, join(env.root, 'missing'))).rejects.toThrow('approval');
    await writeFile(env.approvalPath, JSON.stringify({ ...env.approval, keyPath: join(env.root, 'must-not-read'), scopes: [{ ...env.approval.scopes[0], attemptId: 'wrong' }] }));
    await expect(reviewLive(env.request, env.stateRoot, env.approvalPath)).rejects.toThrow('scope');
    expect(http.fetcher).not.toHaveBeenCalled();
  });
  it('SDK tools/history cross host bridge, max three generations/lens across full two-round ledger', async () => {
    const env = await setup('filing'); const perLens = new Map<string, number>();
    const http = intercept(async (id, init) => {
      const body = JSON.parse(String(init.body)) as { messages: { content: string }[] };
      const key = body.messages[0]!.content; const count = (perLens.get(key) ?? 0) + 1; perLens.set(key, count);
      if (count % 3 !== 0) {
        const raw = reply(id); raw.choices[0]!.finish_reason = 'tool_calls';
        Object.assign(raw.choices[0]!.message, { content: null, tool_calls: [{ id: `call-${id}`, type: 'function', function: { name: 'read_git', arguments: JSON.stringify({ revision: 'head', path: 'src/a.ts', start: 1, end: 1 }) } }] });
        return Response.json(raw);
      }
      return Response.json(reply(id));
    });
    const first = await reviewLive(env.request, env.stateRoot, env.approvalPath); expect(first.exit, JSON.stringify(first.report.body.lenses)).toBe(0); expect(http.posts).toBe(6);
    await put(env.request.repo, 'src/a.ts', 'export const enabled = 2;\n'); const head = await commit(env.request.repo);
    env.approval.scopes[0]!.heads.push(head); await writeFile(env.approvalPath, JSON.stringify(env.approval));
    const second = await reviewLive(env.request, env.stateRoot, env.approvalPath); expect(second.exit, JSON.stringify(second.report.body.lenses)).toBe(0); expect(http.posts).toBe(12);
    expect((await ledger(env)).reservations).toHaveLength(12);
    expect(http.bodies.some(body => body.includes('tool_call_id'))).toBe(true);
    await expect(reviewLive(env.request, env.stateRoot, env.approvalPath)).resolves.toMatchObject({ reused: true }); expect(http.posts).toBe(12);
  });
  it('actual HTTP envelope overflow stops before reservation or fetch, even when snapshot fits', async () => {
    const env = await setup(); const http = intercept();
    env.request.policy.payloadBytes = (await captureSnapshot(env.request)).snapshot.payloadBytes;
    await writeFile(env.approvalPath, JSON.stringify(env.approval));
    const result = await reviewLive(env.request, env.stateRoot, env.approvalPath); expect(result.exit).toBe(20);
    expect(http.posts).toBe(0); expect((await ledger(env)).reservations).toHaveLength(0);
    expect(Object.values(result.report.body.lenses).some(lens => lens.reason?.includes('HTTP body'))).toBe(true);
  });
  it('fourth SDK generation never reaches host HTTP even for endless valid tool use', async () => {
    const env = await setup(); const perLens = new Map<string, number>();
    const http = intercept(async (id, init) => {
      const key = JSON.parse(String(init.body)).messages[0].content as string; perLens.set(key, (perLens.get(key) ?? 0) + 1);
      const raw = reply(id); raw.choices[0]!.finish_reason = 'tool_calls';
      Object.assign(raw.choices[0]!.message, { content: null, tool_calls: [{ id: `call-${id}`, type: 'function', function: { name: 'read_git', arguments: JSON.stringify({ revision: 'head', path: 'src/a.ts', start: 1, end: 1 }) } }] });
      return Response.json(raw);
    });
    const result = await reviewLive(env.request, env.stateRoot, env.approvalPath); expect(result.exit).toBe(20);
    expect(Math.max(...perLens.values())).toBe(3); expect(http.posts).toBeLessThanOrEqual(6);
  });
  it('uncertain HTTP failure retains both holds, aborts sibling, blocks subsequent dispatch and rerun', async () => {
    const env = await setup('calibration', { roundDeadlineMs: 5000 }); let release!: () => void;
    const barrier = new Promise<void>(resolve => { release = resolve; }); let arrived = 0;
    const http = intercept(async id => { if (++arrived === 2) release(); await barrier; return id === 1 ? new Response('{}', { status: 500 }) : new Promise(() => {}); });
    const result = await reviewLive(env.request, env.stateRoot, env.approvalPath);
    expect(result.exit).toBe(20); expect(http.posts).toBe(2);
    const state = await ledger(env); expect(state.reservations.every(item => item.state === 'uncertain' && item.reservedUsd === .5075)).toBe(true);
    await expect(reviewLive(env.request, env.stateRoot, env.approvalPath)).rejects.toThrow('uncertain'); expect(http.posts).toBe(2);
  });
  it('cost beyond reservation preserves observation and uncertain hold, never schedules using underestimated actual spend', async () => {
    const env = await setup(); const http = intercept(async id => Response.json(reply(id, output, .6)));
    const result = await reviewLive(env.request, env.stateRoot, env.approvalPath); expect(result.exit).toBe(20);
    const state = await ledger(env); expect(state.reservations.some(item => item.state === 'uncertain' && item.observation?.costUsd === .6)).toBe(true);
    expect(http.posts).toBeLessThanOrEqual(2);
  });
  it('missing metadata preserves observed native billing/ID while retaining uncertain hold', async () => {
    const env = await setup(); intercept(async id => {
      const raw: Record<string, unknown> = reply(id); delete raw.openrouter_metadata; return Response.json(raw);
    });
    const result = await reviewLive(env.request, env.stateRoot, env.approvalPath); expect(result.exit).toBe(20);
    const rejected = (await ledger(env)).reservations.find(item => item.rejectedEvidence);
    expect(rejected).toMatchObject({ state: 'uncertain', reservedUsd: .5075, rejectedEvidence: { generationId: expect.stringContaining('gen-synthetic-'), costUsd: .00001, inputTokens: 100, outputTokens: 20, cacheTokens: 0 } });
    expect(Object.values(result.report.body.lenses).some(lens => lens.rejectedCalls?.[0]?.costUsd === .00001)).toBe(true);
  });
  it('valid live filing still requires evidence-backed parent triage for P2; fixed/unresolved never pass', async () => {
    const env = await setup('filing'); intercept(async (id, init) => {
      const lens = String(init.body).includes('Lens: correctness.') ? 'correctness' : 'contracts-risk';
      return Response.json(reply(id, JSON.stringify({ findings: [{ id: 'toggle', lens, severity: 'P2', path: 'src/a.ts', revision: 'head', start: 1, end: 1, quote: 'export const enabled = false;', cause: 'Toggle disabled', trigger: 'Feature enabled', impact: 'Feature unavailable', classification: 'introduced', uncertainty: null }], checkedPaths: ['src/a.ts'], omissions: [], requiredUnavailable: [] })));
    });
    const result = await reviewLive(env.request, env.stateRoot, env.approvalPath); expect(result.exit).toBe(10);
    const base = triage(result.report);
    const dispositions = Object.values(result.report.body.lenses).flatMap(lens => lens.findings.map(finding => ({ findingId: finding.id, status: 'dismissed' as const, evidence: [{ kind: 'source' as const, reference: 'src/a.ts:1', observation: 'Disabled is approved behavior in synthetic goal' }] })));
    await expect(verify(result.report, base, env.current, env.approvalPath, env.stateRoot)).rejects.toThrow('dispositions');
    expect(await verify(result.report, { ...base, dispositions }, env.current, env.approvalPath, env.stateRoot)).toBe(0);
    await expect(verify(result.report, { ...base, dispositions: dispositions.map(item => ({ ...item, status: 'unresolved', reason: 'still broken' })) }, env.current, env.approvalPath, env.stateRoot)).rejects.toThrow('Unresolved');
    await expect(verify(result.report, { ...base, dispositions: dispositions.map(item => ({ ...item, status: 'fixed', commit: 'a'.repeat(40) })) }, env.current, env.approvalPath, env.stateRoot)).rejects.toThrow('new full-diff');
  });
  it('atomic cap serializes holds, releases unused funds only on authoritative settlement', async () => {
    const env = await setup(); const attempt = await ownAttempt(env.stateRoot, 'budget-check', env.request.policy);
    const observed: CallObservation = { generationId: 'gen-budget', requestedUpstream: 'google-vertex/global', reportedProvider: 'Google', reportedModel: env.approval.model, inputTokens: 10, outputTokens: 10, cacheTokens: 0, costUsd: .001, routeDigest: 'a'.repeat(64) };
    try {
      await attempt.begin(hash('budget'));
      const [a, b] = await Promise.all([attempt.budget.reserve('correctness', .5075), attempt.budget.reserve('contracts-risk', .5075)]);
      await expect(attempt.budget.reserve('correctness', .5075)).rejects.toThrow('cap');
      await attempt.budget.settle(a!, observed);
      await expect(attempt.budget.reserve('correctness', .5075)).resolves.toBeTypeOf('string');
      const queued = attempt.budget.reserve('correctness', .000001); attempt.stopAdmission();
      await expect(queued).rejects.toThrow('stopped admission');
      await attempt.budget.settle(b!, { ...observed, generationId: 'gen-budget-second' });
      expect(attempt.state.reservations.find(item => item.id === b)?.state).toBe('settled');
    } finally { await attempt.close(); }
  });
  it('help, draft, dry-run and explicit preflight never read dedicated key or dispatch', async () => {
    const env = await setup(); const http = intercept(); await rm(env.approval.keyPath);
    const options = ['--repo', env.request.repo, '--base', 'base', '--head', 'HEAD', '--goal', 'check', '--builder-model', env.request.builderModel, '--attempt', env.request.attemptId, '--approval', env.approvalPath];
    expect((await cli(['--help'])).exit).toBe(0); expect((await cli(['draft-template'])).output).toMatchObject({ status: 'DRAFT', sourceExport: false });
    expect((await cli(['review', ...options, '--dry-run'])).exit).toBe(0); expect(http.fetcher).not.toHaveBeenCalled();
    expect((await cli(['preflight', ...options])).exit).toBe(0); expect(http.posts).toBe(0);
  });
});
