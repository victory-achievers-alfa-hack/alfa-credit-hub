import assert from 'node:assert/strict';
import { test } from 'node:test';
import { getAuthFailure } from '../src/utils/authErrors.ts';

const apiError = (status, message = 'Техническая ошибка', code) => Object.assign(new Error(message), { status, code });

test('failed connection is not reported as an incorrect password', () => {
  const failure = getAuthFailure(apiError(0, 'Failed to fetch', 'NETWORK_ERROR'), 'login');
  assert.equal(failure.kind, 'connection');
  assert.match(failure.message, /Нет подключения к серверу/);
  assert.doesNotMatch(failure.message, /пароль|fetch/);
});

test('a timed-out login has a connection message', () => {
  assert.equal(getAuthFailure(apiError(0, 'timeout', 'REQUEST_TIMEOUT'), 'login').kind, 'connection');
});

for (const status of [500, 502, 503, 504]) {
  test(`HTTP ${status} has a friendly service-unavailable message`, () => {
    const failure = getAuthFailure(apiError(status, 'Internal Server Error'), 'login');
    assert.equal(failure.kind, 'connection');
    assert.match(failure.message, /Сервис временно недоступен/);
    assert.doesNotMatch(failure.message, /Internal Server Error/);
  });
}

test('only a rejected login identifies invalid credentials', () => {
  assert.deepEqual(getAuthFailure(apiError(401), 'login'), {
    kind: 'credentials',
    message: 'Неверная почта или пароль.',
  });
  assert.notEqual(getAuthFailure(apiError(403), 'login').kind, 'credentials');
});

test('initial session restoration can explain an unavailable server on the login page', () => {
  const failure = getAuthFailure(apiError(502), 'session');
  assert.equal(failure.kind, 'connection');
  assert.match(failure.message, /Сервис временно недоступен/);
});

test('a failed offline logout does not claim to have ended the session', () => {
  const failure = getAuthFailure(apiError(0), 'logout');
  assert.equal(failure.kind, 'connection');
  assert.match(failure.message, /Не удалось выйти/);
  assert.match(failure.message, /Нет подключения к серверу/);
  assert.match(failure.message, /Сессия не завершена/);
});

test('server errors during logout explain that the session is still open', () => {
  const failure = getAuthFailure(apiError(503), 'logout');
  assert.equal(failure.kind, 'connection');
  assert.match(failure.message, /Сервис временно недоступен/);
  assert.match(failure.message, /Сессия не завершена/);
});

test('unknown failures have a safe fallback', () => {
  assert.equal(getAuthFailure(null, 'login').kind, 'other');
  assert.match(getAuthFailure(null, 'login').message, /Не удалось войти/);
  assert.match(getAuthFailure(undefined, 'session').message, /Не удалось проверить сессию/);
});
