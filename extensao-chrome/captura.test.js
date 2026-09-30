// Rodar: node --test extensao-chrome/captura.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const C = require('./captura.js');
const fs = require('node:fs');
const path = require('node:path');

const MASTER = 'https://cf-embed.play.hotmart.com/vod/abc/hls/playlist.m3u8?get_qualities=1&hdntl=x';
const VIDEO = 'https://cf-embed.play.hotmart.com/vod/abc/hls/video.m3u8?hdntl=x';
const hdr = (r, o) => [{ name: 'referer', value: r }, { name: 'Origin', value: o }, { name: 'Accept', value: '*/*' }];

test('prioridade: master 2, outro m3u8 1, resto 0', () => {
  assert.equal(C.prioridade(MASTER), 2);
  assert.equal(C.prioridade(VIDEO), 1);
  assert.equal(C.prioridade('https://x.hotmart.com/seg0001.ts'), 0);
  assert.equal(C.prioridade('nao é url'), 0);
});

test('captura do master guarda url e Referer (case-insensitive)', () => {
  const c = C.capturaDe({ tabId: 5, url: MASTER, requestHeaders: hdr('https://cf-embed.play.hotmart.com/embed/?v=1', 'https://cf-embed.play.hotmart.com'), timeStamp: 10 });
  assert.equal(c.media_url, MASTER);
  assert.equal(c.media_referer, 'https://cf-embed.play.hotmart.com/embed/?v=1');
});

test('ignora host fora do Hotmart, aba inválida e host parecido', () => {
  const d = (url, tabId = 1) => ({ tabId, url, requestHeaders: [] });
  assert.equal(C.capturaDe(d('https://evil.com/playlist.m3u8')), null);
  assert.equal(C.capturaDe(d('https://fakehotmart.com/playlist.m3u8')), null);
  assert.equal(C.capturaDe(d('https://hotmart.com.evil.com/playlist.m3u8')), null);
  assert.equal(C.capturaDe(d(MASTER, -1)), null);
});

test('master não é trocado por variante; master novo troca o antigo', () => {
  const m = { media_url: MASTER, media_referer: 'r' };
  const v = { media_url: VIDEO, media_referer: 'r' };
  const m2 = { media_url: MASTER.replace('abc', 'def'), media_referer: 'r' };
  assert.equal(C.escolher(m, v), m);
  assert.equal(C.escolher(v, m), m);
  assert.equal(C.escolher(m, m2), m2);
  assert.equal(C.escolher(null, v), v);
  assert.equal(C.escolher(m, null), m);
});

test('exigeCaptura só no Hotmart', () => {
  assert.equal(C.exigeCaptura('https://hotmart.com/pt-BR/club/x/products/1/content/2'), true);
  assert.equal(C.exigeCaptura('https://www.youtube.com/watch?v=1'), false);
  assert.equal(C.exigeCaptura('https://hub.asimov.academy/x'), false);
});

test('manifest: JSON válido, sem <all_urls> obrigatório, permissões mínimas', () => {
  const m = JSON.parse(fs.readFileSync(path.join(__dirname, 'manifest.json'), 'utf8'));
  assert.equal(m.manifest_version, 3);
  assert.deepEqual(m.host_permissions, ['*://*.hotmart.com/*']);
  assert.ok(!m.host_permissions.includes('<all_urls>'));
  assert.ok(!m.permissions.includes('webRequestBlocking'));
  assert.ok(m.permissions.includes('webRequest'));
  assert.equal(m.background.service_worker, 'background.js');
});
