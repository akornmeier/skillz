import { Type } from 'typebox';
import { DEFAULT_POLICY, ReviewError, hash, validate, type ReviewReport, type ReviewRequest } from './contracts.js';
import { CalibrationBudgetSchema, collectCalibration, gradeCalibration, loadPrepared, prepareCalibration } from './calibration.js';
import { qualifyCalibration, skillBundleHash } from './qualification.js';

export type CalibrationHost = {
  runtimeHash(): Promise<string>;
  draftApproval(): unknown;
  loadApproval(path: string): Promise<unknown>;
  review(request: ReviewRequest, approvalPath: string, approvalDigest: string): Promise<ReviewReport>;
};
const help = {
  usage: ['calibrate prepare --root PATH --id ID', 'calibrate draft --root PATH', 'calibrate run --root PATH --approval PATH --builder-model ID', 'calibrate grade --root PATH --judgments PATH', 'calibrate qualify --root PATH --judgments PATH --records PATH'],
  authority: 'prepare/draft/grade/qualify are offline. run requires explicit private calibration approval with exact prepared scopes and user-approved aggregate calibrationBudget. Draft never enables inference.',
  qualification: 'All case/profile records for both pi and claude-code, matching current skill/runtime, passed assertions and present private local evidence. Output awaits explicit user signoff, never auto-approved.',
};

/** Same handler in both harnesses. Only explicit run reaches approved review transport. */
export async function calibrationCli(args: string[], host: CalibrationHost): Promise<unknown> {
  if (!args.length || args.includes('--help')) return help;
  const command = args[0]; const keys = {
    prepare: ['root', 'id'], draft: ['root'], run: ['root', 'approval', 'builder-model'], grade: ['root', 'judgments'], qualify: ['root', 'judgments', 'records'],
  } as const;
  if (command !== 'prepare' && command !== 'draft' && command !== 'run' && command !== 'grade' && command !== 'qualify') throw new ReviewError(30, 'Expected calibrate prepare, draft, run, grade or qualify');
  const options = new Map<string, string>(); let dry = false;
  for (let index = 1; index < args.length; index++) {
    const option = args[index]!;
    if (option === '--dry-run' && !dry) { dry = true; continue; }
    const key = option.slice(2); const value = args[++index];
    if (!option.startsWith('--') || !keys[command].some(allowed => allowed === key) || options.has(key) || !value || value.startsWith('--')) throw new ReviewError(30, 'Invalid calibration option');
    options.set(key, value);
  }
  const required = (name: string) => { const value = options.get(name); if (!value) throw new ReviewError(30, 'Missing required calibration option'); return value; };
  for (const key of keys[command]) required(key);
  if (dry) return { command, dryRun: true, authorization: false, keyRead: false, generation: false };
  const root = required('root');
  if (command === 'prepare') return prepareCalibration(root, required('id'), await host.runtimeHash(), await skillBundleHash());
  if (command === 'draft') {
    const prepared = await loadPrepared(root); const template = host.draftApproval();
    if (!template || typeof template !== 'object' || Array.isArray(template)) throw new ReviewError(30, 'Invalid approval template');
    return { ...template, status: 'DRAFT', purpose: 'calibration', scopes: prepared.cases.map(item => ({ repo: item.repo, baseRef: 'base', attemptId: item.attemptId, heads: [item.head] })), calibrationBudget: { by: 'user', preparedHash: hash(prepared), expiresAt: 1, maxCostUsd: 12 * DEFAULT_POLICY.schedulingCapUsd, maxRequests: 12 * DEFAULT_POLICY.concurrency * DEFAULT_POLICY.requestsPerLens, maxDurationMs: 12 * DEFAULT_POLICY.roundDeadlineMs } };
  }
  if (command === 'grade') return gradeCalibration(root, required('judgments'));
  if (command === 'qualify') return qualifyCalibration(root, required('judgments'), required('records'), await host.runtimeHash());
  const prepared = await loadPrepared(root); const approvalPath = required('approval');
  const authority = validate(Type.Object({ status: Type.Literal('approved'), purpose: Type.Literal('calibration'), expiresAt: Type.Number(), calibrationBudget: CalibrationBudgetSchema }, { additionalProperties: true }), await host.loadApproval(approvalPath));
  const budget = authority.calibrationBudget;
  const approvalDigest = hash(authority);
  if (authority.expiresAt <= Date.now() || budget.expiresAt <= Date.now() || budget.expiresAt > authority.expiresAt || budget.preparedHash !== hash(prepared)) throw new ReviewError(30, 'Aggregate calibration authority expired or mismatched');
  const deadlineAt = Math.min(authority.expiresAt, budget.expiresAt, Date.now() + budget.maxDurationMs);
  return collectCalibration(root, { deadlineAt, maxCostUsd: budget.maxCostUsd, maxRequests: budget.maxRequests, maxDurationMs: budget.maxDurationMs, builderModel: required('builder-model'), runtimeHash: await host.runtimeHash(), skillHash: await skillBundleHash() }, request => host.review(request, approvalPath, approvalDigest));
}

