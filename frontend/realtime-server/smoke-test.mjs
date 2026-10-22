import { spawn } from 'node:child_process';
import { WebSocket } from 'ws';

const port = 18080;
const relay = spawn(process.execPath, ['realtime-server/server.mjs'], {
  cwd: process.cwd(),
  env: { ...process.env, WS_PORT: String(port) },
  stdio: ['ignore', 'pipe', 'pipe'],
});

function waitForRelay() {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error('Relay did not start in time')), 5_000);
    relay.stdout.on('data', (chunk) => {
      if (chunk.toString().includes('WebSocket relay started')) {
        clearTimeout(timeout);
        resolve();
      }
    });
    relay.stderr.on('data', (chunk) => {
      clearTimeout(timeout);
      reject(new Error(chunk.toString()));
    });
    relay.once('exit', (code) => {
      if (code !== null && code !== 0) reject(new Error(`Relay exited with code ${code}`));
    });
  });
}

function waitForOpen(socket) {
  return new Promise((resolve, reject) => {
    socket.once('open', resolve);
    socket.once('error', reject);
  });
}

try {
  await waitForRelay();

  const sender = new WebSocket(`ws://localhost:${port}`);
  const receiver = new WebSocket(`ws://localhost:${port}`);
  await Promise.all([waitForOpen(sender), waitForOpen(receiver)]);

  const received = new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error('Broadcast was not received')), 5_000);
    receiver.on('message', (rawMessage) => {
      const message = JSON.parse(rawMessage.toString());
      if (message.type === 'application.updated') {
        clearTimeout(timeout);
        resolve(message);
      }
    });
  });

  sender.send(JSON.stringify({
    id: 'smoke-event',
    sentAt: new Date().toISOString(),
    type: 'application.updated',
    payload: { application: { id: 'APP-SMOKE' } },
  }));

  await received;
  sender.close();
  receiver.close();
  console.log('[realtime:test] broadcast passed');
} finally {
  relay.kill('SIGTERM');
}
