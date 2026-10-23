// Opt-in live Twitch check with the real unpacked extension in an isolated profile.
// Saves only public-page screenshots and aggregate diagnostics; never tokens/URLs.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const output = path.join(root, 'local/verification/live-twitch');
const directoryOnly = process.argv.includes('--directory-only');
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
  await fs.mkdir(output, { recursive: true });
  const results = [];
  for (const enabled of [false, true]) {
    const profile = await fs.mkdtemp(path.join(output, 'profile-'));
    let context;
    try {
      context = await chromium.launchPersistentContext(profile, {
        executablePath: process.env.CHROME_BETA_BINARY || '/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta',
        headless: true, ignoreDefaultArgs: ['--disable-extensions'],
        args: ['--enable-unsafe-extension-debugging'], viewport: { width: 1440, height: 900 },
      });
      const browserSession = await context.browser().newBrowserCDPSession();
      let worker;
      if (enabled) {
        const { id } = await browserSession.send('Extensions.loadUnpacked', { path: path.join(root, 'dist/tibia-anti-ad-chrome') });
        worker = context.serviceWorkers().find(w => w.url().includes(id)) || await context.waitForEvent('serviceworker');
      }
      const run = { enabled, started: new Date().toISOString(), browser: (await browserSession.send('Browser.getVersion')).product, hosts: {}, blockedByClient: {} };
      const page = await context.newPage();
      page.on('request', request => {
        try { const host = new URL(request.url()).hostname; run.hosts[host] = (run.hosts[host] || 0) + 1; } catch {}
      });
      page.on('requestfailed', request => {
        if (request.failure()?.errorText.includes('BLOCKED_BY_CLIENT')) {
          const host = new URL(request.url()).hostname;
          run.blockedByClient[host] = (run.blockedByClient[host] || 0) + 1;
        }
      });
      await page.goto('https://www.twitch.tv/directory/category/tibia', { waitUntil: 'domcontentloaded', timeout: 45000 });
      await sleep(15000);
      run.directory = await page.evaluate(() => ({
        title: document.title,
        cards: document.querySelectorAll('[data-a-target="preview-card-image-link"]').length,
        hidden: document.querySelectorAll('[data-twitch-clean-hidden]').length,
        visibleAdContainers: [...document.querySelectorAll('[aria-label="Advertisement"]')].filter(e => e.getBoundingClientRect().height > 0).length,
      }));
      await page.screenshot({ path: path.join(output, `directory-${enabled ? 'filtered' : 'baseline'}.png`) });
      if (directoryOnly) {
        if (enabled) {
          const metadata = await page.locator('article').evaluateAll(articles => articles.filter(article =>
            article.querySelector('a[data-a-target="preview-card-channel-link"], a[data-a-target="preview-card-image-link"]')
          ).map(article => ({
            meta: JSON.parse(article.getAttribute('data-twitch-clean-meta') || 'null'),
            title: article.querySelector('h4[title], h3[title]')?.getAttribute('title'),
          })));
          assert.ok(metadata.length > 0, 'No directory cards to verify');
          for (const { meta, title } of metadata) {
            assert.ok(meta?.title, 'Full stream title missing from React metadata');
            assert.equal(meta.title, title, `Title mismatch for ${meta.channel}`);
          }
          run.titles = await worker.evaluate(rows => {
            const classify = TwitchCleanTibiaClassify.create(TWITCH_CLEAN_TIBIA_EVIDENCE);
            return rows.map(({ meta }) => {
              const result = classify(meta.title, []);
              return { channel: meta.channel, title: meta.title, withoutTags: result.verdict, reason: result.reason };
            });
          }, metadata);
          assert.ok(run.titles.some(row => row.withoutTags === 'other'), 'No title-only hiding evidence');
          assert.ok(run.directory.hidden > 0, 'No stream was classified as other');
          const stream = await page.locator('[data-twitch-clean-hidden] article').first().evaluate(article =>
            JSON.parse(article.getAttribute('data-twitch-clean-meta')));
          assert.ok(stream?.channel && stream?.title, 'Missing broadcast metadata');
          const isHidden = ({ channel }) => {
            const article = [...document.querySelectorAll('article[data-twitch-clean-meta]')].find(article =>
              JSON.parse(article.getAttribute('data-twitch-clean-meta')).channel === channel);
            return article ? Boolean(article.closest('[data-twitch-clean-hidden]')) : null;
          };
          await worker.evaluate(stream => chrome.storage.local.set({ tibiaShown: { [stream.channel]: stream.title } }), stream);
          await page.waitForFunction(arg => {
            const article = [...document.querySelectorAll('article[data-twitch-clean-meta]')].find(article =>
              JSON.parse(article.getAttribute('data-twitch-clean-meta')).channel === arg.channel);
            return article && !article.closest('[data-twitch-clean-hidden]');
          }, stream);
          assert.equal(await page.evaluate(isHidden, stream), false);
          await worker.evaluate(() => chrome.storage.local.set({ tibiaShown: {} }));
          await page.waitForFunction(arg => [...document.querySelectorAll('article[data-twitch-clean-meta]')].some(article =>
            JSON.parse(article.getAttribute('data-twitch-clean-meta')).channel === arg.channel && article.closest('[data-twitch-clean-hidden]')), stream);
          assert.equal(await page.evaluate(isHidden, stream), true);
          await worker.evaluate(() => chrome.storage.local.set({ tibiaFilter: false }));
          await page.waitForFunction(() => document.querySelectorAll('[data-twitch-clean-hidden]').length === 0);
          run.reversibility = { channel: stream.channel, show: 'passed', undo: 'passed', disableFilter: 'passed' };
        }
        results.push(run);
        await fs.writeFile(path.join(output, 'directory-results.json'), JSON.stringify(results, null, 2) + '\n');
        console.log(JSON.stringify(run.directory));
        continue;
      }
      // Public live channel observed in the current Tibia directory.
      await page.goto('https://www.twitch.tv/nxxxte', { waitUntil: 'domcontentloaded', timeout: 45000 });
      await sleep(10000);
      run.playback = [];
      for (let sample = 0; sample < 4; sample++) {
        run.playback.push(await page.evaluate(() => {
          const video = document.querySelector('video');
          return {
            sampled: new Date().toISOString(), currentTime: video?.currentTime ?? null,
            readyState: video?.readyState ?? null, paused: video?.paused ?? null,
            dimensions: video ? [video.videoWidth, video.videoHeight] : null,
            errorCode: video?.error?.code ?? null,
            visibleAdLabel: [...document.querySelectorAll('[data-a-target="video-ad-label"], [data-a-target="video-ad-countdown"]')].some(e => e.getBoundingClientRect().height > 0),
            chatPresent: Boolean(document.querySelector('[data-a-target="chat-scroller"]')),
            captionsControl: Boolean(document.querySelector('[data-a-target="player-captions-button"]')),
            playerError: document.querySelector('[data-a-target="player-overlay-content-gate"]')?.textContent?.slice(0, 250) || null,
          };
        }));
        await sleep(10000);
      }
      await page.screenshot({ path: path.join(output, `player-${enabled ? 'filtered' : 'baseline'}.png`) });
      if (worker) run.rulesets = await worker.evaluate(() => chrome.declarativeNetRequest.getEnabledRulesets());
      results.push(run);
      await fs.writeFile(path.join(output, 'results.json'), JSON.stringify(results, null, 2) + '\n');
      console.log(JSON.stringify(run));
    } finally {
      await context?.close();
      await fs.rm(profile, { recursive: true, force: true });
    }
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
