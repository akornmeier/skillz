import { DEFAULT_POLICY, ReviewError, defaultStateRoot, hash, validateRequest } from './contracts.js';
import { captureSnapshot } from './snapshot.js';
import { calibrationCli } from './calibration-cli.js';
import { draftApproval, loadApproval, validateAuthority } from './approval.js';
import { preflight } from './openrouter.js';
import { implementationIdentity, review, reviewLive, verifyFiles } from './review.js';

const help = {
  usage: ['review --repo PATH --base REF --head REF --goal TEXT --builder-model ID --attempt ID [--approval PATH]', 'verify --report PATH --triage PATH --repo PATH --base REF --head REF [--approval PATH]', 'draft-template', 'preflight --approval PATH --repo PATH --base REF --head REF --goal TEXT --builder-model ID --attempt ID', 'calibrate --help', '--help', '--dry-run'],
  setup: 'Node >=22.19, pinned package dependencies. Live review requires --approval PATH and dedicated private key file. Help/dry-run/template never read keys or dispatch. Preflight reads public metadata only. Offline fixtures are internal tests only.',
  exits: { 0: 'Complete without actionable candidates, or dry-run/help. Not push authorization.', 10: 'Complete with candidates needing parent triage.', 20: 'Incomplete, uncertain, locked or exhausted.', 21: 'Stale identity or dirty source.', 30: 'Setup/auth/identity error; simulated review cannot authorize upload.' },
  blocked: 'Live route/privacy, source export, scoped key access, model availability, token/output semantics and rates/budget require approval and verification.',
};
export async function cli(args: string[]): Promise<{ exit: number; output: unknown; diagnostic?: string }> {
  try {
    if (args[0] === 'calibrate') return { exit: 0, output: await calibrationCli(args.slice(1), {
      runtimeHash: async () => (await implementationIdentity()).runtimeHash,
      draftApproval, loadApproval,
      review: async (request, approvalPath, approvalDigest) => (await reviewLive(request, defaultStateRoot(), approvalPath, approvalDigest)).report,
    }) };
    if (args.includes('--help') || args.length === 0) return { exit: 0, output: help };
    const command = args[0];
    if (command === 'draft-template' && args.length === 1) return { exit: 0, output: draftApproval() };
    if (command !== 'review' && command !== 'verify' && command !== 'preflight') throw new ReviewError(30, 'Expected review, verify, preflight or draft-template');
    const values = new Map<string, string>(); let dry = false;
    const allowed = new Set(command !== 'verify' ? ['repo', 'base', 'head', 'goal', 'builder-model', 'attempt', 'approval'] : ['report', 'triage', 'repo', 'base', 'head', 'approval']);
    for (let index = 1; index < args.length; index++) {
      const argument = args[index]!; if (argument === '--dry-run') { dry = true; continue; }
      const key = argument.slice(2); const value = args[++index];
      if (!argument.startsWith('--') || !allowed.has(key) || values.has(key) || !value || value.startsWith('--')) throw new ReviewError(30, 'Invalid or duplicate CLI option');
      values.set(key, value);
    }
    const required = (name: string) => { const value = values.get(name); if (!value) throw new ReviewError(30, 'Missing required CLI option'); return value; };
    const current = { repo: required('repo'), baseRef: required('base'), headRef: required('head') };
    if (command === 'verify') {
      const report = required('report'); const triage = required('triage');
      if (dry) return { exit: 0, output: { command, dryRun: true, live: false, authorization: false, operation: 'Verify current clean source, runtime identity and parent evidence. Simulated evidence always rejected.' } };
      await verifyFiles(report, triage, current, values.get('approval')); return { exit: 0, output: { verified: true } };
    }
    const request = validateRequest({ ...current, goal: required('goal'), builderModel: required('builder-model'), attemptId: required('attempt'), policy: { ...DEFAULT_POLICY } });
    if (dry) {
      const source = await captureSnapshot(request);
      return { exit: 0, output: { command, dryRun: true, live: false, authorization: false, snapshot: source.snapshot.identity, runtime: await implementationIdentity(), omissions: source.snapshot.omissions } };
    }
    if (command === 'preflight') {
      const approval = await loadApproval(required('approval'));
      const liveRequest = { ...request, policy: { ...request.policy, live: true } };
      const source = await captureSnapshot(liveRequest);
      validateAuthority(approval, liveRequest, source.snapshot.identity, (await implementationIdentity()).runtimeHash);
      return { exit: 0, output: { preflight: await preflight(approval, liveRequest.policy, AbortSignal.timeout(request.policy.roundDeadlineMs)), authorization: false, keyRead: false } };
    }
    const approval = values.has('approval') ? await loadApproval(required('approval')) : undefined;
    if (approval?.purpose === 'calibration') throw new ReviewError(30, 'Use calibrate run to enforce aggregate calibration authority');
    const result = approval ? await reviewLive(request, defaultStateRoot(), required('approval'), hash(approval)) : await review(request, defaultStateRoot());
    return { exit: result.exit, output: result };
  } catch (error) {
    const exit = error instanceof ReviewError ? error.code : 30;
    // Do not print source, argv, credentials, filesystem paths or raw SDK/provider diagnostics.
    const diagnostic = error instanceof ReviewError ? error.message : 'Review setup failed';
    return { exit, output: { error: true, exit, authorization: false }, diagnostic };
  }
}
if (import.meta.main) {
  const result = await cli(process.argv.slice(2));
  process.stdout.write(`${JSON.stringify(result.output)}\n`);
  if (result.diagnostic) process.stderr.write(`${result.diagnostic}\n`);
  process.exitCode = result.exit;
}
