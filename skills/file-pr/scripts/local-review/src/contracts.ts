import { createHash, randomUUID } from 'node:crypto';
import { constants } from 'node:fs';
import { chmod, lstat, mkdir, open, readFile, realpath, rename, rm } from 'node:fs/promises';
import { homedir } from 'node:os';
import { dirname, isAbsolute, join, parse, relative, resolve } from 'node:path';
import { Type, type Static, type TSchema } from 'typebox';
import { Value } from 'typebox/value';

const text = Type.String({ minLength: 1, maxLength: 4096, pattern: '\\S' });
const sha = Type.String({ pattern: '^(?:[a-f0-9]{40}|[a-f0-9]{64})$' });
const digest = Type.String({ pattern: '^[a-f0-9]{64}$' });
const id = Type.String({ pattern: '^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$' });
export const RevisionSchema = Type.Union([Type.Literal('base'), Type.Literal('head')]);
export const LensSchema = Type.Union([Type.Literal('correctness'), Type.Literal('contracts-risk')]);
export const PathSchema = Type.String({ minLength: 1, maxLength: 1024 });
export const LineSpanSchema = Type.Object({ start: Type.Integer({ minimum: 1 }), end: Type.Integer({ minimum: 1 }) }, { additionalProperties: false });

// Scheduling ceilings, not billing authorization. Live mode requires separate operator authority.
export const PolicySchema = Type.Object({
  live: Type.Boolean(),
  maxRounds: Type.Integer({ minimum: 1, maximum: 2 }),
  concurrency: Type.Literal(2),
  requestsPerLens: Type.Integer({ minimum: 1, maximum: 3 }),
  toolsPerLens: Type.Integer({ minimum: 1, maximum: 8 }),
  roundDeadlineMs: Type.Integer({ minimum: 1, maximum: 120_000 }),
  maxOutputTokens: Type.Integer({ minimum: 1, maximum: 3000 }),
  attemptRequests: Type.Integer({ minimum: 1, maximum: 12 }),
  schedulingCapUsd: Type.Number({ exclusiveMinimum: 0, maximum: 1.02 }),
  maxCandidates: Type.Integer({ minimum: 1, maximum: 8 }),
  maxChangedFiles: Type.Integer({ minimum: 1, maximum: 60 }),
  maxDiffBytes: Type.Integer({ minimum: 1, maximum: 131_072 }),
  readLines: Type.Integer({ minimum: 1, maximum: 200 }),
  readBytes: Type.Integer({ minimum: 1, maximum: 8192 }),
  searchHits: Type.Integer({ minimum: 1, maximum: 50 }),
  searchBytes: Type.Integer({ minimum: 1, maximum: 8192 }),
  payloadBytes: Type.Integer({ minimum: 1, maximum: 32768 }),
  maxBlobBytes: Type.Integer({ minimum: 1, maximum: 131_072 }),
  maxTreeEntries: Type.Integer({ minimum: 1, maximum: 20_000 }),
  maxScanBytes: Type.Integer({ minimum: 1, maximum: 16_777_216 }),
  gitOutputBytes: Type.Integer({ minimum: 1024, maximum: 8_388_608 }),
  gitTimeoutMs: Type.Integer({ minimum: 1, maximum: 10_000 }),
  contextLines: Type.Integer({ minimum: 1, maximum: 20 }),
}, { additionalProperties: false });
export type Policy = Static<typeof PolicySchema>;
export const DEFAULT_POLICY: Readonly<Policy> = Object.freeze({
  live: false, maxRounds: 2, concurrency: 2, requestsPerLens: 3, toolsPerLens: 8,
  roundDeadlineMs: 120_000, maxOutputTokens: 3000, attemptRequests: 12, schedulingCapUsd: 1.02,
  maxCandidates: 8, maxChangedFiles: 60, maxDiffBytes: 131_072, readLines: 200, readBytes: 8192,
  searchHits: 50, searchBytes: 8192, payloadBytes: 32768, maxBlobBytes: 131_072,
  maxTreeEntries: 20_000, maxScanBytes: 16_777_216, gitOutputBytes: 8_388_608,
  gitTimeoutMs: 10_000, contextLines: 8,
});
export const ReviewRequestSchema = Type.Object({
  repo: text, baseRef: text, headRef: text, goal: text,
  builderModel: text, attemptId: id, policy: PolicySchema,
}, { additionalProperties: false });
export type ReviewRequest = Static<typeof ReviewRequestSchema>;

export const SnapshotIdentitySchema = Type.Object({
  repo: text, gitCommonDir: text, objectFormat: Type.Union([Type.Literal('sha1'), Type.Literal('sha256')]),
  intendedBaseRef: text, intendedHeadRef: text,
  base: sha, head: sha, mergeBase: sha, baseTree: sha, headTree: sha, mergeBaseTree: sha,
  surfaceDigest: digest,
}, { additionalProperties: false });
export type SnapshotIdentity = Static<typeof SnapshotIdentitySchema>;
export const ModelIdentitySchema = Type.Object({
  provider: Type.Literal('openrouter'), requested: Type.Literal('anthropic/claude-haiku-5.5'),
  returned: Type.Union([Type.Literal('anthropic/claude-haiku-5.5'), Type.Literal('anthropic/claude-haiku-5.5-20261007')]),
  endpoint: Type.Literal('https://openrouter.ai/api/v1'), upstream: Type.Union([text, Type.Null()]),
}, { additionalProperties: false });
// Preserve even rejected response identities in incomplete receipts.
export const ModelObservationSchema = Type.Object({ provider: text, requested: text, returned: text, endpoint: text }, { additionalProperties: false });
export const ReceiptIdentitySchema = Type.Object({
  snapshot: SnapshotIdentitySchema, model: ModelIdentitySchema,
  promptHash: digest, toolPolicyHash: digest, filterPolicyHash: digest,
  packageVersion: Type.Literal('0.1.0'), sdkVersion: Type.Literal('1.3.0'),
  lockHash: digest, runtimeHash: digest, nodeVersion: text,
  reviewSettingsHash: digest, policy: PolicySchema,
  authority: Type.Optional(Type.Object({ approvalDigest: digest, admissionDigest: digest, purpose: Type.Union([Type.Literal('calibration'), Type.Literal('filing')]) }, { additionalProperties: false })),
}, { additionalProperties: false });
export type ReceiptIdentity = Static<typeof ReceiptIdentitySchema>;

export const FindingSchema = Type.Object({
  id, lens: LensSchema,
  severity: Type.Union([Type.Literal('P0'), Type.Literal('P1'), Type.Literal('P2'), Type.Literal('P3')]),
  path: PathSchema, revision: RevisionSchema, start: Type.Integer({ minimum: 1 }), end: Type.Integer({ minimum: 1 }),
  quote: text, cause: text, trigger: text, impact: text,
  classification: Type.Union([Type.Literal('introduced'), Type.Literal('pre-existing'), Type.Literal('uncertain')]),
  uncertainty: Type.Union([text, Type.Null()]),
}, { additionalProperties: false });
export type Finding = Static<typeof FindingSchema>;
export const OmissionSchema = Type.Object({
  path: PathSchema, revision: RevisionSchema, reason: text, changed: Type.Boolean(), semantic: Type.Boolean(),
}, { additionalProperties: false });
export type Omission = Static<typeof OmissionSchema>;
export const CallObservationSchema = Type.Object({
  generationId: text, requestedUpstream: text, reportedProvider: text, reportedModel: text,
  inputTokens: Type.Integer({ minimum: 0 }), outputTokens: Type.Integer({ minimum: 0 }), cacheTokens: Type.Integer({ minimum: 0 }), costUsd: Type.Number({ minimum: 0 }),
  routeDigest: digest,
}, { additionalProperties: false });
export type CallObservation = Static<typeof CallObservationSchema>;
export const CallEvidenceSchema = Type.Partial(CallObservationSchema);
export type CallEvidence = Static<typeof CallEvidenceSchema>;
const UsageSchema = Type.Union([
  Type.Object({ state: Type.Literal('known'), requests: Type.Integer({ minimum: 0, maximum: 3 }), inputTokens: Type.Integer({ minimum: 0 }), outputTokens: Type.Integer({ minimum: 0 }), cacheTokens: Type.Integer({ minimum: 0 }), costUsd: Type.Number({ minimum: 0 }) }, { additionalProperties: false }),
  Type.Object({ state: Type.Union([Type.Literal('unavailable'), Type.Literal('uncertain')]), requests: Type.Integer({ minimum: 0, maximum: 3 }), reason: text }, { additionalProperties: false }),
]);
export const LensResultSchema = Type.Object({
  lens: LensSchema,
  identities: Type.Optional(Type.Array(ModelIdentitySchema, { maxItems: 3 })),
  calls: Type.Optional(Type.Array(CallObservationSchema, { maxItems: 3 })),
  rejectedCalls: Type.Optional(Type.Array(CallEvidenceSchema, { maxItems: 3 })),
  observedModels: Type.Optional(Type.Array(ModelObservationSchema, { maxItems: 3 })),
  contextGaps: Type.Optional(Type.Array(text, { maxItems: 100 })),
  status: Type.Union([Type.Literal('complete'), Type.Literal('incomplete'), Type.Literal('setup-error'), Type.Literal('aborted')]),
  findings: Type.Array(FindingSchema, { maxItems: 8 }), checkedPaths: Type.Array(PathSchema, { maxItems: 20_000, uniqueItems: true }),
  omissions: Type.Array(OmissionSchema, { maxItems: 20_000 }), reason: Type.Union([text, Type.Null()]),
  usage: UsageSchema, startedAt: Type.Integer({ minimum: 0 }), endedAt: Type.Integer({ minimum: 0 }),
}, { additionalProperties: false });
export type LensResult = Static<typeof LensResultSchema>;
export const ReviewReportBodySchema = Type.Object({
  schemaVersion: Type.Literal(1), reportId: id, attemptId: id, round: Type.Integer({ minimum: 1, maximum: 2 }),
  identity: ReceiptIdentitySchema,
  execution: Type.Optional(Type.Object({
    mode: Type.Union([Type.Literal('simulated'), Type.Literal('live')]), goal: text, builderModel: text,
    provenance: Type.Array(Type.Object({ canonicalId: id, findingIds: Type.Array(id, { minItems: 1, maxItems: 16 }) }, { additionalProperties: false }), { maxItems: 16 }),
  }, { additionalProperties: false })),
  status: Type.Union([Type.Literal('complete'), Type.Literal('incomplete'), Type.Literal('setup-error')]),
  lenses: Type.Object({ correctness: LensResultSchema, 'contracts-risk': LensResultSchema }, { additionalProperties: false }),
  omissions: Type.Array(OmissionSchema, { maxItems: 20_000 }),
  startedAt: Type.Integer({ minimum: 0 }), endedAt: Type.Integer({ minimum: 0 }),
}, { additionalProperties: false });
export type ReviewReportBody = Static<typeof ReviewReportBodySchema>;
export const ReviewReportSchema = Type.Object({
  body: ReviewReportBodySchema,
  receipt: Type.Object({ identityDigest: digest, reportDigest: digest }, { additionalProperties: false }),
}, { additionalProperties: false });
export type ReviewReport = Static<typeof ReviewReportSchema>;
const EvidenceSchema = Type.Array(Type.Object({
  kind: Type.Union([Type.Literal('source'), Type.Literal('test')]), reference: text, observation: text,
}, { additionalProperties: false }), { minItems: 1, maxItems: 16 });
export const DispositionSchema = Type.Union([
  Type.Object({ findingId: id, status: Type.Literal('dismissed'), evidence: EvidenceSchema }, { additionalProperties: false }),
  Type.Object({ findingId: id, status: Type.Literal('fixed'), commit: sha, evidence: EvidenceSchema }, { additionalProperties: false }),
  Type.Object({ findingId: id, status: Type.Literal('unresolved'), reason: text, evidence: EvidenceSchema }, { additionalProperties: false }),
  Type.Object({ findingId: id, status: Type.Literal('user-approved-risk'), evidence: EvidenceSchema,
    approval: Type.Object({ by: Type.Literal('user'), reason: text, recordedAt: Type.Integer({ minimum: 0 }), attemptId: id }, { additionalProperties: false }),
  }, { additionalProperties: false }),
]);
export const ParentTriageSchema = Type.Object({
  schemaVersion: Type.Literal(1), reportId: id, attemptId: id, identityDigest: digest,
  dispositions: Type.Array(DispositionSchema, { maxItems: 16 }),
}, { additionalProperties: false });
export type ParentTriage = Static<typeof ParentTriageSchema>;
export const AttemptStateSchema = Type.Object({
  schemaVersion: Type.Literal(1), attemptId: id, owner: id,
  rounds: Type.Array(Type.Object({
    round: Type.Integer({ minimum: 1, maximum: 2 }), identityDigest: digest,
    status: Type.Union([Type.Literal('reserved'), Type.Literal('settled'), Type.Literal('uncertain')]),
    reportId: Type.Union([id, Type.Null()]),
  }, { additionalProperties: false }), { maxItems: 2 }),
  reservations: Type.Array(Type.Object({
    id, round: Type.Integer({ minimum: 1, maximum: 2 }), lens: LensSchema,
    state: Type.Union([Type.Literal('reserved'), Type.Literal('settled'), Type.Literal('uncertain')]),
    reservedUsd: Type.Number({ minimum: 0, maximum: 1.02 }),
    observation: Type.Optional(CallObservationSchema),
    rejectedEvidence: Type.Optional(CallEvidenceSchema),
  }, { additionalProperties: false }), { maxItems: 12 }),
}, { additionalProperties: false });
export type AttemptState = Static<typeof AttemptStateSchema>;
export const EXIT = Object.freeze({ complete: 0, candidates: 10, incomplete: 20, stale: 21, setup: 30 } as const);

export class ReviewError extends Error {
  constructor(readonly code: 20 | 21 | 30, message: string) { super(message); this.name = 'ReviewError'; }
}

export function validate<T extends TSchema>(schema: T, input: unknown): Static<T> {
  if (!Value.Check(schema, input)) throw new ReviewError(20, 'Invalid review contract');
  return input;
}
export function parseJson<T extends TSchema>(schema: T, json: string): Static<T> {
  let input: unknown;
  try { input = JSON.parse(json); } catch { throw new ReviewError(20, 'Malformed JSON'); }
  return validate(schema, input);
}
// Model-chosen keys appear only when they look like short identifiers or indexes; values never do.
const keyName = (key: string) => /^(?:\d{1,6}|[A-Za-z_][A-Za-z0-9_-]{0,40})$/.test(key) ? key : '[key]';
export function schemaLocation(schema: TSchema, input: unknown): string {
  // Skip per-branch union errors and the false-schema twin of each additionalProperties error.
  const error = Value.Errors(schema, input).find(item => item.keyword !== 'boolean' && !/\/anyOf\/\d+/.test(item.schemaPath));
  if (!error) return 'invalid';
  const path = error.instancePath.split('/').slice(1).map(segment => keyName(segment.replace(/~1/g, '/').replace(/~0/g, '~')));
  const extra = (error.params as { additionalProperties?: unknown }).additionalProperties;
  const detail = error.keyword === 'additionalProperties' && Array.isArray(extra) ? `unexpected key ${extra.slice(0, 3).map(key => keyName(String(key))).join(', ')}` : error.message;
  return `/${path.join('/')} ${detail}`;
}
export function canonicalJson(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`;
  if (value !== null && typeof value === 'object') {
    return `{${Object.entries(value).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0).map(([k, v]) => `${JSON.stringify(k)}:${canonicalJson(v)}`).join(',')}}`;
  }
  const json = JSON.stringify(value);
  if (json === undefined || (typeof value === 'number' && !Number.isFinite(value))) throw new ReviewError(20, 'Non-JSON identity');
  return json;
}
export function hash(value: unknown): string { return createHash('sha256').update(canonicalJson(value)).digest('hex'); }
export function hashBytes(value: string | Uint8Array): string { return createHash('sha256').update(value).digest('hex'); }
export function safePath(path: string): boolean {
  return path.length > 0 && path.length <= 1024 && !isAbsolute(path) && !/^[a-zA-Z]:/.test(path)
    && !/[\\\x00-\x1f\x7f]/.test(path) && !path.split('/').some(part => !part || part === '.' || part === '..' || part.toLowerCase() === '.git');
}
export function validateRequest(input: unknown): ReviewRequest {
  const request = validate(ReviewRequestSchema, input);
  for (const ref of [request.baseRef, request.headRef]) {
    if (ref.startsWith('-') || /[\x00-\x20\x7f~^:?*\[\\]/.test(ref) || ref.includes('..') || ref.includes('@{')) throw new ReviewError(30, 'Unsafe revision; use a ref name or commit ID');
  }
  if (/haiku[- /]?5[.-]?5/i.test(request.builderModel)) throw new ReviewError(30, 'Builder is not independent of Haiku 5.5');
  if (/^(unknown|unspecified)$/i.test(request.builderModel.trim())) throw new ReviewError(30, 'Builder identity requires explicit user decision');
  return request;
}
export function actionable(finding: Finding): boolean { return finding.severity !== 'P3'; }

// Quote matching proves location only, not truth of the allegation. Base means merge-base.
// Rejections name the failed check with line numbers and counts only; quote and source text never enter reports.
export function validateFindingEvidence(input: unknown, source: string, changedSpans: readonly Static<typeof LineSpanSchema>[]): Finding {
  const finding = validate(FindingSchema, input);
  const lines = source.split('\n');
  const range = `range ${finding.start}-${finding.end}`;
  const unsupported = (detail: string) => new ReviewError(20, `Unsupported finding evidence: ${detail}`);
  if (!safePath(finding.path)) throw unsupported('unsafe path');
  if (finding.end < finding.start) throw unsupported(`${range} is inverted`);
  if (finding.end > lines.length) throw unsupported(`${range} ends past line ${lines.length}`);
  const cited = lines.slice(finding.start - 1, finding.end);
  if (cited.join('\n') !== finding.quote) throw unsupported(`quote mismatch at ${range}: ${quoteMismatch(finding.quote, cited, source)}`);
  if (!changedSpans.some(span => finding.start <= span.end && finding.end >= span.start)) throw unsupported(`${range} misses the changed lines`);
  if (finding.classification === 'uncertain' && !finding.uncertainty) throw new ReviewError(20, 'Missing uncertainty reason');
  return finding;
}
function quoteMismatch(quote: string, cited: string[], source: string): string {
  // One aligned search: the quote must start and end on line boundaries.
  const found = `\n${source}\n`.indexOf(`\n${quote}\n`);
  const quoted = quote.split('\n');
  if (found !== -1) { const first = source.slice(0, found).split('\n').length; return `exact text is at lines ${first}-${first + quoted.length - 1}`; }
  if (quoted.length === cited.length) {
    if (quoted.every((line, index) => /^[-+ ]/.test(line) && line.slice(1) === cited[index])) return 'keeps diff markers';
    if (quoted.every((line, index) => line.trim() === cited[index]!.trim())) return 'whitespace differs';
  }
  const fragment = quote.trim();
  if (cited.join('\n').includes(fragment)) return 'part of the cited lines';
  return source.includes(fragment) ? 'part of other lines' : `not in file (quote ${quoted.length} lines, range ${cited.length})`;
}
function validateBody(input: unknown): ReviewReportBody {
  const body = validate(ReviewReportBodySchema, input);
  const snapshot = body.identity.snapshot;
  const objectLength = snapshot.objectFormat === 'sha256' ? 64 : 40;
  if (!isAbsolute(snapshot.repo) || !isAbsolute(snapshot.gitCommonDir)
    || [snapshot.base, snapshot.head, snapshot.mergeBase, snapshot.baseTree, snapshot.headTree, snapshot.mergeBaseTree].some(value => value.length !== objectLength)) throw new ReviewError(20, 'Invalid repository/object identity');
  if (body.endedAt < body.startedAt) throw new ReviewError(20, 'Invalid report timing');
  const ids = new Set<string>();
  for (const lens of ['correctness', 'contracts-risk'] as const) {
    const result = body.lenses[lens];
    if (result.lens !== lens || result.endedAt < result.startedAt || result.findings.length > body.identity.policy.maxCandidates
      || result.usage.requests > body.identity.policy.requestsPerLens) throw new ReviewError(20, 'Invalid lens identity or bounds');
    if (result.status !== 'complete' && !result.reason) throw new ReviewError(20, 'Missing incomplete reason');
    if (result.status === 'complete' && (result.usage.requests < 1 || result.checkedPaths.length === 0)) throw new ReviewError(20, 'Complete lens requires observed requests and checked paths');
    if (body.execution && body.status === 'complete' && (result.identities?.length !== result.usage.requests || result.contextGaps?.length)) throw new ReviewError(20, 'Missing runtime identity or context');
    if (body.status === 'complete' && (result.status !== 'complete' || result.usage.state === 'uncertain'
      || (result.usage.state === 'unavailable' && result.usage.requests > 0)
      || result.omissions.some(item => item.changed && item.semantic))) throw new ReviewError(20, 'Partial report cannot be complete');
    for (const finding of result.findings) {
      if (finding.lens !== lens || ids.has(finding.id) || !safePath(finding.path) || finding.end < finding.start) throw new ReviewError(20, 'Invalid finding identity');
      if (body.status === 'complete' && finding.classification === 'uncertain') throw new ReviewError(20, 'Uncertain finding cannot be clean');
      ids.add(finding.id);
    }
  }
  if (body.status === 'complete' && body.omissions.some(item => item.changed && item.semantic)) throw new ReviewError(20, 'Omitted semantic source');
  return body;
}
export function sealReport(input: unknown): ReviewReport {
  const body = validateBody(input);
  return { body, receipt: { identityDigest: hash(body.identity), reportDigest: hash(body) } };
}
export function validateReport(input: unknown, expectedIdentity?: ReceiptIdentity): ReviewReport {
  const report = validate(ReviewReportSchema, input);
  validateBody(report.body);
  if (report.receipt.identityDigest !== hash(report.body.identity) || report.receipt.reportDigest !== hash(report.body)) throw new ReviewError(20, 'Tampered receipt');
  if (expectedIdentity && hash(validate(ReceiptIdentitySchema, expectedIdentity)) !== report.receipt.identityDigest) throw new ReviewError(21, 'Stale receipt identity');
  return report;
}
export function reportExit(input: unknown): 0 | 10 | 20 | 30 {
  const { body } = validateReport(input);
  if (body.status === 'setup-error') return EXIT.setup;
  if (body.status !== 'complete') return EXIT.incomplete;
  return Object.values(body.lenses).some(lens => lens.findings.some(actionable)) ? EXIT.candidates : EXIT.complete;
}
export function validateTriage(input: unknown, reportInput: unknown): ParentTriage {
  const report = validateReport(reportInput);
  const triage = validate(ParentTriageSchema, input);
  if (triage.reportId !== report.body.reportId || triage.attemptId !== report.body.attemptId || triage.identityDigest !== report.receipt.identityDigest) throw new ReviewError(21, 'Triage belongs to another report');
  const findings = new Set(Object.values(report.body.lenses).flatMap(lens => lens.findings.map(finding => finding.id)));
  const seen = new Set<string>();
  for (const disposition of triage.dispositions) {
    if (!findings.has(disposition.findingId) || seen.has(disposition.findingId)) throw new ReviewError(20, 'Unknown or duplicate disposition');
    if (disposition.status === 'user-approved-risk' && disposition.approval.attemptId !== triage.attemptId) throw new ReviewError(20, 'Risk approval attempt mismatch');
    seen.add(disposition.findingId);
  }
  if (seen.size !== findings.size) throw new ReviewError(20, 'Missing finding dispositions');
  return triage;
}
export function reusableReport(input: unknown, identity: ReceiptIdentity): boolean {
  try { const report = validateReport(input, identity); return report.body.status === 'complete' && Object.values(report.body.lenses).every(lens => lens.usage.state !== 'uncertain'); }
  catch { return false; }
}

// State contains minimized schema-owned data, never arbitrary source/transcript fields.
export function defaultStateRoot(): string { return join(homedir(), '.local', 'state', 'file-pr-review'); }
export async function privateRoot(root: string): Promise<string> {
  const absolute = resolve(root);
  if (absolute === parse(absolute).root || absolute === resolve(homedir())) throw new ReviewError(30, 'State requires a dedicated private directory');
  // Reject symlink components, including parent components; do not chmod shared parents.
  let current = parse(absolute).root;
  for (const part of absolute.slice(current.length).split('/').filter(Boolean)) {
    current = join(current, part);
    try { await mkdir(current, { mode: 0o700 }); } catch (error) { if (!(error instanceof Error && 'code' in error && error.code === 'EEXIST')) throw error; }
    const info = await lstat(current);
    if (!info.isDirectory() || info.isSymbolicLink()) throw new ReviewError(30, 'Unsafe state directory');
    try { await lstat(join(current, '.git')); throw new ReviewError(30, 'State must be outside Git checkouts'); }
    catch (error) { if (!(error instanceof Error && 'code' in error && error.code === 'ENOENT')) throw error; }
  }
  const info = await lstat(absolute);
  if (typeof process.getuid === 'function' && info.uid !== process.getuid()) throw new ReviewError(30, 'State directory not owned by user');
  await chmod(absolute, 0o700);
  return realpath(absolute);
}
export async function atomicPrivateWrite(root: string, name: string, content: string): Promise<string> {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,100}\.(json|md)$/.test(name)) throw new ReviewError(30, 'Unsafe state name');
  if (Buffer.byteLength(content) > 1_048_576) throw new ReviewError(20, 'Minimized state byte limit exceeded');
  const directory = await privateRoot(root);
  const destination = join(directory, name);
  const temporary = join(directory, `.${randomUUID()}.tmp`);
  const file = await open(temporary, constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL | constants.O_NOFOLLOW, 0o600);
  try {
    await file.writeFile(content, 'utf8');
    await file.sync();
    await file.close();
    await rename(temporary, destination);
    const parent = await open(directory, constants.O_RDONLY);
    try { await parent.sync(); } finally { await parent.close(); }
  } finally { await file.close(); await rm(temporary, { force: true }); }
  return destination;
}
export async function saveReport(root: string, input: unknown): Promise<{ json: string; markdown: string }> {
  const report = validateReport(input);
  const json = await atomicPrivateWrite(root, `${report.body.reportId}.json`, canonicalJson(report));
  const markdown = await atomicPrivateWrite(root, `${report.body.reportId}.md`, `# Local review: ${report.body.status}${report.body.execution?.mode === 'simulated' ? ' (SIMULATED, not real review)' : ''}\n\nReport: ${report.body.reportId}\nHead: ${report.body.identity.snapshot.head}\nIdentity: ${report.receipt.identityDigest}\n\n${Object.values(report.body.lenses).map(lens => [
    `## ${lens.lens}: ${lens.status}`,
    `Usage: ${JSON.stringify(lens.usage)}`,
    `Native calls: ${JSON.stringify(lens.calls ?? [])}; rejected observations: ${JSON.stringify(lens.rejectedCalls ?? [])}`,
    `Observed models: ${JSON.stringify(lens.observedModels ?? lens.identities ?? [])}`,
    `Context gaps: ${JSON.stringify(lens.contextGaps ?? [])}; omissions: ${JSON.stringify(lens.omissions)}`,
    ...(lens.reason ? [`Reason: ${JSON.stringify(lens.reason)}`] : []),
    ...lens.findings.map(finding => `${finding.id} ${finding.severity} ${JSON.stringify(finding.path)}:${finding.start}-${finding.end} (${finding.revision})\nCause: ${JSON.stringify(finding.cause)}\nTrigger: ${JSON.stringify(finding.trigger)}\nImpact: ${JSON.stringify(finding.impact)}\nQuote: ${JSON.stringify(finding.quote)}`),
  ].join('\n\n')).join('\n\n')}\n\nNot push authorization.\n`);
  return { json, markdown };
}
export function validateAttempt(input: unknown): AttemptState {
  const state = validate(AttemptStateSchema, input);
  if (new Set(state.rounds.map(round => round.round)).size !== state.rounds.length || new Set(state.reservations.map(item => item.id)).size !== state.reservations.length) throw new ReviewError(20, 'Duplicate ledger entry');
  if (state.rounds.some((round, index) => round.round !== index + 1 || (round.status === 'settled' && !round.reportId))) throw new ReviewError(20, 'Unsettled or out-of-order round');
  if (state.reservations.some(item => !state.rounds.some(round => round.round === item.round))) throw new ReviewError(20, 'Reservation has no round');
  if (state.reservations.some(item => item.state === 'settled' && item.reservedUsd > 0 && (!item.observation || item.observation.costUsd > item.reservedUsd))) throw new ReviewError(20, 'Missing or excessive authoritative settlement');
  for (const round of state.rounds) for (const lens of ['correctness', 'contracts-risk'] as const) {
    const reservations = state.reservations.filter(item => item.round === round.round && item.lens === lens);
    if (reservations.length > 3 || (round.status === 'settled' && reservations.some(item => item.state !== 'settled'))) throw new ReviewError(20, 'Invalid request settlement/bound');
  }
  if (state.reservations.reduce((total, item) => total + (item.state === 'settled' ? item.observation?.costUsd ?? item.reservedUsd : item.reservedUsd), 0) > 1.02 + Number.EPSILON) throw new ReviewError(20, 'Attempt scheduling cap exceeded');
  return state;
}
export async function saveAttempt(root: string, input: unknown): Promise<string> {
  const state = validateAttempt(input);
  return atomicPrivateWrite(root, `${state.attemptId}.attempt.json`, canonicalJson(state));
}
export async function loadReport(root: string, name: string): Promise<ReviewReport> {
  const directory = await privateRoot(root);
  if (name !== `${name.split('/').at(-1)}` || !/^[a-zA-Z0-9_-]+\.json$/.test(name)) throw new ReviewError(30, 'Unsafe report name');
  const path = resolve(directory, name);
  if (relative(directory, path).startsWith('..') || dirname(path) !== directory) throw new ReviewError(30, 'Unsafe report path');
  const file = await open(path, constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const info = await file.stat();
    if (!info.isFile() || (info.mode & 0o777) !== 0o600 || info.size > 1_048_576) throw new ReviewError(30, 'Unsafe report file');
    return validateReport(parseJson(ReviewReportSchema, await readFile(file, 'utf8')));
  } finally { await file.close(); }
}
