// Mocked startup checks; no real Twitch requests or video-ad claims.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

for (const file of [
  'extension/src/page.js',
  'scripts/twitch/twitch-stopthemadness.js',
]) {
  for (const readyState of ['loading', 'complete']) {
    const storage = new Map();
    const callbacks = new Map();
    let requests = 0;
    class OriginalWorker {
      constructor(url) { this.url = url; }
      addEventListener() {}
      postMessage() {}
    }
    const originalFetch = async () => { requests++; throw new Error('Unexpected network request'); };
    const document = {
      readyState,
      get hidden() { return true; },
      get webkitHidden() { return true; },
      addEventListener() {},
      querySelector() { return null; },
      getElementsByTagName() { return []; },
    };
    const sandbox = {
      Worker: OriginalWorker,
      fetch: originalFetch,
      document,
      navigator: { userAgent: 'Safari mock' },
      localStorage: {
        getItem(key) { return storage.get(key) ?? null; },
        setItem(key, value) { storage.set(key, String(value)); },
      },
      addEventListener(name, callback) { callbacks.set(name, callback); },
      setInterval() { return 1; },
      setTimeout() { return 1; },
      clearInterval() {},
      clearTimeout() {},
      URL, Blob,
      console: { log() {}, warn() {}, error() {} },
    };
    sandbox.window = sandbox;
    const context = vm.createContext(sandbox);
    const source = fs.readFileSync(path.join(__dirname, '../..', file), 'utf8');
    vm.runInContext(source, context, { timeout: 3000 });
    assert.equal(sandbox.twitchAdSolutionsVersion, 24);
    assert.equal(storage.get('video-quality'), '{"default":"chunked"}');
    assert.notEqual(sandbox.Worker, OriginalWorker);
    assert.notEqual(sandbox.fetch, originalFetch);
    assert.equal(new sandbox.Worker('https://example.com/unrelated.js').url, 'https://example.com/unrelated.js');
    if (readyState === 'loading') {
      assert.ok(callbacks.has('DOMContentLoaded'));
      callbacks.get('DOMContentLoaded')();
    }
    assert.equal(document.hidden, false);
    assert.equal(document.visibilityState, 'visible');
    const firstWorker = sandbox.Worker;
    const firstFetch = sandbox.fetch;
    vm.runInContext(source, context, { timeout: 3000 });
    assert.equal(sandbox.Worker, firstWorker, 'second injection should not wrap Worker again');
    assert.equal(sandbox.fetch, firstFetch, 'second injection should not wrap fetch again');
    assert.equal(requests, 0);
    console.log(`PASS ${file}: ${readyState} startup, hooks, visibility and duplicate guard`);
  }
}
