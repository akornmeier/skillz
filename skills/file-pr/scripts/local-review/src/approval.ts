import { constants } from 'node:fs';
import { lstat, open, realpath } from 'node:fs/promises';
import { isAbsolute, join, parse } from 'node:path';
import { Type, type Static } from 'typebox';
import { DEFAULT_POLICY, PolicySchema, ReviewError, hash, validate, type ReviewRequest, type SnapshotIdentity } from './contracts.js';

const text = Type.String({ minLength: 1, maxLength: 4096, pattern: '\\S' });
const digest = Type.String({ pattern: '^[a-f0-9]{64}$' });
const sha = Type.String({ pattern: '^(?:[a-f0-9]{40}|[a-f0-9]{64})$' });
export const ApprovalSchema = Type.Object({
  schemaVersion: Type.Literal(1), status: Type.Union([Type.Literal('DRAFT'), Type.Literal('approved')]),
  purpose: Type.Union([Type.Literal('calibration'), Type.Literal('filing')]),
  approvedBy: text, expiresAt: Type.Integer({ minimum: 1 }),
  provider: Type.Literal('openrouter'), model: Type.Literal('anthropic/claude-haiku-5.5'), canonicalModel: Type.Literal('anthropic/claude-haiku-5.5-20261007'),
  requestedUpstream: Type.String({ minLength: 1, maxLength: 256, pattern: '^[a-z0-9-]+(?:/[a-z0-9-]+)*$' }), reportedProvider: text,
  sourceExport: Type.Boolean(), keyFileRead: Type.Boolean(), keyPath: text,
  privacy: Type.Object({ zdr: Type.Boolean(), dataCollection: Type.Literal('deny'), consent: Type.Boolean(), accountLoggingDisabled: Type.Boolean() }, { additionalProperties: false }),
  limits: PolicySchema,
  maxInputUsdPerToken: Type.Number({ exclusiveMinimum: 0, maximum: 0.0000005 }),
  maxOutputUsdPerToken: Type.Number({ exclusiveMinimum: 0, maximum: 0.0000025 }),
  scopes: Type.Array(Type.Object({ repo: text, baseRef: text, attemptId: text, heads: Type.Array(sha, { minItems: 1, maxItems: 2, uniqueItems: true }) }, { additionalProperties: false }), { minItems: 1, maxItems: 12 }),
  rollout: Type.Union([Type.Null(), Type.Object({ by: Type.Literal('user'), signoff: text, evidence: Type.Array(text, { minItems: 1, maxItems: 32 }), runtimeHash: digest }, { additionalProperties: false })]),
}, { additionalProperties: false });
export type Approval = Static<typeof ApprovalSchema>;

/** No symlink components, no Git ancestors, exact permissions and ownership. Never discovers credentials. */
export async function readOperatorFile(path: string, maxBytes: number): Promise<string> {
  if (!isAbsolute(path) || await realpath(path) !== path) throw new ReviewError(30, 'Operator file must be canonical and private');
  let current = parse(path).root;
  for (const part of path.slice(current.length).split('/')) {
    current = join(current, part);
    const info = await lstat(current);
    if (info.isSymbolicLink() || (current === path && !info.isFile())) throw new ReviewError(30, 'Non-file or symlink operator file denied');
    if (current !== path) {
      try { await lstat(join(current, '.git')); throw new ReviewError(30, 'Operator file must be outside Git'); }
      catch (error) { if (!(error instanceof Error && 'code' in error && error.code === 'ENOENT')) throw error; }
    }
  }
  const file = await open(path, constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_NONBLOCK);
  try {
    const info = await file.stat();
    if (!info.isFile() || info.nlink !== 1 || (info.mode & 0o777) !== 0o600 || (process.getuid && info.uid !== process.getuid()) || info.size > maxBytes) throw new ReviewError(30, 'Unsafe operator file');
    return await file.readFile('utf8');
  } finally { await file.close(); }
}
export async function loadApproval(path: string): Promise<Approval> {
  try { return validate(ApprovalSchema, JSON.parse(await readOperatorFile(path, 65536)) as unknown); }
  catch { throw new ReviewError(30, 'Missing or invalid private approval'); }
}
export function validateAuthority(approval: Approval, request: ReviewRequest, snapshot: SnapshotIdentity, runtimeHash: string): void {
  validate(ApprovalSchema, approval);
  if (approval.status !== 'approved' || approval.expiresAt <= Date.now() || !approval.sourceExport || !approval.keyFileRead
    || !approval.privacy.consent || !approval.privacy.zdr || !approval.privacy.accountLoggingDisabled || !isAbsolute(approval.keyPath)
    || !request.policy.live || hash(approval.limits) !== hash(request.policy)) throw new ReviewError(30, 'Approval authority, expiry or limits denied');
  const scope = approval.scopes.find(scope => scope.repo === snapshot.repo && scope.baseRef === request.baseRef && scope.attemptId === request.attemptId && scope.heads.includes(snapshot.head));
  if (!scope || (approval.purpose === 'calibration' && approval.scopes.some(scope => scope.heads.length !== 1))) throw new ReviewError(30, 'Approval scope denied');
  if (approval.purpose === 'filing' && (approval.scopes.length !== 1 || !approval.rollout || approval.rollout.runtimeHash !== runtimeHash)) throw new ReviewError(30, 'Filing requires current user rollout signoff');
}
export async function readApprovedKey(approval: Approval, request: ReviewRequest, snapshot: SnapshotIdentity, runtimeHash: string): Promise<string> {
  validateAuthority(approval, request, snapshot, runtimeHash);
  // Intentionally no env/auth fallback.
  try {
    const key = (await readOperatorFile(approval.keyPath, 4096)).trim();
    if (!/^[A-Za-z0-9_-]{16,4096}$/.test(key)) throw new Error();
    return key;
  } catch { throw new ReviewError(30, 'Dedicated private key unavailable'); }
}
export function draftApproval(): Approval {
  return { schemaVersion: 1, status: 'DRAFT', purpose: 'calibration', approvedBy: 'OPERATOR REQUIRED', expiresAt: 1,
    provider: 'openrouter', model: 'anthropic/claude-haiku-5.5', canonicalModel: 'anthropic/claude-haiku-5.5-20261007',
    requestedUpstream: 'operator-required', reportedProvider: 'OPERATOR REQUIRED', sourceExport: false, keyFileRead: false,
    keyPath: '/REPLACE/dedicated-private-key', privacy: { zdr: false, dataCollection: 'deny', consent: false, accountLoggingDisabled: false },
    limits: { ...DEFAULT_POLICY, live: true }, maxInputUsdPerToken: 0.0000005, maxOutputUsdPerToken: 0.0000025,
    scopes: [{ repo: '/REPLACE/canonical-repository', baseRef: 'REPLACE', attemptId: 'REPLACE', heads: ['0'.repeat(40)] }], rollout: null };
}
