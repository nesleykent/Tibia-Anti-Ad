// Offline real-browser checks. Captures and screenshots stay in ignored local/.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
(async () => {
    const browser = await chromium.launch({executablePath: process.env.CHROME_BETA_BINARY || '/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta', headless: true});
    try {
        const page = await browser.newPage({viewport: {width: 1200, height: 700}, acceptDownloads: true});
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        await page.route('https://www.twitch.tv/**', route => route.fulfill({contentType: 'text/html', body: '<body></body>'}));
        await page.goto('https://www.twitch.tv/directory/category/tibia');
        await page.evaluate(() => {
            document.body.innerHTML = '<div data-a-target="root-scroller"><div id="grid"></div></div>';
            window.fixtureSettings = {tibiaMode: 'bottom', tibiaThreshold: 0.5};
            window.fixtureChanges = [];
            window.fixtureMessages = [];
            window.browser = {storage: {local: {get: async defaults => ({...defaults, ...window.fixtureSettings})},
                onChanged: {addListener: fn => window.fixtureChanges.push(fn)}}, runtime: {getManifest: () => ({version: 'test'}),
                sendMessage: async () => {}, onMessage: {addListener: fn => window.fixtureMessages.push(fn)}}};
            window.appendCards = (start, count) => {
                for (let i = start; i < start + count; i++) {
                    const cell = document.createElement('section');
                    const article = document.createElement('article');
                    const info = {channel: `fixture${i}`, title: (i % 2 ? 'Hunt bosses ' : 'RubinOT ') + 'Full title '.repeat(35) + 'END', tags: ['Tag exact', 'Tag exact', 'Português'], viewers: 100 + i};
                    article.setAttribute('data-twitch-clean-meta', JSON.stringify(info));
                    article.innerHTML = `<a data-a-target="preview-card-channel-link" href="/fixture${i}"><h4>truncated</h4><div><p>fixture${i}</p></div></a>`;
                    cell.append(article); document.querySelector('#grid').append(cell);
                }
            };
            window.message = type => new Promise(resolve => window.fixtureMessages.forEach(fn => fn({type}, {}, resolve)));
            window.setting = async values => {
                Object.assign(window.fixtureSettings, values);
                window.fixtureChanges.forEach(fn => fn(Object.fromEntries(Object.entries(values).map(([k, newValue]) => [k, {newValue}])), 'local'));
                await new Promise(resolve => setTimeout(resolve, 50));
            };
            window.appendCards(0, 24);
        });
        await page.addStyleTag({content: 'body{margin:0;font:14px system-ui} [data-a-target="root-scroller"]{height:700px;overflow:auto} #grid{display:flex;flex-wrap:wrap} section{width:25%;height:180px;box-sizing:border-box;padding:12px;border:1px solid #ddd} h4{white-space:nowrap;overflow:hidden} [data-twitch-clean-hidden]{display:none}'});
        for (const file of ['settings.js', 'tibia-evidence.js', 'tibia-classify.js', 'tibia-rules.js', 'tibia-filter.js']) {
            await page.addScriptTag({path: path.join(root, 'extension/src', file)});
        }
        const order = () => page.locator('#grid > section').evaluateAll(cells => [...cells].sort((a,b) => Number(a.style.order)-Number(b.style.order)).map(c => c.querySelector('article').getAttribute('data-twitch-clean-meta')).map(JSON.parse).map(r => r.channel));
        assert.deepEqual(await order(), [...Array.from({length:12},(_,i)=>`fixture${i*2+1}`), ...Array.from({length:12},(_,i)=>`fixture${i*2}`)]);
        const report = await page.evaluate(() => window.message('tibia-anti-ad:tibia-hidden'));
        assert.equal(report.hidden.length, 12);
        assert.equal(await page.locator('[data-twitch-clean-hidden]').count(), 0);
        await page.evaluate(() => { document.querySelector('[data-a-target="root-scroller"]').scrollTop = 450; });
        // Explicit policy changes must regroup the entire loaded list even
        // when the reader has already scrolled through some cards.
        await page.evaluate(() => window.setting({tibiaThreshold:0}));
        assert.deepEqual(await order(), Array.from({length:24},(_,i)=>`fixture${i}`));
        await page.evaluate(() => window.setting({tibiaThreshold:0.5}));
        assert.deepEqual(await order(), [...Array.from({length:12},(_,i)=>`fixture${i*2+1}`), ...Array.from({length:12},(_,i)=>`fixture${i*2}`)]);
        await page.evaluate(() => { document.querySelector('[data-a-target="root-scroller"]').scrollTop = 450; });
        const before = await page.locator('#grid > section').evaluateAll(cells => cells.map(c => ({channel:JSON.parse(c.firstElementChild.getAttribute('data-twitch-clean-meta')).channel, top:c.getBoundingClientRect().top})).filter(c => c.top < 700));
        await page.evaluate(() => window.appendCards(24, 8));
        await page.waitForFunction(() => document.querySelectorAll('article[data-tibia-private-result]').length === 32);
        const after = await page.locator('#grid > section').evaluateAll(cells => Object.fromEntries(cells.map(c => [JSON.parse(c.firstElementChild.getAttribute('data-twitch-clean-meta')).channel, c.getBoundingClientRect().top])));
        before.forEach(c => assert.equal(after[c.channel], c.top, `incremental load moved ${c.channel} above/in viewport`));
        const suffix = (await order()).filter(channel => !before.some(c => c.channel === channel));
        const good = suffix.filter(c => Number(c.replace('fixture','')) % 2);
        const bad = suffix.filter(c => !(Number(c.replace('fixture','')) % 2));
        assert.deepEqual(suffix, [...good, ...bad]);
        await fs.mkdir(path.join(root, 'local/verification'), {recursive: true});
        await page.screenshot({path: path.join(root, 'local/verification/diagnostics-scroll-desktop.png')});
        await page.evaluate(() => window.setting({tibiaMode:'hide'}));
        assert.equal(await page.locator('[data-twitch-clean-hidden]').count(), 16);
        const data = await page.evaluate(() => window.message('tibia-anti-ad:tibia-diagnostics'));
        assert.equal(data.streams.length, 32);
        assert.equal(data.threshold, 0.5);
        assert.equal(data.model_revision, 6);
        assert.equal(data.extension_version, 'test');
        assert.ok(data.model_sha256 && data.captured_at);
        for (const row of data.streams) {
            assert.ok(row.title.endsWith('END') && row.title.length > 300);
            assert.deepEqual(row.tags, ['Tag exact','Tag exact','Português']);
            assert.equal(row.displayed_percentage, row.display_probability * 100);
            row.contributions.forEach(c => assert.equal(c.weight * c.value, c.contribution));
        }
        assert.equal(data.streams.filter(r => r.hidden).length, 16);
        await page.evaluate(() => document.querySelector('#grid > section').remove());
        assert.equal((await page.evaluate(() => window.message('tibia-anti-ad:tibia-diagnostics'))).streams.length, 32);
        const downloadPromise = page.waitForEvent('download');
        const exported = await page.evaluate(() => window.message('tibia-anti-ad:export-diagnostics'));
        assert.equal(exported.ok, true);
        const download = await downloadPromise;
        assert.match(download.suggestedFilename(), /^tibia-diagnostics-.*\.json$/);
        const output = path.join(root, 'local/verification/chrome-diagnostics.json');
        await download.saveAs(output);
        assert.equal(JSON.parse(await fs.readFile(output, 'utf8')).streams.length, 32);
        await page.evaluate(() => window.setting({tibiaMode:'show'}));
        assert.equal(await page.locator('[data-twitch-clean-hidden]').count(), 0);
        assert.equal((await page.evaluate(() => window.message('tibia-anti-ad:tibia-hidden'))).hidden.length, 0);
        assert.equal(await page.locator('section[style*="order"]').count(), 0);
        await page.setViewportSize({width:375,height:667});
        await page.evaluate(() => { document.querySelector('[data-a-target="root-scroller"]').scrollTop = 0; });
        await page.screenshot({path:path.join(root,'local/verification/diagnostics-mobile.png')});
        assert.deepEqual(errors, []);
        console.log('PASS modes, stable grouping on incremental load, session retention, full capture schema, real Chrome file download and responsive rendering');
    } finally { await browser.close(); }
})().catch(error => {console.error(error);process.exit(1)});
