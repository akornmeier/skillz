import { fork, type ExecFileException, type ExecFileOptions } from 'node:child_process';
import { mkdir, mkdtemp, realpath, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterEach, expect, it, vi } from 'vitest';

const control = vi.hoisted(() => ({ slowNext: false, observedTimeout: 0 }));
vi.mock('node:child_process', async importOriginal => {
  const original = await importOriginal<typeof import('node:child_process')>();
  return { ...original, execFile(file: string, args: string[], options: ExecFileOptions, callback: (error: ExecFileException | null, stdout: string | Buffer, stderr: string | Buffer) => void) {
    if (file === '/usr/bin/git' && control.slowNext) {
      control.slowNext = false; control.observedTimeout = options.timeout ?? 0;
      // First capture query is show-toplevel. Simulate slow valid metadata, no child Git process.
      return original.execFile(process.execPath, ['-e', 'setTimeout(() => process.stdout.write(process.cwd()), 600)'], options, callback);
    }
    return original.execFile(file, args, options, callback);
  } };
});

import { DEFAULT_POLICY, ReviewError } from '../src/contracts.js';
import { review } from '../src/review.js';
import { MODEL, PROMPT, type FixtureTransport, type WorkerInput } from '../src/runtime.js';
import { SOURCE_TOOL_SCHEMAS } from '../src/snapshot.js';
import { commit, gitFixture, put } from './git-fixture.js';

const roots: string[] = [];
afterEach(async () => { control.slowNext = false; await Promise.all(roots.splice(0).map(root => rm(root, { recursive: true, force: true }))); });
async function setup() {
  const { repo } = await gitFixture(); roots.push(repo);
  await put(repo, 'src/a.ts', 'export const enabled = false;\n'); await commit(repo);
  const root = await mkdtemp(join(await realpath(tmpdir()), 'file-pr-lifetime-')); roots.push(root);
  return { root, request: { repo, baseRef: 'base', headRef: 'HEAD', goal: 'Check toggle', builderModel: 'openai/gpt-6', attemptId: 'lifetime', policy: { ...DEFAULT_POLICY } } };
}

it('caps initial and in-flight Git capture by remaining whole-round deadline', async () => {
  const { root, request } = await setup(); control.slowNext = true;
  await expect(review({ ...request, policy: { ...request.policy, roundDeadlineMs: 100 } }, root)).rejects.toMatchObject({ code: 20 });
  expect(control.observedTimeout).toBeGreaterThan(0);
  expect(control.observedTimeout).toBeLessThanOrEqual(100);
});

it('aborts and awaits sibling before releasing ownership when uncertainty persistence fails', async () => {
  const { root, request } = await setup(); const pids: number[] = [];
  let release!: () => void; const barrier = new Promise<void>(resolve => { release = resolve; });
  const fixture = (): FixtureTransport => ({ kind: 'fixture', steps: [{ hang: true }], async onEvent(event) {
    if (event.kind !== 'effect') return;
    pids.push(event.pid);
    // Crash only after both effects; immediate cancellation must not deadlock this barrier.
    if (pids.length === 2) { const ledger = join(root, `${request.attemptId}.attempt.json`); await rm(ledger); await mkdir(ledger); process.kill(pids[0]!, 'SIGKILL'); release(); }
    await barrier;
  } });
  try {
    await expect(review(request, root, { correctness: fixture(), 'contracts-risk': fixture() })).rejects.toMatchObject({ code: 20 });
    expect(pids).toHaveLength(2);
    for (const pid of pids) expect(() => process.kill(pid, 0)).toThrow();
    await expect(review(request, root)).rejects.toBeInstanceOf(ReviewError);
  } finally { for (const pid of pids) { try { process.kill(pid, 'SIGKILL'); } catch { /* Already reaped. */ } } }
});

it('terminates abort-ignoring SDK worker on IPC disconnect', async () => {
  const directory = await mkdtemp(join(await realpath(tmpdir()), 'file-pr-sdk-lifetime-')); roots.push(directory);
  const child = fork(new URL('../src/runtime-child.ts', import.meta.url), [], { cwd: directory,
    execArgv: ['--experimental-transform-types', '--disable-warning=ExperimentalWarning'],
    env: { HOME: directory, XDG_CONFIG_HOME: directory, PATH: '/usr/bin:/bin' }, stdio: ['ignore', 'ignore', 'ignore', 'ipc'] });
  let deadlineKilled = false;
  const exited = new Promise<void>(resolve => child.once('exit', () => resolve()));
  const timer = setTimeout(() => { deadlineKilled = true; child.kill('SIGKILL'); }, 4000);
  child.on('message', (packet: unknown) => {
    if (!packet || typeof packet !== 'object' || !('kind' in packet)) return;
    if (packet.kind === 'request' && 'id' in packet) child.send({ id: packet.id, ok: true, data: { hang: true } });
    if (packet.kind === 'effect') child.disconnect();
  });
  try {
    child.send({ kind: 'start', directory, model: MODEL, prompt: PROMPT, payload: '{}', schemas: SOURCE_TOOL_SCHEMAS, maxOutputTokens: 3000 } satisfies WorkerInput);
    await exited;
    expect(deadlineKilled).toBe(false);
    expect(child.exitCode).not.toBeNull();
  } finally { clearTimeout(timer); child.kill('SIGKILL'); await exited; }
});
