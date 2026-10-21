import { execFile } from 'node:child_process';
import { mkdir, mkdtemp, realpath, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';

// Test setup only. Never invoked against a product checkout; no remotes configured.
export async function fixtureGit(repo: string, ...args: string[]): Promise<string> {
  return new Promise((accept, reject) => {
    execFile('/usr/bin/git', ['-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false', '-c', 'protocol.allow=never', ...args], {
      cwd: repo, env: { PATH: '/usr/bin:/bin', HOME: '/dev/null', LC_ALL: 'C', GIT_CONFIG_NOSYSTEM: '1', GIT_CONFIG_GLOBAL: '/dev/null', GIT_AUTHOR_NAME: 'Synthetic', GIT_AUTHOR_EMAIL: 'synthetic@example.invalid', GIT_COMMITTER_NAME: 'Synthetic', GIT_COMMITTER_EMAIL: 'synthetic@example.invalid', GIT_TERMINAL_PROMPT: '0' }, maxBuffer: 8_388_608, timeout: 10_000, killSignal: 'SIGKILL',
    }, (error, stdout) => { if (error) reject(error); else accept(stdout.trimEnd()); });
  });
}
export async function put(repo: string, path: string, text: string | Uint8Array) {
  await mkdir(dirname(join(repo, path)), { recursive: true });
  await writeFile(join(repo, path), text);
}
export async function commit(repo: string, message = 'synthetic change') {
  await fixtureGit(repo, 'add', '--all');
  await fixtureGit(repo, 'commit', '--quiet', '-m', message);
  return fixtureGit(repo, 'rev-parse', 'HEAD');
}
export async function gitFixture(files: Record<string, string> = { 'src/a.ts': 'export const enabled = true;\n', 'src/a.test.ts': 'export const test = "valid behavior";\n' }, objectFormat: 'sha1' | 'sha256' = 'sha1') {
  const repo = await mkdtemp(join(await realpath(tmpdir()), 'file-pr-repo-'));
  await fixtureGit(repo, 'init', '--quiet', '--initial-branch=feature', `--object-format=${objectFormat}`);
  for (const [path, text] of Object.entries(files)) await put(repo, path, text);
  const base = await commit(repo, 'synthetic base');
  await fixtureGit(repo, 'branch', 'base');
  return { repo, base };
}
