import { constants } from 'node:fs';
import { open, readFile, realpath } from 'node:fs/promises';
import { dirname, isAbsolute, join, relative, resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { Type } from 'typebox';
import { ReviewError, atomicPrivateWrite, hash, hashBytes, privateRoot, validate } from './contracts.js';
import { gradeCalibration, readCalibrationJson } from './calibration.js';

const text = Type.String({ minLength: 1 });
const profiles = ['fast/economical', 'balanced/default', 'highest-reasoning'] as const;
const harnesses = ['pi', 'claude-code'] as const;
const DefinitionsSchema = Type.Object({ schema: Type.Literal(1), skill: Type.Literal('file-pr'), requiredProfiles: Type.Array(text), cases: Type.Array(Type.Object({ id: text, expectedBehavior: Type.Array(text), forbiddenBehavior: Type.Array(text) }, { additionalProperties: true })) }, { additionalProperties: false });
// Critical qualification fields from the repository's schema-1 run record, not a replacement schema.
const RecordSchema = Type.Object({ schema: Type.Literal(1), skill: Type.Literal('file-pr'), skillRevision: text, caseId: text, profile: Type.Union(profiles.map(value => Type.Literal(value))), provider: text, model: text, thinking: text, piVersion: text, fixtureRevision: text,
  outcome: Type.Literal('pass'), toolConfiguration: Type.Object({ harness: Type.Union(harnesses.map(value => Type.Literal(value))), skillBundleHash: text }, { additionalProperties: true }), loadedFiles: Type.Array(text, { minItems: 1 }),
  assertions: Type.Array(Type.Object({ kind: Type.Union([Type.Literal('expected'), Type.Literal('forbidden')]), text, outcome: Type.Literal('pass'), evidence: Type.Array(text, { minItems: 1 }) }, { additionalProperties: true }), { minItems: 1 }), evidence: Type.Array(text, { minItems: 1 }) }, { additionalProperties: true });

export async function skillBundleHash() {
  const files = await Promise.all(['SKILL.md', 'workflows/local-review.md', 'evals/evals.json'].map(async name => [name, hashBytes(await readFile(new URL(`../../../${name}`, import.meta.url)))]));
  return hash(files);
}
async function evidenceHash(path: string, root: string) {
  const resolved = resolve(path); const relation = relative(root, resolved);
  if (!relation || relation.startsWith('..') || isAbsolute(relation) || await realpath(resolved) !== resolved) throw new ReviewError(30, 'Qualification evidence escapes canonical evidence root');
  const file = await open(resolved, constants.O_RDONLY | constants.O_NOFOLLOW);
  try {
    const info = await file.stat();
    // Bounded primary artifacts, not silently truncated transcripts.
    if (!info.isFile() || info.size <= 0 || info.size > 33554432 || (info.mode & 0o777) !== 0o600 || (process.getuid && info.uid !== process.getuid())) throw new ReviewError(30, 'Invalid private qualification evidence');
    const digest = createHash('sha256'); for await (const chunk of file.createReadStream({ autoClose: false })) digest.update(chunk);
    return digest.digest('hex');
  } finally { await file.close(); }
}

/** Mechanical coverage/identity checks only, not independent grading of assertion truth. */
export async function checkQualificationRecords(recordsManifest: string, currentSkillHash: string) {
  const definitions = validate(DefinitionsSchema, JSON.parse(await readFile(new URL('../../../evals/evals.json', import.meta.url), 'utf8')));
  if (hash(definitions.requiredProfiles) !== hash(profiles)) throw new ReviewError(30, 'Qualification profile contract changed');
  const manifest = validate(Type.Object({ files: Type.Array(text, { minItems: 1, maxItems: 512 }) }, { additionalProperties: false }), await readCalibrationJson(recordsManifest));
  const evidenceRoot = await realpath(dirname(recordsManifest)); const expected = harnesses.length * profiles.length * definitions.cases.length;
  if (manifest.files.length !== expected) throw new ReviewError(20, `Qualification requires ${expected} case/profile/harness records`);
  const seen = new Set<string>(); const artifacts: { path: string; hash: string }[] = [];
  for (const name of manifest.files) {
    if (isAbsolute(name)) throw new ReviewError(30, 'Run record references must be relative');
    const path = resolve(evidenceRoot, name); const recordHash = await evidenceHash(path, evidenceRoot);
    const record = validate(RecordSchema, await readCalibrationJson(path));
    const definition = definitions.cases.find(item => item.id === record.caseId);
    const key = `${record.toolConfiguration.harness}:${record.caseId}:${record.profile}`;
    if (!definition || seen.has(key) || record.toolConfiguration.skillBundleHash !== currentSkillHash || !record.loadedFiles.some(file => file.endsWith('/SKILL.md') || file === 'SKILL.md')) throw new ReviewError(21, 'Duplicate, stale or unrelated qualification record');
    for (const [kind, required] of [['expected', definition.expectedBehavior], ['forbidden', definition.forbiddenBehavior]] as const) {
      for (const assertion of required) if (!record.assertions.some(item => item.kind === kind && item.text === assertion)) throw new ReviewError(20, 'Qualification omits required behavioral assertion');
    }
    const references = new Set([...record.evidence, ...record.assertions.flatMap(item => item.evidence)]);
    for (const reference of references) {
      const target = reference.split('#')[0]!;
      if (!target || isAbsolute(target)) throw new ReviewError(30, 'Evidence references must be local relative paths');
      const artifact = resolve(dirname(path), target);
      artifacts.push({ path: relative(evidenceRoot, artifact), hash: await evidenceHash(artifact, evidenceRoot) });
    }
    seen.add(key); artifacts.push({ path: name, hash: recordHash });
  }
  // Complete unique cross-product is required, not merely enough records with the right count.
  for (const harness of harnesses) for (const profile of profiles) for (const item of definitions.cases) if (!seen.has(`${harness}:${item.id}:${profile}`)) throw new ReviewError(20, 'Qualification matrix incomplete');
  return { definitionsHash: hash(definitions), records: expected, harnesses, profiles, artifacts };
}

/** Both paid calibration and harness evidence are prerequisites; never auto-approve rollout. */
export async function qualifyCalibration(root: string, judgmentsPath: string, recordsManifest: string, currentRuntimeHash: string) {
  const directory = await privateRoot(root); const grade = await gradeCalibration(directory, judgmentsPath);
  const currentSkillHash = await skillBundleHash();
  if (!grade.eligible || grade.runtimeHash !== currentRuntimeHash || grade.skillHash !== currentSkillHash) throw new ReviewError(21, 'Calibration failed or belongs to another implementation');
  const evidence = await checkQualificationRecords(recordsManifest, currentSkillHash);
  const draft = { schema: 1, approved: false, by: null, status: 'awaiting-user-signoff', runtimeHash: currentRuntimeHash, skillHash: currentSkillHash, calibrationHash: hash(grade), ...evidence, qualificationHash: hash({ grade, artifacts: evidence.artifacts }), disclaimer: 'Artifact/coverage validation is not independent human verification of assertion truth. Explicit user rollout acceptance still required.' };
  await atomicPrivateWrite(directory, 'qualification.json', JSON.stringify(draft)); return draft;
}
