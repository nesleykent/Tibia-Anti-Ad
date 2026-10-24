// One live, unlabelled capture with the actual unpacked extension. Never fits.
// Refuses to overwrite an existing capture. Public metadata stays under local/.
const {chromium} = require('playwright');
const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '../..');
const output = path.resolve(process.argv[2] || path.join(root, 'local/verification/tibia-first-c'));
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
    if (!output.startsWith(path.join(root, 'local') + path.sep)) { throw new Error('Capture must stay under ignored local/'); }
    await fs.mkdir(output, {recursive: true});
    const file = path.join(output, 'capture.json');
    const frozen = await fs.readFile(path.join(root, 'research/twitch/model/private-model.json'));
    const capture = {started_at: new Date().toISOString(), url: 'https://www.twitch.tv/directory/category/tibia',
        model_sha256: crypto.createHash('sha256').update(frozen).digest('hex'),
        status: 'capturing', labelled: false, tuned_on_capture: false, rows: []};
    await fs.writeFile(file, JSON.stringify(capture, null, 2), {flag: 'wx'});
    const profile = await fs.mkdtemp(path.join(output, 'profile-'));
    let context;
    try {
        context = await chromium.launchPersistentContext(profile, {
            executablePath: process.env.CHROME_BETA_BINARY || '/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta',
            headless: true, ignoreDefaultArgs: ['--disable-extensions'],
            args: ['--enable-unsafe-extension-debugging'], viewport: {width: 1440, height: 900},
        });
        const cdp = await context.browser().newBrowserCDPSession();
        capture.browser = (await cdp.send('Browser.getVersion')).product;
        const {id} = await cdp.send('Extensions.loadUnpacked', {path: path.join(root, 'dist/tibia-anti-ad-chrome')});
        const worker = context.serviceWorkers().find(w => w.url().includes(id)) || await context.waitForEvent('serviceworker');
        const page = await context.newPage();
        // Exactly one navigation to the live category. Scrolling is one continuous capture.
        await page.goto(capture.url, {waitUntil: 'domcontentloaded', timeout: 45000});
        await sleep(12000);
        const seen = new Map();
        let stagnant = 0;
        for (let step = 0; step < 45; step++) {
            const result = await worker.evaluate(async () => {
                const tabs = await chrome.tabs.query({url: 'https://www.twitch.tv/directory/category/tibia*'});
                if (!tabs.length) { throw new Error('Category tab missing'); }
                return chrome.tabs.sendMessage(tabs[0].id, {type: 'tibia-anti-ad:tibia-diagnostics'});
            });
            if (result.model_sha256 !== capture.model_sha256 || !result.enabled) { throw new Error('Frozen model not running with hiding enabled'); }
            const count = seen.size;
            for (const row of result.rows) {
                // Preserve the first observation; later changes never rewrite this test input.
                if (!seen.has(row.channel)) { seen.set(row.channel, {...row, captured_at: result.captured_at}); }
            }
            capture.rows = [...seen.values()];
            await fs.writeFile(file, JSON.stringify(capture, null, 2));
            stagnant = seen.size === count ? stagnant + 1 : 0;
            const atEnd = await page.evaluate(() => {
                const scroller = document.querySelector('[data-a-target="root-scroller"]');
                if (!scroller) { throw new Error('Root scroller missing'); }
                const atEnd = scroller.scrollHeight - scroller.scrollTop <= scroller.clientHeight + 8;
                scroller.scrollTop += Math.max(600, scroller.clientHeight * 0.85);
                return atEnd;
            });
            if (atEnd && stagnant >= 5) { capture.reached_end = true; break; }
            await sleep(1000);
        }
        capture.status = 'complete';
        capture.finished_at = new Date().toISOString();
        capture.reached_end ??= false;
        capture.summary = {total: capture.rows.length, hidden: capture.rows.filter(r => r.hidden).length,
            shown_over_half: capture.rows.filter(r => !r.hidden && r.private_probability > 0.5).length};
        await fs.writeFile(file, JSON.stringify(capture, null, 2));
        console.log(JSON.stringify({status: capture.status, ...capture.summary, reached_end: capture.reached_end}));
    } catch (error) {
        capture.status = 'failed'; capture.error = String(error.message);
        await fs.writeFile(file, JSON.stringify(capture, null, 2));
        throw error;
    } finally {
        try { await context?.close(); }
        finally { await fs.rm(profile, {recursive: true, force: true}); }
    }
})().catch(error => {console.error(error); process.exit(1);});
