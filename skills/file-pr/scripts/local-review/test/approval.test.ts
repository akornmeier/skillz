import { afterEach, describe, expect, it, vi } from 'vitest';
import { chmod, mkdtemp, realpath, rm, symlink, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { ApprovalSchema, draftApproval, loadApproval, readApprovedKey, validateAuthority } from '../src/approval.js';
import { validate } from '../src/contracts.js';
import { identity, request } from './fixtures.js';

const roots: string[] = [];
afterEach(async () => { vi.unstubAllGlobals(); await Promise.all(roots.splice(0).map(root => rm(root, { recursive: true, force: true }))); });
function authority() {
  const snapshot = identity().snapshot; const req = { ...request(), repo: snapshot.repo, baseRef: snapshot.intendedBaseRef, policy: { ...request().policy, live: true } };
  const approval = { ...draftApproval(), status: 'approved' as const, approvedBy: 'synthetic operator', expiresAt: Date.now() + 60000, sourceExport: true, keyFileRead: true,
    calibrationBudget: { by: 'user' as const, preparedHash: 'a'.repeat(64), expiresAt: Date.now() + 50000, maxCostUsd: 1.02, maxRequests: 6, maxDurationMs: 120000 },
    limits: req.policy, privacy: { zdr: true, dataCollection: 'deny' as const, consent: true, accountLoggingDisabled: true },
    scopes: [{ repo: snapshot.repo, baseRef: req.baseRef, attemptId: req.attemptId, heads: [snapshot.head] }] };
  return { snapshot, req, approval };
}
describe('explicit operator authority', () => {
  it('draft cannot enable transport; schema rejects unknown consent or fields', () => {
    const { snapshot, req } = authority();
    expect(() => validateAuthority(draftApproval(), req, snapshot, 'a'.repeat(64))).toThrow();
    expect(() => validate(ApprovalSchema, { ...draftApproval(), inferredConsent: true })).toThrow();
    expect(() => validate(ApprovalSchema, { ...draftApproval(), privacy: { zdr: true } })).toThrow();
  });
  it('scope, purpose, privacy, expiry and policy all fail before dedicated key path is touched', async () => {
    const { approval, req, snapshot } = authority();
    for (const change of [
      { expiresAt: 1 }, { calibrationBudget: { ...approval.calibrationBudget, expiresAt: 1 } }, { status: 'DRAFT' as const }, { sourceExport: false }, { keyFileRead: false },
      { privacy: { ...approval.privacy, zdr: false } }, { privacy: { ...approval.privacy, consent: false } },
      { scopes: [{ ...approval.scopes[0]!, heads: ['c'.repeat(40)] }] }, { scopes: [{ ...approval.scopes[0]!, repo: '/other' }] },
      { scopes: [{ ...approval.scopes[0]!, attemptId: 'other' }] }, { scopes: [{ ...approval.scopes[0]!, baseRef: 'other' }] },
      { limits: { ...approval.limits, schedulingCapUsd: .5 } }, { purpose: 'filing' as const },
    ]) await expect(readApprovedKey({ ...approval, ...change }, req, snapshot, 'a'.repeat(64))).rejects.toThrow(/Approval|Filing/);
  });
  it('calibration pins exactly one SHA per entry; filing binds one attempt and current rollout hash', () => {
    const { approval, req, snapshot } = authority();
    expect(() => validateAuthority(approval, req, snapshot, 'a'.repeat(64))).not.toThrow();
    expect(() => validateAuthority({ ...approval, scopes: [{ ...approval.scopes[0]!, heads: [snapshot.head, 'b'.repeat(40)] }] }, req, snapshot, 'a'.repeat(64))).toThrow();
    const filing = { ...approval, purpose: 'filing' as const, rollout: { by: 'user' as const, signoff: 'synthetic explicit signoff', evidence: ['synthetic offline qualification'], runtimeHash: 'a'.repeat(64) } };
    expect(() => validateAuthority(filing, req, snapshot, 'a'.repeat(64))).not.toThrow();
    expect(() => validateAuthority(filing, req, snapshot, 'b'.repeat(64))).toThrow('rollout');
    expect(() => validateAuthority({ ...filing, scopes: [filing.scopes[0]!, filing.scopes[0]!] }, req, snapshot, 'a'.repeat(64))).toThrow();
  });
  it('private owner file only; no env fallback; symlinks and permissive approval/key files denied', async () => {
    const root = await mkdtemp(join(await realpath(tmpdir()), 'file-pr-approval-')); roots.push(root);
    const { approval, req, snapshot } = authority(); const keyPath = join(root, 'dedicated-key'); const path = join(root, 'approval.json');
    const approved = { ...approval, keyPath };
    await writeFile(path, JSON.stringify(approved), { mode: 0o600 }); await writeFile(keyPath, 'synthetic-only-key-123456', { mode: 0o600 });
    expect(await loadApproval(path)).toEqual(approved);
    expect(await readApprovedKey(approved, req, snapshot, 'a'.repeat(64))).toBe('synthetic-only-key-123456');
    await chmod(keyPath, 0o644); await expect(readApprovedKey(approved, req, snapshot, 'a'.repeat(64))).rejects.toThrow('Dedicated');
    await chmod(path, 0o644); await expect(loadApproval(path)).rejects.toThrow('approval');
    await chmod(path, 0o600); await symlink(path, join(root, 'link')); await expect(loadApproval(join(root, 'link'))).rejects.toThrow('approval');
    await expect(loadApproval(join(root, 'absent'))).rejects.toThrow('approval');
  });
});
