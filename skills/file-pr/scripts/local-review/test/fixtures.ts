import { DEFAULT_POLICY, hash, sealReport, type Finding, type ReceiptIdentity, type ReviewReportBody, type ReviewRequest } from '../src/contracts.js';

export const SHA_A = 'a'.repeat(40);
export const SHA_B = 'b'.repeat(40);
export function request(repo = '/synthetic'): ReviewRequest {
  return { repo, baseRef: 'base', headRef: 'HEAD', goal: 'Fix synthetic behavior', builderModel: 'openai/gpt-builder', attemptId: 'fixture-attempt', policy: { ...DEFAULT_POLICY } };
}
export function identity(): ReceiptIdentity {
  return {
    snapshot: { repo: '/synthetic', gitCommonDir: '/synthetic/.git', objectFormat: 'sha1', intendedBaseRef: 'base', intendedHeadRef: 'HEAD', base: SHA_A, head: SHA_B, mergeBase: SHA_A, baseTree: SHA_A, headTree: SHA_B, mergeBaseTree: SHA_A, surfaceDigest: hash('surface') },
    model: { provider: 'openrouter', requested: 'anthropic/claude-haiku-5.5', returned: 'anthropic/claude-haiku-5.5-20261007', endpoint: 'https://openrouter.ai/api/v1', upstream: null },
    promptHash: hash('prompt'), toolPolicyHash: hash('tools'), filterPolicyHash: hash('filters'), packageVersion: '0.1.0', sdkVersion: '1.3.0', lockHash: hash('lock'), runtimeHash: hash('runtime'), nodeVersion: process.version, reviewSettingsHash: hash('settings'), policy: { ...DEFAULT_POLICY },
  };
}
export function finding(): Finding {
  return { id: 'finding-1', lens: 'correctness', severity: 'P2', path: 'src/a.ts', revision: 'head', start: 2, end: 2, quote: 'return false;', cause: 'Condition inverted', trigger: 'Valid request', impact: 'Valid request is rejected', classification: 'introduced', uncertainty: null };
}
export function body(): ReviewReportBody {
  return {
    schemaVersion: 1, reportId: 'fixture-report', attemptId: 'fixture-attempt', round: 1, identity: identity(), status: 'complete',
    lenses: {
      correctness: { lens: 'correctness', status: 'complete', findings: [], checkedPaths: ['src/a.ts'], omissions: [], reason: null, usage: { state: 'known', requests: 1, inputTokens: 20, outputTokens: 30, cacheTokens: 0, costUsd: 0 }, startedAt: 1, endedAt: 2 },
      'contracts-risk': { lens: 'contracts-risk', status: 'complete', findings: [], checkedPaths: ['src/a.ts'], omissions: [], reason: null, usage: { state: 'known', requests: 1, inputTokens: 20, outputTokens: 30, cacheTokens: 0, costUsd: 0 }, startedAt: 1, endedAt: 2 },
    }, omissions: [], startedAt: 1, endedAt: 2,
  };
}
export function report() { return sealReport(body()); }
