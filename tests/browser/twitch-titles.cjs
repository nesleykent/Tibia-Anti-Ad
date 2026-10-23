// Reproduce title-only filtering in the actual extension, in a disposable browser.
// Fixtures exercise the React metadata bridge and the DOM fallback separately.
const {
  chromium
} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const output = path.join(root, 'local/verification/twitch-titles');
const escape = text => text.replace(/[&<>"']/g, c => ({
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;'
})[c]);
(async () => {
  await fs.mkdir(output, {
    recursive: true
  });
  const cases = JSON.parse(await fs.readFile(path.join(root, 'tests/data/tibia-classify-cases.json'), 'utf8')).cases;
  const stale = JSON.parse(await fs.readFile(path.join(root, 'filters/sources/twitch/tibia-evidence.json'), 'utf8'));
  delete stale.revision;
  stale.games['Other Pok\u00e9mon servers'].words = stale.games['Other Pok\u00e9mon servers'].words.filter(w => w !== 'otponline');
  stale.games['Idle games'].words = stale.games['Idle games'].words.filter(w => !w.startsWith('ibaiak'));
  const profile = await fs.mkdtemp(path.join(output, 'profile-'));
  let context;
  try {
    context = await chromium.launchPersistentContext(profile, {
      executablePath: process.env.CHROME_BETA_BINARY || '/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta',
      headless: true,
      ignoreDefaultArgs: ['--disable-extensions'],
      args: ['--enable-unsafe-extension-debugging'],
      viewport: {
        width: 1440,
        height: 1000
      }
    });
    // Fixtures test the packaged rules. Keep the automatic GitHub updater from
    // replacing them with the published version while the test is running.
    await context.setOffline(true);
    const session = await context.browser().newBrowserCDPSession();
    const {
      id
    } = await session.send('Extensions.loadUnpacked', {
      path: path.join(root, 'dist/tibia-anti-ad-chrome')
    });
    const worker = context.serviceWorkers().find(w => w.url().includes(id)) || (await context.waitForEvent('serviceworker'));
    await worker.evaluate(data => chrome.storage.local.set({
      tibiaEvidence: {
        data,
        fetchedAt: Date.now()
      }
    }), stale);
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const fixture = cases.filter(c => !c.channel);
    const html = `<!doctype html><html><head><meta charset="utf-8"><style>
      body { background:#18181b; color:white; font:16px system-ui; margin:30px }
      main { display:grid; grid-template-columns:repeat(3,1fr); gap:18px }
      section { background:#27272b; padding:15px } h4 { margin:0 0 10px }
      .tw-tag { display:inline-block; background:#444; border-radius:12px; padding:3px 8px }
      </style></head><body><h1>Title and tag regression fixtures</h1><main>${fixture.map((c, i) => `<section id="case-${i}"><article><a data-a-target="preview-card-channel-link" href="/fixture${i}">fixture${i}</a>
      <h4 title="${escape(c.title)}">${escape(c.title)}</h4>${(c.tags || []).map(tag => `<span class="tw-tag">${escape(tag)}</span>`).join('')}</article></section>`).join('')}</main></body></html>`;
    await page.route('https://www.twitch.tv/**', route => route.fulfill({
      contentType: 'text/html',
      body: html
    }));
    const results = [];
    for (const mode of ['dom', 'react']) {
      await page.goto('https://www.twitch.tv/directory/category/tibia');
      if (mode === 'react') {
        await page.evaluate(rows => rows.forEach((c, i) => {
          const article = document.querySelector(`#case-${i} article`);
          article.__reactFiberFixture = {
            memoizedProps: {
              channelLogin: `fixture${i}`,
              title: c.title,
              tagListProps: {
                freeformTags: (c.tags || []).map(name => ({
                  name
                }))
              }
            }
          };
          // The rendered text is truncated; only the bridge has the full title.
          article.querySelector('h4').setAttribute('title', 'live');
        }), fixture);
        await page.waitForFunction(count => document.querySelectorAll('article[data-twitch-clean-meta]').length === count, fixture.length);
      }
      await page.waitForFunction(count => document.querySelectorAll('[data-twitch-clean-tibia]').length === count, fixture.length);
      // The bridge and filter run in different worlds. Publishing the metadata
      // precedes the filter's observer, so wait for its verdicts as well.
      await page.waitForFunction(rows => rows.every((c, i) => document.getElementById(`case-${i}`).getAttribute('data-twitch-clean-tibia')?.startsWith(`${c.expect}:`)), fixture).catch(async error => {
        const mismatches = await page.evaluate(rows => rows.flatMap((c, i) => {
          const cell = document.getElementById(`case-${i}`);
          const verdict = cell.getAttribute('data-twitch-clean-tibia');
          return verdict?.startsWith(`${c.expect}:`) ? [] : [{
            title: c.title,
            expect: c.expect,
            verdict,
            meta: cell.querySelector('article').getAttribute('data-twitch-clean-meta')
          }];
        }), fixture);
        console.error(JSON.stringify({
          mode,
          mismatches
        }));
        throw error;
      });
      const observed = await page.locator('section').evaluateAll(sections => sections.map(s => ({
        hidden: getComputedStyle(s).display === 'none',
        verdict: s.getAttribute('data-twitch-clean-tibia')
      })));
      fixture.forEach((c, i) => {
        assert.equal(observed[i].hidden, c.expect === 'other', `${mode}: ${c.title}: ${observed[i].verdict}`);
        assert.ok(observed[i].verdict.startsWith(`${c.expect}:`), `${mode}: ${c.title}: ${observed[i].verdict}`);
      });
      await page.screenshot({
        path: path.join(output, `${mode}-filtered.png`),
        fullPage: true
      });
      results.push({
        mode,
        passed: observed.length,
        observations: observed
      });
    }
    assert.deepEqual(errors, []);
    await fs.writeFile(path.join(output, 'results.json'), JSON.stringify({
      browser: (await session.send('Browser.getVersion')).product,
      results,
      errors
    }, null, 2) + '\n');
    console.log(`PASS title filtering: ${fixture.length} cases through DOM and React metadata, no page errors`);
  } finally {
    await context?.close();
    await fs.rm(profile, {
      recursive: true,
      force: true
    });
  }
})().catch(error => {
  console.error(error);
  process.exit(1);
});
