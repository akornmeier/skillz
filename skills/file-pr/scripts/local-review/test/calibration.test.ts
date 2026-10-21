import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { describe, expect, it } from 'vitest';
import { Type } from 'typebox';
import { safePath, validate } from '../src/contracts.js';
import { containsSecret } from '../src/snapshot.js';

const SourceMap = Type.Record(Type.String(), Type.String());
const Corpus = Type.Array(Type.Object({ id: Type.String(), before: SourceMap, after: SourceMap }, { additionalProperties: false }));
const Labels = Type.Array(Type.Object({ id: Type.String(), actionable: Type.Boolean(), severity: Type.Union([Type.String(), Type.Null()]), path: Type.String(), trigger: Type.String(), impact: Type.String(), required: Type.Boolean() }, { additionalProperties: false }));

// Frozen before any model runs; revisions require a new explicitly recorded calibration cohort.
describe('frozen synthetic calibration, not model quality', () => {
  it('preserves exact source/label bytes and eight defects/four clean controls', async () => {
    const sourceBytes = await readFile(new URL('./calibration/cases.json', import.meta.url));
    const goldBytes = await readFile(new URL('./calibration/gold.json', import.meta.url));
    expect(createHash('sha256').update(sourceBytes).digest('hex')).toBe('da451dcf22472bb2c543fa43f49bc23ebc8d9be80237071181ee629f9f21931b');
    expect(createHash('sha256').update(goldBytes).digest('hex')).toBe('aa330352b3f8fc098d1512e1311d318cde482767ed573af307cb7261c7bc55da');
    const cases = validate(Corpus, JSON.parse(sourceBytes.toString()));
    const labels = validate(Labels, JSON.parse(goldBytes.toString()));
    expect(cases).toHaveLength(12); expect(labels).toHaveLength(12);
    expect(new Set(cases.map(item => item.id)).size).toBe(12);
    expect(labels.filter(item => item.actionable)).toHaveLength(8);
    expect(labels.filter(item => !item.actionable)).toHaveLength(4);
    expect(labels.filter(item => item.required).map(item => item.id)).toEqual(['caller-schema-mismatch', 'error-path-regression']);
    for (const item of cases) {
      const label = labels.find(candidate => candidate.id === item.id);
      expect(label).toBeDefined();
      expect(item.before).not.toEqual(item.after);
      expect(Object.keys(item.after)).toContain(label!.path);
      expect(item.before[label!.path]).not.toBe(item.after[label!.path]);
      for (const source of [item.before, item.after]) {
        expect(Buffer.byteLength(JSON.stringify(source))).toBeLessThan(32768);
        for (const [path, text] of Object.entries(source)) { expect(safePath(path)).toBe(true); expect(containsSecret(text)).toBe(false); }
      }
    }
  });
});
