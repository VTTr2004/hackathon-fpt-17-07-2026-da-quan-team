import test from 'node:test';
import assert from 'node:assert/strict';
import { filterNewSessionRecords } from './collect-claude-log.mjs';

test('only keeps sessions that are not already present', () => {
  const records = [
    { sessionId: 'session-a', lines: ['alpha'] },
    { sessionId: 'session-b', lines: ['beta'] },
    { sessionId: 'session-c', lines: ['gamma'] },
  ];

  const result = filterNewSessionRecords(records, ['session-a', 'session-c']);

  assert.deepEqual(result.map((item) => item.sessionId), ['session-b']);
});
