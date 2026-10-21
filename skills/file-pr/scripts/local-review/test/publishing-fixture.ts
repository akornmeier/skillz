import { execFile } from 'node:child_process';
import { readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { promisify } from 'node:util';
import { ReviewError, canonicalJson, type ReviewReport } from '../src/contracts.js';
import { verify } from '../src/review.js';

const execute = promisify(execFile);
export type StubEvent = { operation: string; head: string; status: string };

// Executable stand-ins with no Git/GitHub/network import. They cannot publish anything.
export async function publishingFixture(directory: string, head: string) {
  const state = join(directory, 'stub-state.json');
  const log = join(directory, 'stub-log.jsonl');
  const executable = join(directory, 'publish-stub.cjs');
  await writeFile(state, JSON.stringify({ head, status: 'blocked' }));
  await writeFile(log, '');
  await writeFile(executable, `const fs = require('node:fs');
const state = JSON.parse(fs.readFileSync(process.env.STUB_STATE, 'utf8'));
const [operation, head] = process.argv.slice(2);
const status = operation === 'lookup' ? 'read-only' : state.head === head && ['fixture-only', 'bypassed'].includes(state.status) ? state.status : 'denied';
fs.appendFileSync(process.env.STUB_LOG, JSON.stringify({ operation, head, status }) + '\\n');
process.stdout.write(JSON.stringify(operation === 'lookup' ? { head: state.head, exists: true } : { status }));
process.exitCode = status === 'denied' ? 1 : 0;
`);
  return {
    async invoke(operation: 'lookup' | 'push' | 'pr-write', candidate = head) {
      try {
        const { stdout } = await execute(process.execPath, [executable, operation, candidate], {
          env: { STUB_STATE: state, STUB_LOG: log }, timeout: 5000, maxBuffer: 8192,
        });
        return { exit: 0, output: JSON.parse(stdout) as unknown };
      } catch (error) {
        if (error instanceof Error && 'code' in error && error.code === 1) return { exit: 1, output: undefined };
        throw error;
      }
    },
    async authorize(candidate: string, status: 'fixture-only' | 'bypassed', userApproved = false) {
      if (status === 'bypassed' && !userApproved) throw new Error('Fixture waiver needs explicit user approval');
      await writeFile(state, JSON.stringify({ head: candidate, status }));
    },
    async events(): Promise<StubEvent[]> {
      return (await readFile(log, 'utf8')).trim().split('\n').filter(Boolean).map(line => JSON.parse(line) as StubEvent);
    },
  };
}

export function dismissedTriage(report: ReviewReport) {
  return { schemaVersion: 1, reportId: report.body.reportId, attemptId: report.body.attemptId, identityDigest: report.receipt.identityDigest,
    dispositions: Object.values(report.body.lenses).flatMap(lens => lens.findings.map(finding => ({ findingId: finding.id, status: 'dismissed', evidence: [{ kind: 'source', reference: `${report.body.identity.snapshot.head}:${finding.path}:${finding.start}`, observation: 'Approved fixture goal requires this toggle to be disabled' }] }))) };
}

// Exercise every production freshness/triage check, then require its deliberate simulation denial.
// This test-only adapter cannot turn a real CLI verification failure into upload authorization.
export async function checkFixtureReceipt(report: ReviewReport, triage: unknown, current: { repo: string; baseRef: string; headRef: string }) {
  try { await verify(report, triage, current); }
  catch (error) {
    if (error instanceof ReviewError && error.code === 30 && error.message === 'Simulated evidence cannot authorize real review or upload') return;
    throw error;
  }
  throw new Error(`Production verifier unexpectedly accepted simulated evidence: ${canonicalJson(report.receipt)}`);
}
