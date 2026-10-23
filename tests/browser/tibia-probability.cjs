// Probability presentation must remain numeric even if its stylesheet is absent.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const output = path.join(root, 'local/verification/identity-probability');
(async () => {
  await fs.mkdir(output, { recursive: true });
  const browser = await chromium.launch({ executablePath: '/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta', headless: true });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    for (const width of [1440, 375]) {
      await page.setViewportSize({ width, height: 667 });
      await page.setContent(await fs.readFile(path.join(root, 'tests/browser/fixtures/twitch-probability.html'), 'utf8'));
      for (const file of ['extension/src/tibia-evidence.js', 'extension/src/tibia-classify.js', 'extension/browsers/safari/web/tibia-probability.js']) {
        await page.addScriptTag({ path: path.join(root, file) });
      }
      await page.evaluate(() => {
        const classify = TwitchCleanTibiaClassify.create(TWITCH_CLEAN_TIBIA_EVIDENCE);
        document.querySelectorAll('article').forEach(article => {
          const title = article.querySelector('h4').title;
          const tags = [...article.querySelectorAll('.tw-tag')].map(t => t.textContent);
          TibiaAntiAdProbability.render(article, classify(title, tags));
        });
      });
      for (const badge of await page.locator('[data-tibia-official-probability]').all()) {
        assert.match(await badge.textContent(), /^[<>]?\d+(?:\.\d+)?%$/, 'Only the percentage belongs in visible page text');
        assert.match(await badge.getAttribute('aria-label'), /official Tibia/);
      }
      await page.screenshot({ path: path.join(output, `${width}-without-extension-css.png`) });
      await page.addStyleTag({ path: path.join(root, 'extension/browsers/safari/web/tibia-probability.css') });
      await page.addStyleTag({ content: 'body span { white-space: normal; font-size: 20px; color: rebeccapurple }' });
      const layout = await page.locator('[data-tibia-official-probability]').evaluateAll(badges => badges.map(b => {
        const badge = b.getBoundingClientRect();
        const name = b.previousElementSibling.getBoundingClientRect();
        return { sameRow: Math.abs(badge.top - name.top) < 2, overlaps: badge.left < name.right - 1,
          nowrap: getComputedStyle(b).whiteSpace === 'nowrap', clipped: badge.right > innerWidth };
      }));
      assert.ok(layout.every(x => x.sameRow && !x.overlaps && x.nowrap && !x.clipped), JSON.stringify(layout));
      await page.screenshot({ path: path.join(output, `${width}-styled.png`) });
    }
    assert.deepEqual(errors, []);
    console.log('PASS numeric-only probability, accessible labels, absent/conflicting CSS, 1440px and 375px layouts');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
