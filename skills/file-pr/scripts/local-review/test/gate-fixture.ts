// Scripted fixture boundary, NOT skill integration or upload authorization.
// No process/network APIs: every external effect is represented only in this log.
export type FixtureOperation =
  | { kind: 'lookup' | 'fetch' | 'metadata' }
  | { kind: 'review'; head: string; outcome: 'clean' | 'candidates' | 'incomplete' | 'setup-error' }
  | { kind: 'fix'; head: string }
  | { kind: 'dismiss'; evidence: string }
  | { kind: 'verify'; head: string; dirty?: boolean }
  | { kind: 'waiver'; head: string; reason: string; userApproved: boolean }
  | { kind: 'push' | 'pr-write'; head: string };

export function fixtureBoundary() {
  const log: (FixtureOperation & { result: 'recorded' | 'denied' | 'passed' | 'bypassed' })[] = [];
  let rounds = 0;
  let reviewed: { head: string; outcome: string } | undefined;
  let verified: { head: string; status: 'passed' | 'bypassed' } | undefined;
  let waiver: { head: string; reason: string } | undefined;
  return {
    log,
    record(operation: FixtureOperation) {
      let result: 'recorded' | 'denied' | 'passed' | 'bypassed' = 'recorded';
      switch (operation.kind) {
        case 'review':
          verified = undefined;
          reviewed = undefined;
          if (++rounds > 2) result = 'denied';
          else reviewed = { head: operation.head, outcome: operation.outcome };
          break;
        case 'fix':
          reviewed = undefined;
          verified = undefined;
          waiver = undefined;
          break;
        case 'dismiss':
          if (!operation.evidence.trim() || reviewed?.outcome !== 'candidates') result = 'denied';
          else reviewed.outcome = 'clean';
          break;
        case 'waiver':
          verified = undefined;
          if (operation.userApproved && operation.reason.trim()) waiver = operation;
          else result = 'denied';
          break;
        case 'verify':
          verified = undefined;
          if (operation.dirty) result = 'denied';
          else if (reviewed?.head === operation.head && reviewed.outcome === 'clean') {
            verified = { head: operation.head, status: 'passed' };
            result = 'passed';
          } else if (waiver?.head === operation.head) {
            verified = { head: operation.head, status: 'bypassed' };
            result = 'bypassed';
          } else result = 'denied';
          break;
        case 'push':
        case 'pr-write':
          result = verified?.head === operation.head ? verified.status : 'denied';
          break;
      }
      log.push({ ...operation, result });
      return result;
    },
  };
}
