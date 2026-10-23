// Metadata transport only. Model behavior/parity belongs to milestone C.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
(async () => {
    const packet = JSON.parse(await fs.readFile(path.join(root, 'research/twitch/rebuild/annotation-proposals.json'), 'utf8'));
    const inputs = packet.annotations.filter(r => r.input).map(r => r.input);
    const browser = await chromium.launch({ executablePath: process.env.CHROME_BETA_BINARY || '/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta', headless: true });
    try {
        const page = await browser.newPage();
        await page.route('https://www.twitch.tv/**', route => route.fulfill({ contentType: 'text/html', body: '<body></body>' }));
        await page.goto('https://www.twitch.tv/directory/category/tibia');
        await page.evaluate(rows => rows.forEach((row, i) => {
            const article = document.createElement('article');
            article.innerHTML = '<h4 title="live">truncated</h4>';
            article.__reactFiberFixture = { memoizedProps: { channelLogin: `fixture${i}`, title: row.title,
                tagListProps: { freeformTags: row.tags.map(name => ({ name })) } } };
            document.body.append(article);
        }), inputs);
        await page.addScriptTag({ path: path.join(root, 'extension/src/tibia-props.js') });
        await page.waitForFunction(() => [...document.querySelectorAll('article')].every(a => a.hasAttribute('data-twitch-clean-meta')));
        const actual = await page.locator('article').evaluateAll(rows => rows.map(a => {
            const { title, tags } = JSON.parse(a.getAttribute('data-twitch-clean-meta'));
            return { title, tags };
        }));
        assert.deepEqual(actual, inputs);
        console.log('PASS full reviewed title/tag metadata transport');
    } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
