// Optional integration check: installed Chrome Beta + Playwright on NODE_PATH.
// Uses a disposable profile, never the user's browser profile.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const root = path.join(__dirname, '../..');

(async () => {
    const profile = await fs.mkdtemp(path.join(os.tmpdir(), 'tibia-beta-'));
    const captures = path.join(root, 'local/verification/toolbar');
    await fs.mkdir(captures, { recursive: true });
    let context;
    const launch = () => chromium.launchPersistentContext(profile, {
        executablePath: process.env.CHROME_BETA_BINARY || '/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta',
        headless: true, viewport: { width: 440, height: 760 },
        ignoreDefaultArgs: ['--disable-extensions'],
        args: ['--enable-unsafe-extension-debugging'],
    });
    try {
        context = await launch();
        const session = await context.browser().newBrowserCDPSession();
        console.log('Browser:', (await session.send('Browser.getVersion')).product);
        const { id } = await session.send('Extensions.loadUnpacked', { path: path.join(root, 'dist/tibia-anti-ad-chrome') });
        const page = await context.newPage();
        await page.goto(`chrome-extension://${id}/popup.html`);
        await page.locator('body').evaluate(element => element.classList.contains('loading')
            ? new Promise(resolve => new MutationObserver((_, observer) => {
                if (!element.classList.contains('loading')) { observer.disconnect(); resolve(); }
            }).observe(element, { attributes: true })) : undefined);
        const worker = context.serviceWorkers().find(item => item.url().includes(id)) || await context.waitForEvent('serviceworker');
        await worker.evaluate(() => {
            globalThis.toolbarCalls = [];
            const setIcon = chrome.action.setIcon.bind(chrome.action);
            chrome.action.setIcon = async details => {
                await setIcon(details);
                globalThis.toolbarCalls.push(details.path);
            };
        });
        for (const theme of ['light', 'dark']) {
            await page.emulateMedia({ colorScheme: theme });
            for (const enabled of [false, true]) {
                await page.locator('#enabled').setChecked(enabled);
                const title = `Tibia Anti-Ad — Blocking ${enabled ? 'enabled' : 'disabled'}`;
                await page.waitForFunction(async title => (await chrome.action.getTitle({})) === title, title);
                const expected = `icons/chrome-toolbar/${enabled ? 'active' : 'inactive'}-16.png`;
                let icon;
                for (let attempt = 0; attempt < 100; attempt++) {
                    icon = await worker.evaluate(() => globalThis.toolbarCalls.at(-1));
                    if (icon?.['16'] === expected) { break; }
                    await new Promise(resolve => setTimeout(resolve, 10));
                }
                assert.equal(icon?.['16'], expected);
                assert.ok(!JSON.stringify(icon).includes('safari'));
                await page.screenshot({ path: path.join(captures, `chrome-beta-${theme}-${enabled ? 'active' : 'inactive'}.png`) });
                console.log('PASS', theme, enabled ? 'active' : 'inactive', JSON.stringify(icon));
            }
        }
        await page.locator('#enabled').uncheck();
        await page.waitForFunction(async () => (await chrome.action.getTitle({})).endsWith('disabled'));
        await context.close();
        context = await launch();
        const restarted = await context.browser().newBrowserCDPSession();
        const reloaded = await restarted.send('Extensions.loadUnpacked', { path: path.join(root, 'dist/tibia-anti-ad-chrome') });
        assert.equal(reloaded.id, id);
        const restored = await context.newPage();
        await restored.goto(`chrome-extension://${id}/popup.html`);
        await restored.waitForFunction(async () => (await chrome.action.getTitle({})).endsWith('disabled'));
        assert.equal(await restored.locator('#enabled').isChecked(), false);
        console.log('PASS stored disabled state after Chrome Beta restart and unpacked reload');
        await restored.setContent(`<style>body{font:16px system-ui;margin:0}section{padding:24px;display:flex;gap:32px;align-items:center}.dark{background:#202124;color:white}img{width:32px;height:32px}h2{width:120px}</style>
            ${['light', 'dark'].map(theme => `<section class="${theme}"><h2>${theme}</h2>
                <div><img src="icons/chrome-toolbar/inactive-32.png"><p>Disabled</p></div>
                <div><img src="icons/chrome-toolbar/active-32.png"><p>Enabled</p></div></section>`).join('')}`);
        await restored.locator('img').evaluateAll(images => Promise.all(images.map(image => image.decode())));
        await restored.locator('body').screenshot({ path: path.join(captures, 'chrome-beta-icon-preview.png') });
    } finally {
        try { await context?.close(); }
        finally { await fs.rm(profile, { recursive: true, force: true }); }
    }
})().catch(error => { console.error(error); process.exitCode = 1; });
