// Offline browser verification of full metadata, model hiding and Safari complement.
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
        const cases = JSON.parse(await fs.readFile(path.join(root, 'tests/data/tibia-private-context-acceptance.json'), 'utf8')).cases;
        cases.push(
            {title: 'Olympic Tibia 7.4', tags: ['Gaming4Fun', 'VenezuelaStreamer'], private_probability_min: .5, private_probability_max: 1},
            {title: 'Hunt Tibia 7.4', tags: [], private_probability_min: .01, private_probability_max: .01},
        );
        await page.evaluate(rows => {
            document.body.replaceChildren();
            window.fixtureSettings = {};
            window.fixtureChanges = [];
            window.fixtureMessages = [];
            window.browser = {storage: {local: {get: async defaults => ({...defaults, ...window.fixtureSettings})},
                onChanged: {addListener: fn => window.fixtureChanges.push(fn)}},
                runtime: {sendMessage: async () => {}, onMessage: {addListener: fn => window.fixtureMessages.push(fn)}}};
            rows.forEach((row, i) => {
                const section = document.createElement('section');
                const article = document.createElement('article');
                article.innerHTML = `<a data-a-target="preview-card-channel-link" href="/fixture${i}"><h4></h4><div><p>fixture${i}</p></div></a>`;
                article.querySelector('h4').textContent = row.title;
                article.querySelector('h4').title = row.title;
                article.__reactFiberFixture = {memoizedProps: {channelLogin: `fixture${i}`, title: row.title,
                    tagListProps: {freeformTags: row.tags.map(name => ({name}))}}};
                section.append(article); document.body.append(section);
            });
        }, cases);
        for (const file of ['extension/src/tibia-evidence.js', 'extension/src/tibia-classify.js', 'extension/src/tibia-rules.js',
            'extension/src/settings.js', 'extension/browsers/safari/web/tibia-probability.js', 'extension/src/tibia-filter.js']) {
            await page.addScriptTag({path: path.join(root, file)});
        }
        await page.addStyleTag({path: path.join(root, 'extension/browsers/safari/web/tibia-probability.css')});
        await page.addStyleTag({content: '[data-twitch-clean-hidden] {display:none} section {width:300px} h4 {overflow:hidden;white-space:nowrap}'});
        await page.waitForFunction(count => document.querySelectorAll('article[data-tibia-private-result]').length === count, cases.length);
        const result = await page.locator('article').evaluateAll(articles => articles.map(a => ({
            ...JSON.parse(a.getAttribute('data-tibia-private-result')), hidden: Boolean(a.closest('[data-twitch-clean-hidden]')),
            displayed: Number(a.querySelector('[data-tibia-official-probability]').getAttribute('data-tibia-official-probability')),
        })));
        cases.forEach((c, i) => {
            assert.ok(result[i].private_probability >= c.private_probability_min && result[i].private_probability <= c.private_probability_max);
            assert.equal(result[i].hidden, result[i].display_probability < .01);
            assert.equal(result[i].displayed, result[i].display_probability);
        });
        for (const width of [1280, 375]) {
            await page.setViewportSize({width, height: 800});
            assert.equal(await page.locator('.tibia-probability-value').nth(1).textContent(), '99.0%');
            assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
        }
        await page.evaluate(() => {
            window.fixtureSettings = {tibiaFilter: false};
            window.fixtureChanges.forEach(fn => fn({tibiaFilter: {newValue: false}}, 'local'));
        });
        await page.waitForFunction(() => !document.querySelector('[data-twitch-clean-hidden]'));
        assert.equal(await page.locator('[data-tibia-official-probability]').count(), cases.length);
        console.log('PASS browser hiding, complement, disabling filter, desktop/mobile layout');
    } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
